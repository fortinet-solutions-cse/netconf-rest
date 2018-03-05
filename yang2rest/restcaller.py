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
# This helps performing REST calls towards Fortigate.
# Maps operations from Netconf to REST and prepares
# the content/url etc to execute the operation
#
#************************************************
"""

__author__ = "Miguel Angel Muñoz González (magonzalez at fortinet.com)"
__copyright__ = "Copyright 2018, Fortinet, Inc."
__credits__ = "Miguel Angel Muñoz"
__license__ = "Apache 2.0"
__version__ = "0.5"
__maintainer__ = "Miguel Ángel Muñoz"
__email__ = "magonzalez at fortinet.com"
__status__ = "Development"


class RestCaller():

    def __init__(self):
        self._fos = None

    @staticmethod
    def _map(operation):
        op_map = {'get': 'get',
                  'create': 'post',
                  'replace': 'put',
                  'merge': 'put',
                  'delete': 'delete'}
        if operation is None:
            operation = 'get'
        return op_map[operation]

    def set_fos(self, fortiosapi):
        self._fos = fortiosapi

    def check_empty_values(self, content):
        # Due to a problem with FGT REST API causing segmentation fault,
        # it is required to modify empty tags in json before sending to FGT
        # e.g. <comment></comment> is by default translated to
        # "comment":None while it should be: "comment:""

        for key in content:
            if not content[key]:
                content[key] = ""
        return content

    def execute_rest_call(self, operation, url, content):
        rest_op = RestCaller._map(operation)

        splitted_url = url.split('/')

        path = '/'.join(splitted_url[1:-1])
        name = splitted_url[-1]

        fos_method = getattr(self._fos, rest_op)

        content = self.check_empty_values(content)

        if rest_op=='get':
            result = fos_method(path, name)
            if 'results' in result:
                http_result_or_status = result['results']
            else:
                http_result_or_status = result['status']
            return result['http_status'], http_result_or_status

        else:
            result = fos_method(path, name, data=content, vdom='root')
            if 'results' in result:
                http_result_or_status = result['results']
            else:
                http_result_or_status = result['status']
            return result['http_status'], http_result_or_status



