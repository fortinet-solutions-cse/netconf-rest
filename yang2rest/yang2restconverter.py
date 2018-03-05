#!/usr/bin/env python

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
# Author: "Miguel Angel Muñoz González" (magonzalez at fortinet.com)
#
# Parses and extracts relevant data from a Netconf request
# with the intention to transform it to a REST call
#
# Idea is to navigate down the Netconf Yang request and
# build incrementally URL and content data.
#
# For the sake of simplicity it avoids using a Yang schema,
# it simply translates what it finds in the Netconf request.
#
#************************************************
"""

import logging

__author__ = "Miguel Angel Muñoz González (magonzalez at fortinet.com)"
__copyright__ = "Copyright 2018, Fortinet, Inc."
__credits__ = "Miguel Angel Muñoz"
__license__ = "Apache 2.0"
__version__ = "0.6"
__maintainer__ = "Miguel Ángel Muñoz"
__email__ = "magonzalez at fortinet.com"
__status__ = "Development"

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class YangUtil:

    @staticmethod
    def remove_urn(text):
        return text[text.find('}') + 1:]

    @staticmethod
    def contains_operation(netconf_data):
        # Checks if current tag contains an operation

        for attrib in netconf_data.attrib:
            if YangUtil.remove_urn(attrib) == "operation":
                return True
        return False

    @staticmethod
    def contains_mkey(netconf_data):
        # Checks if current tag contains mkey
        return 'mkey' in netconf_data.attrib

    @staticmethod
    def extract_operation(netconf_data):
        for elem in netconf_data.iter():
            for attrib in elem.attrib:
                if YangUtil.remove_urn(attrib) == "operation":
                    return elem.attrib[attrib]

        raise Exception("No operation found in netconf data")

    @staticmethod
    def extract_mkey(netconf_data):
        mkey = netconf_data.attrib['mkey']

        for elem in netconf_data:
            if YangUtil.remove_urn(elem.tag) == mkey:
                return elem.text

        raise Exception("Error, mkey: '{0}' not found in data: {1}", format(mkey), format(netconf_data))

    @staticmethod
    def extract_content_under_operation(netconf_data):
        # Algorithm to extract data will be: Get every content inside the tag
        # that contains 'operation' attribute

        content = {}

        for elem in netconf_data.iter():
            for attrib in elem.attrib:
                if YangUtil.remove_urn(attrib) == "operation":
                    for avp in elem:
                        content[YangUtil.remove_urn(avp.tag)] = avp.text
        return content


class Yang2RestConverter(object):

    def _extract_path_until_final_resource(self, netconf_data, add_deepest_key=False):
        # Algorithm to calculate the rest of the path consists on going down until
        # a tag with 'operation' attribute is found. That tag will
        # be the last one to be included in the final url
        path = ""
        while not YangUtil.contains_operation(netconf_data):
            path += "/" + YangUtil.remove_urn(netconf_data.tag)
            if YangUtil.contains_mkey(netconf_data):
                path += "/" + YangUtil.extract_mkey(netconf_data)
                if len(netconf_data)>1:
                    # In order to continue navigation down in the yang model,
                    # it is assumed that the mkey is in position 0 and the next
                    # tag in position 1
                    netconf_data = netconf_data[1]
                else:
                    break
            else:
                if len(netconf_data)>0:
                    netconf_data = netconf_data[0]
                else:
                    break

        if YangUtil.contains_operation(netconf_data):
            path += "/" + YangUtil.remove_urn(netconf_data.tag)
            return path
        else:
            return path

    def _extract_name_content_operation(self, netconf_data):

        name = YangUtil.remove_urn(netconf_data.tag)
        logger.debug("Name: %s", name)

        operation = None
        try:
            operation = YangUtil.extract_operation(netconf_data)
            logger.debug("Operation: %s", operation)
        except Exception:
            logger.debug("Operation not found, is this a 'get'?")

        is_a_modification = operation == "delete" or operation == "replace" or operation=="merge"

        remaining_path = self._extract_path_until_final_resource(netconf_data,
                                                                 add_deepest_key=is_a_modification)
        logger.debug("Remaining path: %s", remaining_path)

        content = YangUtil.extract_content_under_operation(netconf_data)
        logger.debug("Content: %s", content)

        return remaining_path, content, operation

    def _extract_path_content_operation(self, netconf_data):
        path = YangUtil.remove_urn(netconf_data.tag)
        logger.debug("Path: %s", path)

        (name, content, operation) = self._extract_name_content_operation(netconf_data[0])

        return path + name, content, operation

    def extract_url_content_operation(self, netconf_data):
        api_type = YangUtil.remove_urn(netconf_data.tag)

        logger.debug("Api Type: %s", api_type)

        if api_type == "cmdb" or api_type == "monitor":
            (path, content, operation) = self._extract_path_content_operation(netconf_data[0])
        else:
            raise Exception("Main tag is not cmdb or monitor. Cannot continue.")

        return api_type + "/" + path, content, operation
