import logging

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class YangRestConverter(object):


    def remove_urn(self, text):
        return text[text.find('}') + 1:]

    def contains_operation(self, netconf_data):
        for attrib in netconf_data.attrib:
            if self.remove_urn(attrib) == "operation":
                return True
        return False

    def contains_mkey(self, netconf_data):
        return 'mkey' in netconf_data.attrib

    def extract_table_operation(self, netconf_data):
        for elem in netconf_data.iter():
            for attrib in elem.attrib:
                if self.remove_urn(attrib) == "operation":
                    return elem.attrib[attrib]

        raise Exception("No operation found in netconf data")

    def extract_mkey(self, netconf_data):
        mkey = netconf_data.attrib['mkey']

        for elem in netconf_data:
            if self.remove_urn(elem.tag) == mkey:
                return elem.text

        raise Exception("Error, mkey: '%s' not found in netconf data", format(mkey))

    def extract_table_content(self, netconf_data):
        # Algorithm to extract data will be: Get every content inside the tag
        # that contains 'operation' attribute

        content = {}

        for elem in netconf_data.iter():
            for attrib in elem.attrib:
                if self.remove_urn(attrib) == "operation":
                    for avp in elem:
                        content[self.remove_urn(avp.tag)] = avp.text
        return content

    def extract_path_until_final_resource(self, netconf_data, is_delete_operation=False):
        # Algorithm to calculate the rest of the path consists on going down until
        # a tag with 'operation' attribute is found. That tag will
        # be the last one to be included in the final url
        path = ""
        while not self.contains_operation(netconf_data):
            path += "/" + self.remove_urn(netconf_data.tag)
            if self.contains_mkey(netconf_data):
                path += "/" + self.extract_mkey(netconf_data)
                netconf_data = netconf_data[1]
            else:
                netconf_data = netconf_data[0]

        if self.contains_operation(netconf_data):
            path += "/" + self.remove_urn(netconf_data.tag)
            if is_delete_operation:
                path += "/" + self.remove_urn(self.extract_mkey(netconf_data))
            return path
        else:
            raise Exception("Error, not able to calculate path. Is operation defined?")

    def extract_name_content_operation(self, netconf_data):

        name = self.remove_urn(netconf_data.tag)
        logger.debug("Name: %s", name)

        operation = self.extract_table_operation(netconf_data)
        logger.debug("Operation: %s", operation)

        remaining_path = self.extract_path_until_final_resource(netconf_data,
                                                                is_delete_operation=operation == "delete")
        logger.debug("Remaining path: %s", remaining_path)

        content = self.extract_table_content(netconf_data)
        logger.debug("Content: %s", content)

        return remaining_path, content, operation

    def extract_path_content_operation(self, netconf_data):
        path = self.remove_urn(netconf_data.tag)
        logger.debug("Path: %s", path)

        (name, content, operation) = self.extract_name_content_operation(netconf_data[0])

        return path + name, content, operation

    def extract_url_content_operation(self, netconf_data):
        api_type = self.remove_urn(netconf_data.tag)

        logger.debug("Api Type: %s", api_type)

        if api_type == "cmdb":
            (path, content, operation) = self.extract_path_content_operation(netconf_data[0])

        elif api_type == "monitor":
            raise Exception("Monitor url are not supported yet")
        else:
            raise Exception("Main tag is not cmdb or monitor. Cannot continue.")

        return api_type + "/" + path, content, operation
