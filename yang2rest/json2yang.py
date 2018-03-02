import json
import lxml


class Json2Yang():

    def _yang_builder(self, json_structure):

        json_type = type(json_structure)

        result= None

        if json_type == list:
            for elem in json_structure:
                result+= self._yang_builder(elem)
        elif json_type == dict:
            for elem in json_structure:

                result += '<' + elem + '>'
                result += self._yang_builder(json_structure[elem])
                result += '</' + elem + '>'
        elif json_type == str:
            result += json_structure
        else:
            result += str(json_structure)

        return result

    def convert_json(self, string):

        json_structure = json.loads(string)

        yang_result = self._yang_builder(json_structure)

        return yang_result
