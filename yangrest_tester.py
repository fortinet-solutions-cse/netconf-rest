from yangrest.yangrestconverter import YangRestConverter
from lxml import etree


def test_create_urlfilter_object():
    yrc = YangRestConverter()

    netconf_data = """
	      <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id" nc:operation="create">
                 <id>1</id>
                 <comment></comment>
                 <one-arm-ips-urlfilter>disable</one-arm-ips-urlfilter>
                 <ip-addr-block>disable</ip-addr-block>
                 <entries></entries>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter"
    assert content == {'id': '1',
                       'comment': None,
                       'one-arm-ips-urlfilter': 'disable',
                       'ip-addr-block': 'disable',
                       'entries': None}
    assert operation == "create"


def test_create_urlfilter_child_object():
    yrc = YangRestConverter()

    netconf_data = """
	      <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id">
                 <id>1</id>
                 <entries nc:operation="create" mkey="id">
                        <id>48</id>
                        <url>www.test.com</url>
                 </entries>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter/1/entries"
    assert content == {'id': '48', 'url': 'www.test.com'}
    assert operation == "create"


def test_delete_urlfilter_child_object():
    yrc = YangRestConverter()

    netconf_data = """
          <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id">
                 <id>1</id>
                 <entries nc:operation="delete" mkey="id">
                        <id>48</id>
                 </entries>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter/1/entries/48"
    assert content == {'id': '48'}
    assert operation == "delete"


def test_delete_fw_address_object():
    yrc = YangRestConverter()

    netconf_data = """
          <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <firewall>
               <address mkey="id" nc:operation="delete">
                 <id>address1</id>
               </address>
            </firewall>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/firewall/address/address1"
    assert content == {'id': 'address1'}
    assert operation == "delete"

def test_purge_fw_address():
    yrc = YangRestConverter()

    netconf_data = """
          <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <firewall>
               <address nc:operation="delete">
               </address>
            </firewall>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/firewall/address/address1"
    assert content == {'id': 'address1'}
    assert operation == "delete"


def test_get_urlfilter_object():
    yrc = YangRestConverter()

    netconf_data = """
	      <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id">
                 <id>1</id>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter/1"
    assert content == {}
    assert operation == None

def test_get_urlfilter_child_object():
    yrc = YangRestConverter()

    netconf_data = """
	      <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id">
                 <id>1</id>
                 <entries mkey="id">
                    <id>48</id>
                 </entries>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter/1/entries/48"
    assert content == {}
    assert operation == None


def test_edit_urlfilter_object():
    yrc = YangRestConverter()

    netconf_data = """
          <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id" nc:operation="replace">
                 <id>1</id>
                 <comment>New Comment</comment>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter/1"
    assert content == {'id': '1', 'comment': 'New Comment'}
    assert operation == "replace"


def test_edit_urlfilter_child_object():
    yrc = YangRestConverter()

    netconf_data = """
	      <cmdb xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <webfilter>
               <urlfilter mkey="id">
                 <id>1</id>
                 <entries nc:operation="replace" mkey="id">
                        <id>48</id>
                        <url>www.test_modified.com</url>
                 </entries>
               </urlfilter>
            </webfilter>
          </cmdb>"""

    root = etree.fromstring(netconf_data)

    (url, content, operation) = yrc.extract_url_content_operation(root)

    assert url == "cmdb/webfilter/urlfilter/1/entries/48"
    assert content == {'id': '48', 'url': 'www.test_modified.com'}
    assert operation == "replace"



if __name__ == "__main__":
    test_create_urlfilter_object()
    test_create_urlfilter_child_object()
    test_delete_urlfilter_child_object()
    test_delete_fw_address_object()
    test_get_urlfilter_object()
    test_get_urlfilter_child_object()
    test_edit_urlfilter_object()
    test_edit_urlfilter_child_object()

# Current status of features supported
#
# Retrieve Table         ?
# Retrieve Table Schema  X
# Retrieve Table Default X
# Purge Table            X
# Retrieve Object        yes
# Create Object          yes
# Edit Object            yes
# Delete Object          yes
# Clone Object           X
# Move Object            X
# Retrieve Child Object  yes
# Append Child Object    yes
# Edit Child Object      yes
# Delete Child Object    yes
# Purge Child Table      X
# Retrieve complex Table ?
# Edit Complex Table      ?