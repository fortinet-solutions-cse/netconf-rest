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

# **********************************
# Global definitions
# **********************************

netconf_server = None # pylint: disable=C0103

logger = logging.getLogger(__name__) # pylint: disable=C0103

NC_PORT = 830
USER = ""
PASSWORD = ""
SERVER_DEBUG = False


# **********************************
# General Netconf functions
# **********************************
def remove_urn(text):
    return text[text.find('}') + 1:]


def extract_table_id(netconf_data):
    mkey = netconf_data.attrib['mkey']

    for elem in netconf_data:
        if remove_urn(elem.tag) == mkey:
            return elem.text

    raise Exception("Error, mkey: '%s' not found in netconf data", format(mkey))

def extract_name_content_operation(netconf_data):

    name = remove_urn(netconf_data.tag)
    logger.info("//////%s", name)

    id = extract_table_id(netconf_data)
    logger.info("........%s", id)

    #operation  = extract_table_operation(netconf_data)
    #content = extract_table_content(netconf_data)

    return (name+"/"+id, content, operation)

def extract_path_content_operation(netconf_data):

    path = remove_urn(netconf_data.tag)
    logger.info("+++++%s", path)

    (name, content, operation) = extract_name_content_operation(netconf_data[0])

    return (path+"/"+name, content, operation)



def extract_url_content_operation(netconf_data):

    api_type = remove_urn(netconf_data.tag)

    logger.info("****%s", api_type)

    if api_type == "cmdb":
        (path, content, operation) = extract_path_content_operation(netconf_data[0])

    elif api_type == "monitor":
        raise Exception("Monitor url are not supported yet")
    else:
        raise Exception("Main tag is not cmdb or monitor. Cannot continue.")

    return (api_type + "/" + path, content, operation)


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

        netconf_data = rpc.find("nc:edit-config/nc:config/",ns)

        (url, content, operation) = extract_url_content_operation(netconf_data)

        logger.info("RESULT: %s", format(url))


        return etree.Element("ok")

    def rpc_create_subscription(self, unused_session, rpc, *unused_params):

        return etree.Element("ok")

# **********************************
# Setup Netconf
# **********************************

def setup_netconf():

    "Configure Netconf server listener"

    global netconf_server # pylint: disable=C0103

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
    parser.add_argument("-d","--debug", action="store_true", help="Activate debug logs")
    args =  parser.parse_args()

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



