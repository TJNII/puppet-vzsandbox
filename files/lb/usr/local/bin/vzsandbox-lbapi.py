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
# Load balancer API script

from flask import Flask,abort,request
from flask.ext import restful
import sys
import urllib2
import json
import yaml

Config = {}

def loadConfig(conffile = "/etc/vzsandbox-lb.yaml"):
    try:
        with open(conffile, "r") as fd:
            config = yaml.load(fd.read())
        return config
    except IOError:
        print "Error loading configuration file %s" % conffile
        return False

class RestBase(object):
  def __init__(self, debug = False):
    self.debug = debug

    # request: Perform RESTful HTTP query
    # PRE: data (if specified) is a dictionary
    # Post: None
    # Return Value: Dataset returned from query
    # Data will be sent as JSON
  def request(self, url, data = None, contentType = "application/json"):
    if self.debug is True:
      handler=urllib2.HTTPSHandler(debuglevel=10)
      opener = urllib2.build_opener(handler)
      urllib2.install_opener(opener)

    req = urllib2.Request(url)
    if data is not None:
      req.add_data(json.dumps(data))
      if contentType:
        req.add_header("Content-Type", contentType)

    try:
      uh = urllib2.urlopen(req)
    except:
      return False

    return json.loads(uh.read())
  
  # get: Convience wrapper around request.  Performs a HTTP GET
  # PRE/POST/Return Value: Same as request()
  def get(self, url):
    return self.request(url)
  
  # post: Convience wrapper around request.  Performs a HTTP POST with data
  # PRE/POST/Return Value: Same as request()
  def post(self, url, data):
    return self.request(url, data = data)

class Builder(restful.Resource):
    def get(self):
        if Config['server'].has_key("debug"):
            debug = Config['server']['debug']
        else:
            debug = False

        rest = RestBase(debug)

        lastNodeID = rrfile_get_next(Config)
        nodeID = (lastNodeID + 1)
        while True:
            if nodeID >= len(Config["hypervisors"]):
                nodeID = 0

            if debug:
                print "INFO: Trying server %s" % Config["hypervisors"][nodeID]

            retVal = rest.get("http://%s:5000/providect" % Config["hypervisors"][nodeID])
            if retVal != False:
                retVal["host"] = Config["hypervisors"][nodeID]
                return retVal

            print "WARNING: Error on node %s" % Config["hypervisors"][nodeID]

            if nodeID == lastNodeID:
                abort(502)
            nodeID += 1
            

        abort(503)

def init_rrfile(config):
    with open(config['server']['rrfile'], "w") as fd:
        fd.write("0")

def rrfile_get_next(config):
    # There's a huge race condition here, hopefully it will be
    # maneagable until we figure out something better
    maxNodeID = len(Config["hypervisors"])
    with open(config['server']['rrfile'], "r") as fd:
        nodeID = int(fd.read())
    
    wNodeID = nodeID + 1
    if wNodeID >= maxNodeID:
        wNodeID = 0
    
    with open(config['server']['rrfile'], "w") as fd:
        fd.write("%s" % wNodeID)

    return nodeID

def main():
    global Config
    Config = loadConfig()
    if Config == False:
        return 1

    init_rrfile(Config)

    app = Flask(__name__)
    api = restful.Api(app)
    
    api.add_resource(Builder, '/providect')

    if Config['server'].has_key("debug"):
        app.run(debug=True)
    else:
        app.run(host=Config['server']['bind-address'], threaded=True)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
