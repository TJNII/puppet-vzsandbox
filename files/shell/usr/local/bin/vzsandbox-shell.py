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
#
# This is the shell script for the sandbox environment, intended to be
# called as a login shell
#
# This script obtains a VM via the API and opens a SSH session to it.
#

import sys
import os
import pexpect
import yaml
import urllib2
import json
import time

def loadConfig(conffile = "/etc/vzsandbox-shell.yaml"):
    try:
        with open(conffile, "r") as fd:
            config = yaml.load(fd.read())
        return config
    except IOError:
        print "Error loading configuration file %s" % conffile
        return False


def mkKeyFile(sourcefile, tmpdir, fileid):
    # Ensure we have a copy of the key only readable by the user
    # (SSH restriction)
    outfile = "%s/%d.%s.id_rsa" % ( tmpdir, os.getuid(), fileid )

    if os.path.exists(outfile):
        # Delete the existing file so we get a new descriptor
        os.remove(outfile)

    # No os.copy()?
    with open(sourcefile, "r") as sfd:
        with open(outfile, "w") as ofd:
            # Eh, keyfiles are small...
            # Probably shouldn't be reused on arbitrary sized files, though...
            ofd.write(sfd.read())

    assert(os.path.isfile(outfile))

    os.chown(outfile, os.getuid(), os.getgid())
#    os.chmod(outfile, 400) <- Fails
    os.system("chmod 400 \"%s\"" % outfile)

    assert(os.stat(outfile).st_mode == 0100400)
    return outfile

def interact(server, keyfile, config):
    child = pexpect.spawn("ssh %s@%s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i %s" % 
                          (config["hypervisor"]["user"], server, keyfile))
    try:
        child.interact()
    except OSError:
        # interact() throws an exception when the shell exits
        # TODO: Determine more graceful method
        pass

class Vzlbapi(object):
    def __init__(self, config, debug = False):
        self.rest = RestBase(debug)
        self.config = config
        
    def poweron(self):
        # Todo remove hardcoding
        return self.rest.get("http://%s:%d/providect" % (self.config['loadbalancer']['host'], 
                                                  self.config['loadbalancer']['port']))
    
    def poweroff(self, hyp, ctid):
        return self.rest.post(("http://%s:%d/ct/%d/power" % (hyp,
                                               self.config['hypervisor']['port'], 
                                               ctid)), {"state": "off"})

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

def main():
    startTime = time.time()

    config = loadConfig()
    if config == False:
        return 1

    if config['general'].has_key("debug"):
        debug = config['general']['debug']
    else:
        debug = False
   
    if not os.path.isdir(config["general"]["tmpdir"]):
        print "ERROR: Temporary directory does not exist"    

    print "INITIALIZATION: Acquiring Container"
    api = Vzlbapi(config, debug)
    container = api.poweron()
    if container is False:
        print "ERROR: Failed to obtain container"
        return 1

    if debug:
        print container
    print "INITIALIZATION: Container built in %s seconds" % container["runtime"]
    print "INITIALIZATION: Your server will be %s, container %d on hypervisor %s" % (
         container["ip"],
         container["ct"],
         container["host"] )

    keyfile = mkKeyFile(config["general"]["keyfile"],
                        config["general"]["tmpdir"],
                        container["ip"])

    if debug:
        print "Key file: %s" % keyfile

    # Hack for https://github.com/TJNII/puppet-vzsandbox/issues/17
    time.sleep(3)

    print "INITIALIZATION COMPLETE: TRANSFERRING LOGON"
    print "Total initialization time: %s seconds" % (time.time() - startTime)
    print ""
    interact(container["ip"], keyfile, config)

    print
    print "Interaction complete"

    print "CLEANUP: Powering down"
    if api.poweroff(container["host"], container["ct"]) is False:
        print "WARNING: POWEROFF FAILED"

    print "Complete."
    return 0

if __name__ == '__main__':
    sys.exit(main())
