#!/bin/bash
# This is a quick and dirty wrapper to background vzsandbox-api.py
# TODO: Migrate to something more graceful
/usr/local/bin/vzsandbox-api.py >>/var/log/vzsandbox-api.log 2>&1 &
