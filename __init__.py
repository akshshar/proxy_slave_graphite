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
import pdb
import re

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

GRAPHITE_SERVER = "http://10.105.237.219"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
MOUNT_BRANCH = {}
BRANCH_COUNT = 0

#Function to convert a list of indices to a dict path
def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value

def metric_list(prev_mount, mount):
    metric_url = GRAPHITE_SERVER + "/metrics/expand/?query=collectd"+ prev_mount +  mount + ".*"
    metric_result = requests.get(metric_url)
    results = json.loads(metric_result.content)["results"]
    return results

#Start the lldp data gathering thread
def lldp_gather():
    shell_cmd = "python "+ABS_PATH+"/heat_map_gen.py -u akshshar -p cisco123 --ip-list 172.16.11.254 172.16.11.253 172.16.11.252 172.16.11.251 172.16.11.1 172.16.11.2"
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


def update_mnt_branch (branch_list, prev_mount):
       global BRANCH_COUNT, MOUNT_BRANCH
       BRANCH_COUNT = BRANCH_COUNT + 1
       MOUNT_BRANCH["branch_"+str(BRANCH_COUNT)] = {"branch" : branch_list, "prev_mount" : prev_mount}

def get_mnt_branch_keyed_list():
    branch_keys = []
    #Obtain list of keys from mount branch
    for key, value in MOUNT_BRANCH.iteritems():
         branch_keys.append(key)

    return branch_keys


def store_nd_stats():
    shell_cmd = "python "+ABS_PATH+"/store_nd_stats.py"
    print "shell_cmd is "+str(shell_cmd)

    try:
        out = subprocess.call(shlex.split(shell_cmd))
    except:
        print "Failed to run the store_nd_stats script"

    Timer(60, store_nd_stats).start()

    #Walk through the entire collectd metric list using Graphite's API
#    global MOUNT_BRANCH
#    collectd_metrics = {}
    #Prepare a list of nodes
#    node_list = []
#    metric_nodes_collectd_url = GRAPHITE_SERVER + "/metrics/expand/?query=collectd.*"
#    output = requests.get(metric_nodes_collectd_url)
#    prev_mount = "."
#    mount_list = []
#    for node in json.loads(output.content)["results"]:
#        node = re.sub('^collectd\.', '' , node)
#        node_list.append(node)
#        collectd_metrics[node] = {}
#    update_mnt_branch(node_list, prev_mount)
   
#    keys_done = 1
#    key_index = 1
    #key = get_mnt_branch_keyed_list()[key_index] dd
   
#    while(True): 
#        for mount in MOUNT_BRANCH["branch_"+str(key_index)]["branch"]:
#            results = metric_list(MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"], mount)
#            if results == []:
#                print "Result was empty!!"
                #This is a terminal metric. Determine its summarized value over the last 1 minute
#                render_url = GRAPHITE_SERVER + "/render?target=summarize(collectd"+ MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"] +  mount+", \"1min\", \"avg\", true)&from=-1min&format=json"
#                metric_value = requests.get(render_url)
#                mount_value_list = filter(None, (prev_mount+mount).split(".")) 
                #pdb.set_trace()
#                nested_set(collectd_metrics, mount_value_list, json.loads(metric_value.content)[0]['datapoints'][0][0]) 
#                break

#            prev_mount = MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"]+mount+"."
#            count = 0
#            for metric in results:
#                mount =  re.sub('^collectd'+prev_mount, '' , metric)
#                results[count] = mount
#                count = count + 1
#            update_mnt_branch(results, prev_mount)
#            mount_list =  filter(None, prev_mount.split("."))
#            for mount in results:
#                mount_list.append(mount)
                #print "MPOUNT LIST IS ---> !!!!!"
                #print mount_list
#                nested_set(collectd_metrics, mount_list, {})  
#                mount_list = mount_list[:-1]
#        MOUNT_BRANCH.pop("branch_"+str(key_index), None)
#        key_index = key_index + 1
#        if ("branch_"+str(key_index)) not in MOUNT_BRANCH:
#            break

#    try:
#        pickle.dump(collectd_metrics, open("graphite_nd_stats", "wb"))     
#        MOUNT_BRANCH = {}
#        response  = {"result" : "success"}
#    except:
#        response  = {"result" : "failure"}


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


@app.route('/gather-nd-stats')
def gather_nd_stats():
    try:
        collectd_metrics = pickle.load( open( "graphite_nd_stats", "rb" ) )         
        response = {"result" : "success" , "collectd_metrics" : collectd_metrics}
    except:
        response = {"result" : "failure, try again", "collectd_metrics" : ""}

    return jsonify(response)
 
if __name__ == '__main__':
    lldp_gather()
    store_nd_stats()
    app.run(host='0.0.0.0',port=6302, debug=True, use_reloader=False)



