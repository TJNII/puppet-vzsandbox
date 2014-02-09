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
# This is the main API control script for OpenVZ

Config={}

from flask import Flask,abort,request
from flask.ext import restful
import time
import sys
import vzsandboxlib
import socket

class VZCTAPI(restful.Resource):
    def get(self, ctid, action):
        if ctid < 1 or ctid > 254:
            print "ERROR: ctid out of range"
            abort(400)

        vzlib = vzsandboxlib.Vzsandbox(Config)

        if action == "config":
            retVal = vzlib.get_config(ctid)
        elif action == "status":
            retVal = vzlib.get_status(ctid)
        else:
            abort(404)

        if retVal == False:
            abort(400)
        return retVal
        

    def post(self, ctid, action):
        if ctid < 1 or ctid > 254:
            print "ERROR: ctid out of range"
            abort(400)

        vzlib = vzsandboxlib.Vzsandbox(Config, arguments = request.json)

        if not vzlib.verify_ct(ctid):
            print "ERROR: POST to non-existant container"
            abort(400)

        if action == "reset":
            retVal = vzlib.reset_ctfs(ctid)
        elif action == "power":
            retVal = vzlib.set_ct_power(ctid)
        else:
            abort(404)

        if retVal == False:
            abort(400)

        return retVal

    def put(self, ctid, action):
        if ctid < 1 or ctid > 254:
            print "ERROR: ctid out of range"
            abort(400)

        vzlib = vzsandboxlib.Vzsandbox(Config, arguments = request.json)

        if action == "create":
            retVal = vzlib.create_ct(ctid)
        else:
            abort(404)
            
        if retVal == False:
            abort(400)
        return retVal

class Delay(restful.Resource):
    def get(self, secs):
        if secs > 60:
            abort(400)

        time.sleep(secs)

class Status(restful.Resource):
    def get(self, location):
        retVal = None

        if location == "containers":
            vzlib = vzsandboxlib.Vzsandbox(Config, arguments = request.json)
            retVal = vzlib.get_all_status()

        if retVal == None:
            abort(404)
        if retVal == False:
            abort(400)
        return retVal

# This class only has one method: it responds to GET /providect and returns a known free worker
# This method relies on the fact that this API is currently blocking
# So by resetting and powering on in a blocking fashon we prevent potential race conditions
#
# TODO: Log build times to syslog for auditing
class Builder(restful.Resource):
    def get(self):
        retVal = None
        vzlib = vzsandboxlib.Vzsandbox(Config, arguments = request.json)
        starttime = time.time()

        # Get current idle CTs
        # DO NOT USE expiredContainers: They may be in between poweron and login
        # (Race Condition)
        cts = vzlib.get_all_status()["idleContainers"]
        for ctid in cts:
            # These ctids are known created
            # Reset contains running sanity checks
            if vzlib.reset_ctfs(ctid) == False:
                continue

            # Power on VM
            vzlib.poweraction("start", ctid)

            assert(vzlib.get_status(ctid)["running"] == True)

            return { "ct": ctid,
                     "ip": ("%s%s" % (Config["build"]["ipaddr-prefix"], ctid)),
                     "host": Config["server"]["hostname"],
                     "runtime": (time.time() - starttime)
                     }

        # Failed to use existing cts, build a new one
        while True:
            ctid = vzlib.get_unused_ct()
            if ctid == None:
                # Failed
                abort(503)

            # Create contains running sanity checks
            if vzlib.create_ct(ctid) == False:
                continue

            # Power on VM
            vzlib.poweraction("start", ctid)
            
            assert(vzlib.get_status(ctid)["running"] == True)
            
            return { "ct": ctid,
                     "ip": ("%s%s" % (Config["build"]["ipaddr-prefix"], ctid)),
                     "runtime": (time.time() - starttime) }
        
def main():
    global Config
    Config = vzsandboxlib.loadConfig()
    if Config == False:
        return 1
    if not Config["server"].has_key("hostname"):
        Config["server"]["hostname"] = socket.gethostname()
    
    app = Flask(__name__)
    api = restful.Api(app)
    
    api.add_resource(VZCTAPI, '/ct/<int:ctid>/<string:action>')
    api.add_resource(Delay, '/delay/<int:secs>')
    api.add_resource(Status, '/status/<string:location>')
    api.add_resource(Builder, '/providect')

    if Config['server'].has_key("debug"):
        app.run(debug=True)
    else:
        app.run(host=Config['server']['bind-address'])
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
    
