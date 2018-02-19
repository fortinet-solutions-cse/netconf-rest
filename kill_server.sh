#!/usr/bin/env bash

ps -ef|grep netconf-rest.py|grep -v grep|awk '{print $2}'|xargs -I[] sudo kill -9 []
