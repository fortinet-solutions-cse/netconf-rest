#!/usr/bin/env python
# coding=utf-8
"""
#************************************************
# Copyright 2018 Fortinet, Inc.
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
#************************************************
# Netconf to Rest translator for FortiGate
#
# +----------+-----------------------------------------+
# | RESTCONF | NETCONF                                 |
# +----------+-----------------------------------------+
# | OPTIONS  | none                                    |
# | HEAD     | none                                    |
# | GET      | < get - config >, < get >               |
# | POST     | < edit - config > (operation="create")  |
# | PUT      | < edit - config > (operation="replace") |
# | PATCH    | < edit - config > (operation="merge")   |
# | DELETE   | < edit - config > (operation="delete")  |
# +----------+-----------------------------------------+

# Use: sudo ./netconf-rest.py
#
# Author: "Miguel Angel Muñoz González" (********* at fortinet.com)
#
#************************************************
"""
from __future__ import absolute_import, division, unicode_literals, print_function, nested_scopes
import logging
import argparse
from time import sleep

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

from netconf import server

from yang2rest.yang2restconverter import Yang2RestConverter
from yang2rest.restcaller import RestCaller
from yang2rest.json2yang import Json2Yang

from fortiosapi import FortiOSAPI

import sys, traceback

__author__ = "Miguel Angel Muñoz González (********** at fortinet.com)"
__copyright__ = "Copyright 2018, Fortinet, Inc."
__credits__ = "Miguel Angel Muñoz"
__license__ = "Apache 2.0"
__version__ = "0.6"
__maintainer__ = "Miguel Ángel Muñoz"
__email__ = "******* at fortinet.com"
__status__ = "Development"

# **********************************
# Global definitions
# **********************************

netconf_server = None  # pylint: disable=C0103

logger = logging.getLogger(__name__)  # pylint: disable=C0103

NC_PORT = 830
NC_USER = ''
NC_PASSWORD = ''

FGT_HOST='192.168.122.40'
FGT_USER=''
FGT_PASSWORD=''

SERVER_DEBUG = False


# **********************************
# General Netconf functions
# **********************************

class NetconfMethods(server.NetconfMethods):
    """ Class containing the methods that will be called upon reception of Netconf external calls"""

    def nc_append_capabilities(self, capabilities_answered):
        capability_list = ["urn:ietf:params:netconf:capability:writable - running:1.0",
                           "urn:ietf:params:netconf:capability:interleave:1.0",
                           "urn:ietf:params:netconf:capability:notification:1.0",
                           "urn:ietf:params:netconf:capability:validate:1.0"]

        for cap in capability_list:
            elem = etree.Element("capability")
            elem.text = cap
            capabilities_answered.append(elem)
        return

    def rpc_get(self, unused_session, rpc, *unused_params):
        logger.info("rpc_get")

        logger.debug("RPC received:%s", format(etree.tostring(rpc, pretty_print=True)))

        # Locate object
        ns = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}

        netconf_data = rpc.find("nc:get/nc:filter/", ns)

        if netconf_data is None:
            raise Exception("Not able to find filter tag")

        y2rc = Yang2RestConverter()

        (url, content, operation) = y2rc.extract_url_content_operation(netconf_data)

        logger.info("URL: %s", format(url))
        logger.info("Content: %s", format(content))
        logger.info("Operation: %s", format(operation))

        fosapi = FortiOSAPI()
        fosapi.https('off')
        fosapi.login(FGT_HOST, FGT_USER, FGT_PASSWORD)

        rc = RestCaller()
        rc.set_fos(fosapi)
        http_result, http_content = rc.execute_rest_call(operation, url, content)

        fosapi.logout()

        if http_result == 200 or 'success':
            if not http_content or http_content is None:
                return etree.Element('ok')
            else:
                j2y = Json2Yang()
                return j2y.convert_json(str(http_content).replace("'", '"'))
        else:
            raise Exception('http-result:' + str(http_result) + ', ' + http_content)

    def rpc_get_config(self, unused_session, rpc, *unused_params):
        logger.info("rpc_get_config")

        logger.debug("RPC received:%s", format(etree.tostring(rpc, pretty_print=True)))

        # Locate object
        ns = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}

        netconf_data = rpc.find("nc:get-config/nc:filter/", ns)

        if netconf_data is None:
            raise Exception("Not able to find filter tag")

        y2rc = Yang2RestConverter()

        (url, content, operation) = y2rc.extract_url_content_operation(netconf_data)

        logger.info("URL: %s", format(url))
        logger.info("Content: %s", format(content))
        logger.info("Operation: %s", format(operation))

        fosapi = FortiOSAPI()
        fosapi.https('off')
        fosapi.login(FGT_HOST, FGT_USER, FGT_PASSWORD)

        rc = RestCaller()
        rc.set_fos(fosapi)
        http_result, http_content = rc.execute_rest_call(operation, url, content)

        fosapi.logout()

        if http_result == 200:
            j2y = Json2Yang()
            return j2y.convert_json(str(http_content).replace("'", '"'))
        else:
            raise Exception('http-result:' + str(http_result) + ', ' + http_content)

    def rpc_edit_config(self, unused_session, rpc, *unused_params):
        logger.info("rpc_edit_config")

        logger.debug("RPC received:%s", format(etree.tostring(rpc, pretty_print=True)))

        # #Locate object
        ns = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}

        netconf_data = rpc.find("nc:edit-config/nc:config/", ns)

        yrc = Yang2RestConverter()

        (url, content, operation) = yrc.extract_url_content_operation(netconf_data)

        logger.info("URL: %s", format(url))
        logger.info("Content: %s", format(content))
        logger.info("Operation: %s", format(operation))

        fosapi = FortiOSAPI()
        fosapi.https('off')
        fosapi.login(FGT_HOST, FGT_USER, FGT_PASSWORD)

        rc = RestCaller()
        rc.set_fos(fosapi)
        http_result, status = rc.execute_rest_call(operation, url, content)

        fosapi.logout()

        if http_result == 200:
            return etree.Element("ok")
        else:
            raise Exception('http-result:' + str(http_result) + ', ' + status)

    def rpc_create_subscription(self, unused_session, rpc, *unused_params):
        return etree.Element("ok")


# **********************************
# Setup Netconf
# **********************************

def setup_netconf():
    "Configure Netconf server listener"

    global netconf_server  # pylint: disable=C0103

    if netconf_server is not None:
        logger.error("Netconf Server is already up and running")
    else:
        server_ctl = server.SSHUserPassController(username=NC_USER,
                                                  password=NC_PASSWORD)
        netconf_server = server.NetconfSSHServer(server_ctl=server_ctl,
                                                 server_methods=NetconfMethods(),
                                                 port=NC_PORT,
                                                 host_key="keys/host_key",
                                                 debug=SERVER_DEBUG)


# **********************************
# Main
# **********************************

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Netconf Server")
    parser.add_argument("-d", "--debug", action="store_true", help="Activate debug logs")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.DEBUG)

    SERVER_DEBUG = logger.getEffectiveLevel() == logging.DEBUG
    logger.info("SERVER_DEBUG:" + str(SERVER_DEBUG))

    setup_netconf()

    # Start the loop for Netconf
    logger.info("Listening Netconf")

    while True:
        sleep(5)
