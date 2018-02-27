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

        return op_map[operation]

    def set_fos(self, fortiosapi):
        self._fos = fortiosapi

    def check_empty_values(self, content):
        # Due to a problem with FGT REST API causing segmentation fault,
        # it is required to modify empty tags before sending to FGT
        # e.g. <comment></comment> is by default translated to
        # "comment":None while it should be: "comment:""

        for key in content:
            if not content[key]:
                content[key] = ""
        return content

    def execute_rest_call(self, operation, url, content):
        rest_op = RestCaller._map(operation)

        splitted_url = url.split('/')

        # path = 'api/v2/'+('/'.join(splitted_url[0:2]))
        path = splitted_url[1]
        name = splitted_url[2]

        fos_method = getattr(self._fos, rest_op)

        content = self.check_empty_values(content)

        result = fos_method(path, name, data=content, vdom='root')

        return result['http_status'], result['status']

