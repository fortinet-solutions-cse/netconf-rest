#!/usr/bin/env bash

if [ -z $1 ]; then
  echo "Please enter file to be sent"
  exit -1
fi
cat $1 | sshpass -p . ssh 127.0.0.1 -p 830 -s netconf
#./kill_server.sh
