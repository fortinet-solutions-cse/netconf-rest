import json

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree



class Json2Yang():

    def _add_list_of_nodes_to_node(self, node, list):
        for elem in list:
            node.append(elem)
        return node

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
                else:
                    node.append(temp)
                result.append(node)

            if result is []:
                return None

        elif json_type is dict:
            result = []
            for elem in json_structure:
                node = etree.Element(elem)
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
