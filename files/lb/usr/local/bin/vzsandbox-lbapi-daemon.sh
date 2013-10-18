#!/bin/bash
# This is a quick and dirty wrapper to background vzsandbox-api.py
# TODO: Migrate to something more graceful
/usr/local/bin/vzsandbox-lbapi.py >>/var/log/vzsandbox-lbapi.log 2>&1 &
