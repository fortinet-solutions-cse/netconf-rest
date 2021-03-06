# -*- coding: utf-8 eval: (yapf-mode 1) -*-
#
# February 19 2015, Christian Hopps <chopps@gmail.com>
#
# Copyright (c) 2015, Deutsche Telekom AG
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import absolute_import, division, unicode_literals, print_function, nested_scopes
import logging
import io
import threading
import socket

import sshutil.conn
from lxml import etree
from monotonic import monotonic
from netconf import NSMAP
from netconf.base import NetconfSession
from netconf.error import RPCError, SessionError, ReplyTimeoutError

logger = logging.getLogger(__name__)


def _is_filter(select):
    return select.lstrip().startswith("<")


def _get_selection(select):
    if select is None:
        return ""
    elif _is_filter(select) is not None:
        return "<filter>{}</filter>".format(select)
    else:
        return """<filter type="xpath" select="{}"/>""".format(select)


class Timeout(object):
    def __init__(self, timeout):
        self.start_time = monotonic()
        if timeout is None:
            self.end_time = None
        else:
            self.end_time = self.start_time + timeout

    def is_expired(self):
        if self.end_time is None:
            return False
        return self.end_time < monotonic()

    def remaining(self):
        if self.end_time is None:
            return None
        ctime = monotonic()
        if self.end_time < ctime:
            return 0
        else:
            return self.end_time - ctime


class NetconfClientSession(NetconfSession):
    """Netconf Protocol"""

    def __init__(self, stream, debug=False):
        super(NetconfClientSession, self).__init__(stream, debug, None)
        self.message_id = 0
        self.closing = False
        self.rpc_out = {}

        # Condition to handle rpc_out queue
        self.cv = threading.Condition()

        super(NetconfClientSession, self)._open_session(False)

    def __str__(self):
        return "NetconfClientSession(sid:{})".format(self.session_id)

    def close(self):
        if self.debug:
            logger.debug("%s: Closing session.", str(self))

        reply = None
        try:
            # So we need a lock here to check these members.
            send = False
            with self.cv:
                if self.session_id is not None and self.is_active():
                    send = True

            if send:
                self.send_rpc_async("<close-session/>", noreply=True)
                # Don't wait for a reply the session is closed!
        except socket.error:
            if self.debug:
                logger.debug("Got socket error sending close-session request, ignoring")

        super(NetconfClientSession, self).close()

        if self.debug:
            logger.debug("%s: Closed: %s", str(self), str(reply))

    def send_rpc_async(self, rpc, noreply=False):

        # Get the next message id
        with self.cv:
            assert self.session_id is not None
            msg_id = self.message_id
            self.message_id += 1

        if self.debug:
            logger.debug("%s: Sending RPC message-id: %s", str(self), str(msg_id))

        def sendit():
            self.send_message("""<rpc message-id="{}"
                xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">{}</rpc>""".format(msg_id, rpc))

        if noreply:
            sendit()
            return None

        with self.cv:
            sendit()
            # Mark us as expecting a reply
            self.rpc_out[msg_id] = None

        return msg_id

    def send_rpc(self, rpc, timeout=None):
        msg_id = self.send_rpc_async(rpc)
        return self.wait_reply(msg_id, timeout)

    def is_reply_ready(self, msg_id):
        """Check whether reply is ready (or session closed)"""
        with self.cv:
            if not self.is_active():
                raise SessionError("Session closed while checking for reply")
            return self.rpc_out[msg_id] is not None

    def wait_reply(self, msg_id, timeout=None):
        assert msg_id in self.rpc_out

        check_timeout = Timeout(timeout)

        self.cv.acquire()
        # XXX need to make sure the channel doesn't close
        while self.rpc_out[msg_id] is None and self.is_active():
            remaining = check_timeout.remaining()

            self.cv.wait(remaining)
            if self.rpc_out[msg_id] is not None:
                break

            if check_timeout.is_expired():
                raise ReplyTimeoutError(
                    "Timeout ({}s) while waiting for RPC reply to msg-id: {}".format(
                        timeout, msg_id))

        if not self.is_active():
            self.cv.release()
            raise SessionError("Session closed while waiting for reply")

        tree, reply, msg = self.rpc_out[msg_id]
        del self.rpc_out[msg_id]
        self.cv.release()

        error = reply.xpath("nc:rpc-error", namespaces=NSMAP)
        if error:
            raise RPCError(msg, tree, error[0])

        # data = reply.xpath("nc:data", namespaces=self.nsmap)
        # ok = reply.xpath("nc:ok", namespaces=self.nsmap)
        return tree, reply, msg

    def reader_exits(self):
        if self.debug:
            logger.debug("%s: Reader thread exited notifying all.", str(self))
        with self.cv:
            self.cv.notify_all()

    def reader_handle_message(self, msg):
        """Handle a message, lock is already held"""
        try:
            tree = etree.parse(io.BytesIO(msg.encode('utf-8')))
            if not tree:
                raise SessionError(msg, "Invalid XML from server.")
        except etree.XMLSyntaxError:
            raise SessionError(msg, "Invalid XML from server.")

        replies = tree.xpath("/nc:rpc-reply", namespaces=NSMAP)
        if not replies:
            raise SessionError(msg, "No rpc-reply found")

        for reply in replies:
            try:
                msg_id = int(reply.get('message-id'))
            except (TypeError, ValueError):
                # # Cisco is returning errors without message-id attribute which is non-rfc-conforming
                # # it is doing this for any malformed XML not simply missing message-id attribute.
                # error = reply.xpath("nc:rpc-error", namespaces=self.nsmap)
                # if error:
                #     raise RPCError(received, tree, error[0])
                raise SessionError(msg, "No valid message-id attribute found")

            # Queue the message
            with self.cv:
                try:
                    if msg_id not in self.rpc_out:
                        if self.debug:
                            logger.debug("Ignoring unwanted reply for message-id %s", str(msg_id))
                        return
                    elif self.rpc_out[msg_id] is not None:
                        logger.warning("Received multiple replies for message-id %s:"
                                       " before: %s now: %s", str(msg_id), str(
                                           self.rpc_out[msg_id]), str(msg))

                    if self.debug:
                        logger.debug("%s: Received rpc-reply message-id: %s", str(self),
                                     str(msg_id))
                    self.rpc_out[msg_id] = tree, reply, msg
                except Exception as error:
                    logger.debug("%s: Unexpected exception: %s", str(self), str(error))
                    raise
                finally:
                    self.cv.notify_all()

    def get_config_async(self, source, select):
        rpc = "<get-config><source><{}/></source>".format(source)
        rpc += _get_selection(select)
        rpc += "</get-config>"
        return self.send_rpc_async(rpc)

    def get_config(self, source="running", select=None, timeout=None):
        msg_id = self.get_config_async(source, select)
        _, reply, _ = self.wait_reply(msg_id, timeout)
        return reply.find("nc:config", namespaces=NSMAP)

    def get_async(self, select):
        rpc = "<get>" + _get_selection(select) + "</get>"
        return self.send_rpc_async(rpc)

    def get(self, select=None, timeout=None):
        msg_id = self.get_async(select)
        _, reply, _ = self.wait_reply(msg_id, timeout)
        return reply.find("nc:data", namespaces=NSMAP)


class NetconfSSHSession(NetconfClientSession):
    def __init__(self,
                 host,
                 port=830,
                 username=None,
                 password=None,
                 debug=False,
                 cache=None,
                 proxycmd=None):
        if username is None:
            import getpass
            username = getpass.getuser()
        stream = sshutil.conn.SSHClientSession(
            host, port, "netconf", username, password, debug, cache=cache, proxycmd=proxycmd)
        super(NetconfSSHSession, self).__init__(stream, debug)


__author__ = 'Christian Hopps'
__date__ = 'February 19 2015'
__version__ = '1.0'
__docformat__ = "restructuredtext en"
