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
# Author: "Miguel Angel Muñoz González" (magonzalez at fortinet.com)
#
# Converts json string to yang using lxml etree nodes.
#
# This is intended to transform JSON content typically coming
# from a REST answer into a YANG structure using XML nodes (lxml)
#
#************************************************
"""

import json

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree


__author__ = "Miguel Angel Muñoz González (magonzalez at fortinet.com)"
__copyright__ = "Copyright 2018, Fortinet, Inc."
__credits__ = "Miguel Angel Muñoz"
__license__ = "Apache 2.0"
__version__ = "0.6"
__maintainer__ = "Miguel Ángel Muñoz"
__email__ = "magonzalez at fortinet.com"
__status__ = "Development"


class Json2Yang():

    def _add_list_of_nodes_to_node(self, node, list):
        for elem in list:
            node.append(elem)
        return node

    def _check_tag_and_fix(self, string):
        if str.isdigit(string[0]):
            string = 'tag_'+ string
        return string

    def _yang_builder(self, json_structure):

        json_type = type(json_structure)

        result = None

        if json_type is list:
            result = []
            for elem in json_structure:
                node = etree.Element('element')
                temp = self._yang_builder(elem)
                if type(temp) is list:
                    node = self._add_list_of_nodes_to_node(node, temp)
                elif type(temp) is str:
                    node.text = temp
                else:
                    node.append(temp)
                result.append(node)

            if result is []:
                return None

        elif json_type is dict:
            result = []
            for elem in json_structure:
                node = etree.Element(self._check_tag_and_fix(elem))
                temp = self._yang_builder(json_structure[elem])
                if type(temp) is str:
                    node.text = temp
                elif type(temp) is list:
                    node = self._add_list_of_nodes_to_node(node, temp)
                elif temp is not None:
                    node.insert(0, temp)
                elif temp is None:
                    pass
                result.append(node)
            if result is []:
                return None

        elif json_type is str:
            result = json_structure

        else:
            result = str(json_structure)

        return result

    def convert_json(self, string):

        json_structure = json.loads(string)

        yang_result = self._yang_builder(json_structure)

        return yang_result
