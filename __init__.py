import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from pprint import pprint
import requests
from requests.auth import HTTPDigestAuth
import urlparse
import logging
import httplib
httplib.HTTPConnection.debuglevel = 1
import subprocess
import commands
import shlex
import json
from subprocess import Popen, PIPE
import time
import os.path as path
from threading import Timer
import pickle
import hashlib


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

#Start the lldp data gathering thread
def lldp_gather():
    shell_cmd = "python "+ABS_PATH+"/heat_map_gen.py -u akshshar -p cisco123 --ip-list 172.16.11.254 172.16.11.253 172.16.11.252 172.16.11.251"
    print "shell_cmd is "+str(shell_cmd)

    try:
        out = subprocess.call(shlex.split(shell_cmd))
    except:
        print "Failed to run the lldp_gather script" 

    Timer(30, lldp_gather).start()


def check_file_mod(path):
    fileChanged = False
    try:
        l = pickle.load(open("db"))
    except IOError:
        l = []
    db = dict(l)
    #this converts the hash to text
    checksum = hashlib.md5(open(path).read()).hexdigest()
    if db.get(path, None) != checksum:
        print "file changed"
        fileChanged = True
        db[path] = checksum
    pickle.dump(db.items(), open("db", "w"))
    return fileChanged


app = Flask(__name__)

@app.route('/')
def home():
        return render_template('topo.html')


@app.route('/check-topo')
def check_topo():
        fileMod = check_file_mod('/home/akshshar/topo/static/js/topo.json')
        if fileMod == True:
            response = {"status" : "changed"}
        else:
            response = {"status" : "unchanged"}
  
        return jsonify(response)


if __name__ == '__main__':
    lldp_gather()
    app.run(host='0.0.0.0',port=6302, debug=True, use_reloader=False)



