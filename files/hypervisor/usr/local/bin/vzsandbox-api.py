#!/usr/bin/python -tt

Config={}

from flask import Flask,abort,request
from flask.ext import restful
import sys
import vzsandboxlib

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


def main():
    global Config
    Config = vzsandboxlib.loadConfig()
    if Config == False:
        return 1

    app = Flask(__name__)
    api = restful.Api(app)
    
    api.add_resource(VZCTAPI, '/ct/<int:ctid>/<string:action>')
    api.add_resource(Delay, '/delay/<int:secs>')
    api.add_resource(Status, '/status/<string:location>')

    if Config['server'].has_key("debug"):
        app.run(debug=True)
    else:
        app.run(host=Config['server']['bind-address'])
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
    
