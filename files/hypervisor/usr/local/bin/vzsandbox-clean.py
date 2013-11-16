#!/usr/bin/python -tt
# Copyright 2013 Tom Noonan II (TJNII)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# vzsandbox-clean.py: Clean up unused containers and ensure
# a minimum nuber of containers are staged.
#
# Intended to be run by cron

import sys
import vzsandboxlib
import syslog

def clean_ct(vzlib, ctid):
    # Get status again in case a VM was while we were busy
    status = vzlib.get_status(ctid)

    if status["rebuilding"] == True or status["userActive"] == True:
        return False

    if status["running"] == True:
        vzlib.poweraction("stop", ctid)

    vzlib.reset_ctfs(ctid)
    return True

def clean_cts(vzlib, cts, debug):
    for ctid in cts:
        if debug:
            syslog.syslog("%s: INFO: Cleaning ctid %s" % (sys.argv[0], ctid))
        clean_ct(vzlib, ctid)

def clean(vzlib, debug):
    # Get container status
    cts = vzlib.get_all_status()

    # Iterate over idle containers and reset them
    clean_cts(vzlib, cts["expiredContainers"], debug)
    clean_cts(vzlib, cts["idleContainers"], debug)

def build_spares(vzlib, debug, standby_count):
    # Get container status
    cts = vzlib.get_all_status()

    idle_cts = len(cts["idleContainers"])
    if debug:
        syslog.syslog("%s: INFO: Idle containers: %d" % (sys.argv[0], idle_cts))
    needed_cts = standby_count - idle_cts
    if needed_cts <= 0:
        return True
    
    if debug:
        syslog.syslog("%s: INFO: Needed containers: %d" % (sys.argv[0], needed_cts))

    for x in xrange(0, needed_cts, 1):
        ctid = vzlib.get_unused_ct()
        if debug:
            syslog.syslog("%s: INFO: Building container %d" % (sys.argv[0], ctid))
        vzlib.create_ct(ctid)
    

def main():
    syslog.syslog("%s: NOTICE: Run commencing" % sys.argv[0])
    config = vzsandboxlib.loadConfig()
    if config == False:
        syslog.syslog("%s: ERROR: Configuration load failure" % sys.argv[0])
        return 1

    if config['server'].has_key("debug"):
        debug = config['server']['debug']
    else:
        debug = False
        
    vzlib = vzsandboxlib.Vzsandbox(config)

    clean(vzlib, debug)
    build_spares(vzlib, debug, config['build']['standby-count'])

    syslog.syslog("%s: NOTICE: Run complete" % sys.argv[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())
