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


#Walk through the entire collectd metric list using Graphite's API
global MOUNT_BRANCH
collectd_metrics = {}
#Prepare a list of nodes
node_list = []
metric_nodes_collectd_url = GRAPHITE_SERVER + "/metrics/expand/?query=collectd.*"
output = requests.get(metric_nodes_collectd_url)
prev_mount = "."
mount_list = []
for node in json.loads(output.content)["results"]:
    node = re.sub('^collectd\.', '' , node)
    node_list.append(node)
    collectd_metrics[node] = {}
update_mnt_branch(node_list, prev_mount)

keys_done = 1
key_index = 1
#key = get_mnt_branch_keyed_list()[key_index] dd

while(True):
    for mount in MOUNT_BRANCH["branch_"+str(key_index)]["branch"]:
        results = metric_list(MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"], mount)
        if results == []:
            print "Result was empty!!"
            #This is a terminal metric. Determine its summarized value over the last 1 minute
            render_url = GRAPHITE_SERVER + "/render?target=summarize(collectd"+ MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"] +  mount+", \"1min\", \"avg\", true)&from=-1min&format=json"
            metric_value = requests.get(render_url)
            mount_value_list = filter(None, (MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"]+mount).split("."))
            print "mount = " + mount +" prev_mount = " +  MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"]+ ", render_url = "+render_url
            #pdb.set_trace()
            nested_set(collectd_metrics, mount_value_list, json.loads(metric_value.content)[0]['datapoints'][0][0])
            continue 

        prev_mount = MOUNT_BRANCH["branch_"+str(key_index)]["prev_mount"]+mount+"."
        count = 0
        for metric in results:
            mount =  re.sub('^collectd'+prev_mount, '' , metric)
            results[count] = mount
            count = count + 1
        update_mnt_branch(results, prev_mount)
        mount_list =  filter(None, prev_mount.split("."))
        for mount in results:
            mount_list.append(mount)
            #print "MPOUNT LIST IS ---> !!!!!"
            #print mount_list
            nested_set(collectd_metrics, mount_list, {})
            mount_list = mount_list[:-1]
    MOUNT_BRANCH.pop("branch_"+str(key_index), None)
    key_index = key_index + 1
    if ("branch_"+str(key_index)) not in MOUNT_BRANCH:
        break

try:
    pickle.dump(collectd_metrics, open("graphite_nd_stats", "wb"))
    MOUNT_BRANCH = {}
    response  = {"result" : "success"}
except:
    response  = {"result" : "failure"}

print response

