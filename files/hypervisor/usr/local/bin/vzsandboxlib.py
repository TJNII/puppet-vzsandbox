#!/bin/false
# Include library for use by the API and times jobs

import re
import time
import os
import subprocess
import yaml

def loadConfig(conffile = "/etc/vzsandbox.yaml"):
    try:
        with open(conffile, "r") as fd:
            config = yaml.load(fd.read())
        return config
    except IOError:
        print "Error loading configuration file %s" % conffile
        return False


class Vzsandbox(object):
    def __init__(self, config, arguments = None):
        self.config = config
        self.arguments = arguments
        self.ctid_limit = { "min": 1,
                            "max": 253 }

    # verify_ct: Verify if a container exists / is configured via the conf file
    def verify_ct(self, ctid):
        if os.path.exists("%s/%d.conf" % (self.config["vz-dirs"]["conf"], ctid)):
            return True
        else:
            return False

    def import_ct_config(self, conffile):
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
            return False

    def get_ct_config(self, ctid):
        return self.import_ct_config("%s/%d.conf" % (self.config["vz-dirs"]["conf"], ctid))


    def get_status(self, ctid):
        # Verify that the container is configured
        retVal = {}
        retVal["configured"] = self.verify_ct(ctid)
        retVal["rebuilding"] = self.check_rebuilding_flag(ctid)

        # Get vzctl status
        statusProcess = subprocess.Popen(("vzctl status %d" % ctid), stdout=subprocess.PIPE, shell=True)
        assert(statusProcess.wait() == 0)
        statusList = statusProcess.stdout.read().strip().split(' ')

        # vz.* entries are primarily for debug info
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
            retVal["userActive"] = False
            retVal["running"] = False

        return retVal

    # Return an array of all configured containers
    # Use configuration files as, AFAICT openVZ vzctl can't do this
    def get_all_cts(self):
        conf_re = re.compile("^([0-9]+)\.conf$")
        retVal=[]
        for file in os.listdir(self.config["vz-dirs"]["conf"]):
            match = conf_re.findall(file)
            if match:
                matchi = int(match[0])
                if int(matchi) != 0:
                    retVal.append(matchi)
                    
        return sorted(retVal)

    # get_unused_ctid: Return an unused/unconfigured ct
    def get_unused_ct(self):
        cts = self.get_all_cts()
        for x in xrange(self.ctid_limit["min"], (self.ctid_limit["max"] + 1), 1):
            if x >= len(cts):
                if not self.check_rebuilding_flag(x):
                    return x
            else:
                if x < cts[(x - 1)] and not self.check_rebuilding_flag(x):
                    return x

        return None

    def get_all_status(self):
        cts = self.get_all_cts()
        retVal = { "containers": cts,
                   "idleContainers": [],
                   "inUseContainers": [],
                   "busyContainers": [],
                   "expiredContainers": []
                   }

        for ctid in cts:
            status = self.get_status(ctid)
            
            # ["configured"] will be true, as we know the conf exists
            if status["rebuilding"] == True:
                retVal["busyContainers"].append(ctid)
            elif status["userActive"] == True:
                retVal["inUseContainers"].append(ctid)
            elif status["running"] == True:
                retVal["expiredContainers"].append(ctid)
            else:
                retVal["idleContainers"].append(ctid)

        return retVal


    def create_ct(self, ctid):
        source = "%s/%s" % (self.config["build"]["templates"], self.config["build"]["source"])
        if not os.path.isdir(source) or not os.path.isfile("%s.conf" % source):
            print "ERROR: Bad Source \"%s\"" % source
            return False
        
        status = self.get_status(ctid)
        if status["running"] or status["rebuilding"]:
            print "ERROR: container is up"
            return False

        starttime = time.time()
        # Copy vz private data
        self.reset_ctfs_core(ctid, source)

        # Ensure root mount point exists
        if not os.path.isdir("%s/%d" % (self.config["vz-dirs"]["root"], ctid)):
            process = subprocess.Popen(("mkdir %s/%d" % (self.config["vz-dirs"]["root"], ctid)), stdout=subprocess.PIPE, shell=True)
            assert(process.wait() == 0)
            assert(os.path.isdir("%s/%d" % (self.config["vz-dirs"]["root"], ctid)))

        # Generate config file
        self.write_config(("%s.conf" % source), 
                          ("%s%s%s" % (self.config["build"]["hostname-prefix"], ctid, self.config["build"]["hostname-suffix"])),
                          ("%s%s" % (self.config["build"]["ipaddr-prefix"], ctid)),
                          ("%s/%d.conf" % (self.config["vz-dirs"]["conf"], ctid)))

        return {"status": True,
                "runtime": (time.time() - starttime)}

    def write_config(self, sourcefile, hostname, ipaddr, outfile):
        config = self.import_ct_config(sourcefile)
        config["IP_ADDRESS"] = ipaddr
        config["HOSTNAME"] = hostname
        with open(outfile, "w") as fd:
            fd.write("# AUTOMATICALLY GENERATED FILE\n");
            fd.write("# SOURCE TEMPLATE: %s\n" % sourcefile);
            for key in sorted(config.keys()):
                fd.write("%s=\"%s\"\n" % (key, config[key]))

    def reset_ctfs_core(self, ctid, source):
        self.set_rebuilding_flag(ctid)
        process = subprocess.Popen(("rsync --delete -a %s/ %s/%d" % (source, self.config["vz-dirs"]["private"], ctid)), stdout=subprocess.PIPE, shell=True)
        assert(process.wait() == 0)
        self.clear_rebuilding_flag(ctid)

    def reset_ctfs(self, ctid):
        source = "%s/%s" % (self.config["build"]["templates"], self.config["build"]["source"])
        if not os.path.isdir(source) or not os.path.isfile("%s.conf" % source):
            print "ERROR: Bad Source \"%s\"" % source
            return False
        
        status = self.get_status(ctid)
        if status["running"] or status["rebuilding"]:
            print "ERROR: Bad Container is up"
            return False

        starttime = time.time()
        # Copy vz private data
        self.reset_ctfs_core(ctid, source)

        return {"status": True,
                "runtime": (time.time() - starttime)}

    def poweraction(self, command, ctid):
        starttime = time.time()
        process = subprocess.Popen(("vzctl %s %d" % (command, ctid)), stdout=subprocess.PIPE, shell=True)
        assert(process.wait() == 0)
        return (time.time() - starttime)

    def set_ct_power(self, ctid):
        if self.arguments is None:
            print "ERROR: power POST requires state argument"
            return False

        if not self.arguments.has_key("state"):
            print "ERROR: power POST requires state argument"
            return False
            
        state = self.arguments['state'].strip().lower()
        if state == "on":
            if self.get_status(ctid)["running"]:
                print "ERROR: ct is already on"
                return False

            return {"status": True,
                    "runtime": self.poweraction("start", ctid)}

        if state == "off":
            status = self.get_status(ctid)
            if not status["running"]:
                print "ERROR: ct is already off"
                return False

            # This is not populated if the server is down.
            if status["userActive"]:
                if self.arguments.has_key("force"):
                    if self.arguments['force'] != True:
                        print "ERROR: ct is in use"
                        return False
                else:
                    print "ERROR: ct is in use"
                    return False

            return {"status": True,
                    "runtime": self.poweraction("stop", ctid)}

        print "Unknown state \"%s\"" % state
        return False

    def _rebuilding_lockfile(self, ctid):
        # This is a simple lock file
        return ("%s/%d.conf.rebuilding" % (self.config["vz-dirs"]["conf"], ctid))

    def set_rebuilding_flag(self, ctid):
        # This is a potential race condition, but I'm unaware of any way to determine
        # from open() if the file existed.
        assert(self.check_rebuilding_flag(ctid) == False)
        with open(self._rebuilding_lockfile(ctid), "w") as fd:
            fd.write("%s" % time.time())

    def clear_rebuilding_flag(self, ctid):
        assert(self.check_rebuilding_flag(ctid) == True)
        os.remove(self._rebuilding_lockfile(ctid))

    def check_rebuilding_flag(self, ctid):
        return os.path.isfile(self._rebuilding_lockfile(ctid))
