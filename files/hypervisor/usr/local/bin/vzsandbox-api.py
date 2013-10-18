#!/usr/bin/python -tt

Config={}

from flask import Flask,abort,request
from flask.ext import restful
import re
import time
import os
import subprocess
import sys
import yaml

class VZCTAPI(restful.Resource):
    def get(self, ctid, action):
        if ctid < 1 or ctid > 254:
            abort(400)

        if action == "config":
            return self.get_config(ctid)

        if action == "status":
            return self.get_status(ctid)

        abort(404)

    def post(self, ctid, action):
        if ctid < 1 or ctid > 254:
            abort(400)
        if not self.verify_ct(ctid):
            abort(400)

        if action == "reset":
            return self.reset_ctfs(ctid)
        if action == "power":
            return self.set_ct_power(ctid)

        abort(404)

    def put(self, ctid, action):
        if ctid < 1 or ctid > 254:
            abort(400)

        if action == "datatest":
            return request.json
        if action == "datatest2":
            return {"source": request.json['source'],
                    "hostname": request.json['hostname'],
                    "ipaddr": request.json['ipaddr']}

        if action == "create":
            return self.create_ct(ctid)

        abort(404)

    # verify_ct: Verify if a container exists / is configured via the conf file
    def verify_ct(self, ctid):
        if os.path.exists("%s/%d.conf" % (Config["vz-dirs"]["conf"], ctid)):
            return True
        else:
            return False

    def import_config(self, conffile):
        conf_re=re.compile('^(\w+)="([^"]+)"')
        retVal={}
        try:
            with open(conffile, "r") as fd:
                for line in fd.read().split('\n'):
                    match = conf_re.findall(line)
                    if match:
                        retVal[match[0][0]] = match[0][1]
            return retVal
        except IOError:
            abort(400)

    def get_config(self, ctid):
        return self.import_config("%s/%d.conf" % (Config["vz-dirs"]["conf"], ctid))


    def get_status(self, ctid):
        # Verify that the container is configured
        retVal = {}
        retVal["configured"] = self.verify_ct(ctid)

        # Get vzctl status
        statusProcess = subprocess.Popen(("vzctl status %d" % ctid), stdout=subprocess.PIPE, shell=True)
        assert(statusProcess.wait() == 0)
        statusList = statusProcess.stdout.read().strip().split(' ')

        retVal["vzExists"] = statusList[2]
        retVal["vzMounted"] = statusList[3]
        retVal["vzRunning"] = statusList[4]
        if statusList[4] == "running":
            retVal["running"] = True

            # VM is running, get user status
            userProcess = subprocess.Popen(("vzctl exec %d users" % ctid), stdout=subprocess.PIPE, shell=True)
            assert(userProcess.wait() == 0)
            if userProcess.stdout.read().strip() == "":
                retVal["userActive"] = False
            else:
                retVal["userActive"] = True

        else:
            retVal["running"] = False

        return retVal

    def create_ct(self, ctid):
        if not request.json.has_key("source") or not request.json.has_key("hostname") or not request.json.has_key("ipaddr"):
            abort(400)

        # Validate input
        if not re.match("^[^ \t\n\r\f\v/]+$", request.json['source']):
            abort(400)
        if not re.match("^[a-zA-Z0-9.-]+$", request.json['hostname']):
            abort(400)
        # Just ensure this is something that /looks/ like an IP address, not a full verification
        if not re.match("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$", request.json['ipaddr']):
            abort(400)
        
        source = "%s/%s" % (Config["vz-dirs"]["templates"], request.json['source'])
        if not os.path.isdir(source) or not os.path.isfile("%s.conf" % source):
            abort(400)
        
        if self.get_status(ctid)["running"]:
            abort(400)

        starttime = time.time()
        # Copy vz private data
        process = subprocess.Popen(("rsync --delete -a %s/ %s/%d" % (source, Config["vz-dirs"]["private"], ctid)),
                                   stdout=subprocess.PIPE, shell=True)
        assert(process.wait() == 0)

        # Ensure root mount point exists
        if not os.path.isdir("%s/%d" % (Config["vz-dirs"]["root"], ctid)):
            process = subprocess.Popen(("mkdir %s/%d" % (Config["vz-dirs"]["root"], ctid)), stdout=subprocess.PIPE, shell=True)
            assert(process.wait() == 0)
            assert(os.path.isdir("%s/%d" % (Config["vz-dirs"]["root"], ctid)))

        # Generate config file
        self.write_config(("%s.conf" % source), request.json['hostname'], request.json['ipaddr'],
                          ("%s/%d.conf" % (Config["vz-dirs"]["conf"], ctid)))

        return {"status": True,
                "runtime": (time.time() - starttime)}

    def write_config(self, sourcefile, hostname, ipaddr, outfile):
        config = self.import_config(sourcefile)
        config["IP_ADDRESS"] = ipaddr
        config["HOSTNAME"] = hostname
        with open(outfile, "w") as fd:
            fd.write("# AUTOMATICALLY GENERATED FILE\n");
            fd.write("# SOURCE TEMPLATE: %s\n" % sourcefile);
            for key in sorted(config.keys()):
                fd.write("%s=\"%s\"\n" % (key, config[key]))

    def reset_ctfs(self, ctid):
        if not request.json.has_key("source"):
            abort(400)

        # Validate input
        if not re.match("^[^ \t\n\r\f\v/]+$", request.json['source']):
            abort(400)
        source = "%s/%s" % (Config["vz-dirs"]["templates"], request.json['source'])
        if not os.path.isdir(source) or not os.path.isfile("%s.conf" % source):
            abort(400)
        
        if self.get_status(ctid)["running"]:
            abort(400)

        starttime = time.time()
        # Copy vz private data
        process = subprocess.Popen(("rsync --delete -a %s/ %s/%d" % (source, Config["vz-dirs"]["private"], ctid)), stdout=subprocess.PIPE, shell=True)
        assert(process.wait() == 0)

        return {"status": True,
                "runtime": (time.time() - starttime)}

    def set_ct_power(self, ctid):
        def _poweraction(command, ctid):
            starttime = time.time()
            process = subprocess.Popen(("vzctl %s %d" % (command, ctid)), stdout=subprocess.PIPE, shell=True)
            assert(process.wait() == 0)
            return (time.time() - starttime)
            
        if not request.json.has_key("state"):
            abort(400)
            
        state = request.json['state'].strip().lower()
        if state == "on":
            if self.get_status(ctid)["running"]:
                abort(400)

            return {"status": True,
                    "runtime": _poweraction("start", ctid)}

        if state == "off":
            status = self.get_status(ctid)
            if not status["running"]:
                abort(400)

            # This is not populated if the server is down.
            if status["userActive"]:
                if request.json.has_key("force"):
                    if request.json['force'] != True:
                        abort(400)
                else:
                    abort(400)

            return {"status": True,
                    "runtime": _poweraction("stop", ctid)}

        abort(400)


class Delay(restful.Resource):
    def get(self, secs):
        if secs > 60:
            abort(400)

        time.sleep(secs)

def loadConfig(conffile):
    try:
        with open(conffile, "r") as fd:
            global Config
            Config = yaml.load(fd.read())
        return 0
    except IOError:
        print "Error loading configuration file %s" % conffile
        return 1

def main():
    if loadConfig("/etc/vzsandbox-api.yaml") != 0:
        return 1
    

    app = Flask(__name__)
    api = restful.Api(app)
    
    api.add_resource(VZCTAPI, '/ct/<int:ctid>/<string:action>')
    api.add_resource(Delay, '/delay/<int:secs>')

    app.run(host=Config['server']['bind-address'])
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
    
