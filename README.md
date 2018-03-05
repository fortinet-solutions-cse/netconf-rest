# netconf-rest
#### A bridge to transform netconf calls into REST API for Fortigate

It will listen to netconf request (port 830) and transform them into REST API calls. Only valid for Fortigate for now.<br>
It does not validate internally against any schema. If the request is malformed, i.e. not according to a format FortiGate can understand, it will fail.

To write a new netconf request please to make use of FGT REST API schema.
Check: https://fndn.fortinet.net/index.php?/documents/file/84-fortios-56-rest-api-reference/

At the moment **only cmdb commands are supported**, monitor commands will be added on a later version.

Please check examples in **./tests/integration_test**
To run examples start the application and run some tests:

```
sudo ./netconf-rest.py
cd ./integration_test
./run_test.sh edit-config-create-child-object.sample
```

*Please note that fortigate access parameters are hardcoded in the application.
Feel free to edit ./netconf-rest.py and modify them according to your needs:*
```
FGT_HOST='192.168.122.40'
FGT_USER='admin'
FGT_PASSWORD=''
```
<br>

###### Reference
Operation mapping between Netconf and REST protocols.
```
 +----------+-----------------------------------------+
 | RESTCONF | NETCONF                                 |
 +----------+-----------------------------------------+
 | OPTIONS  | none                                    |
 | HEAD     | none                                    |
 | GET      | < get - config >, < get >               |
 | POST     | < edit - config > (operation="create")  |
 | PUT      | < edit - config > (operation="replace") |
 | PATCH    | < edit - config > (operation="merge")   |
 | DELETE   | < edit - config > (operation="delete")  |
 +----------+-----------------------------------------+
 ```

Operations supported currently

```
 Retrieve Table         yes
 Retrieve Table Schema  X
 Retrieve Table Default X
 Purge Table            X
 Retrieve Object        yes
 Create Object          yes
 Edit Object            yes
 Delete Object          yes
 Clone Object           X
 Move Object            X
 Retrieve Child Object  yes
 Append Child Object    yes
 Edit Child Object      yes
 Delete Child Object    yes
 Purge Child Table      X
 Retrieve complex Table X
 Edit Complex Table     X

 X Not supported
 ```

 Note: For 'Monitor' (not CMDB) requests, POST operations and parameters are not supported.