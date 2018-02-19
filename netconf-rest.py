#!/usr/bin/sudo python

"""
#************************************************
# Netconf to Rest translator
#
# Use: ./netconf-rest.py
#
# Miguel Angel Munoz Gonzalez
# **********(at)fortinet.com
#
#************************************************

"""

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

from __future__ import absolute_import, division, unicode_literals, print_function, nested_scopes
import logging
import argparse
from time import sleep

# **********************************
# Netconf imports
# **********************************

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

from netconf import server

from yangrest.yangrestconverter import YangRestConverter

# **********************************
# Global definitions
# **********************************

netconf_server = None  # pylint: disable=C0103

logger = logging.getLogger(__name__)  # pylint: disable=C0103

NC_PORT = 830
USER = ""
PASSWORD = ""
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
        logger.info("rpc_get %s %s %s", unused_session, rpc, unused_params)
        return etree.Element("ok")

    def rpc_get_config(self, unused_session, rpc, *unused_params):
        data = etree.Element("data")
        return data

    def rpc_edit_config(self, unused_session, rpc, *unused_params):
        logger.info("rpc_edit_config")

        logger.debug("RPC received:%s", format(etree.tostring(rpc, pretty_print=True)))

        # #Locate object
        ns = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}

        netconf_data = rpc.find("nc:edit-config/nc:config/", ns)

        yrc = YangRestConverter()

        (url, content, operation) = yrc.extract_url_content_operation(netconf_data)

        logger.info("URL: %s", format(url))
        logger.info("Content: %s", format(content))
        logger.info("Operation: %s", format(operation))

        return etree.Element("ok")

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
        server_ctl = server.SSHUserPassController(username=USER,
                                                  password=PASSWORD)
        netconf_server = server.NetconfSSHServer(server_ctl=server_ctl,
                                                 server_methods=NetconfMethods(),
                                                 port=NC_PORT,
                                                 host_key="keys/host_key",
                                                 debug=SERVER_DEBUG)


# **********************************
# Main
# **********************************

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Netconf Server with SNMP trap listening capabilities")
    parser.add_argument("-d", "--debug", action="store_true", help="Activate debug logs")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.DEBUG)

    SERVER_DEBUG = logger.getEffectiveLevel() == logging.DEBUG
    logger.info("SERVER_DEBUG:" + str(SERVER_DEBUG))

    setup_netconf()

    # Start the loop for SNMP / Netconf
    logger.info("Listening Netconf - Snmp")

    while True:
        sleep(5)
