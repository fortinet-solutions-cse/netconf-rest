# netconf-rest
A bridge to transform netconf calls into REST API for Fortigate

It will read netconf request and transform them into REST API calls. Only valid for Fortigate
It does not need schema for now.
If the request is malformed, i.e. not according to a format FortiGate can understand, it will fail.
Writers of Netconf calls need to make use of FGT REST API schema.
Check: https://fndn.fortinet.net/index.php?/documents/file/84-fortios-56-rest-api-reference/

