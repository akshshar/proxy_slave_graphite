import networkx as nx
import os
from pprint import pprint
import json
import time
import pdb
import getpass
import paramiko
import argparse
from networkx.readwrite import json_graph


def run_ssh_cmd(host, user, pswd, cmd):
    ssh_session = paramiko.SSHClient()
    ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_session.connect(host, username=user, password=pswd, timeout=5)
    #ssh2.connect('localhost', username='ubuntu', password='cisco', port=7060,timeout=5)
    stdin, stdout, stderr = ssh_session.exec_command(cmd)
    lldp_out = stdout.read()

    ssh_session.close()
    return lldp_out

def kv_to_dict(kv_obj):
    output_dict = {}
    lldp_entries = kv_obj.split("\n")


    for entry in lldp_entries:
        try:
            path, value = entry.strip().split("=", 1)
            path = path.split(".")
            path_components, final = path[:-1], path[-1]
        except:
            print "Bad entry value, ignoring..."
            continue
 
        current_dict = output_dict
        for path_component in path_components:
            current_dict[path_component] = current_dict.get(path_component, {})
            current_dict = current_dict[path_component]
        current_dict[final] = value


    return output_dict

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--ip-list', help="List of network node ip addresses", nargs='+', type=str)
parser.add_argument('-u', '--user', help="username", nargs='+', type=str)
parser.add_argument('-p', '--pswd', help="password", nargs='+', type=str)
args =  parser.parse_args()

#place in the right buckets
user = args.user[0]
pswd = args.pswd[0]
ip_list = args.ip_list


#Use paramiko to ssh and run the lldp command on each host

host_dict = {}
graph = nx.Graph()

for host in ip_list:
    cmd = "lldpctl -f keyvalue"
    lldp_kv = run_ssh_cmd(host, user, pswd, cmd)
    #Convert into dictionary
    lldp_dict = kv_to_dict(lldp_kv)
    #pprint(lldp_dict)
    cmd = "hostname"
    name = run_ssh_cmd(host, user, pswd, cmd)
      
    host_dict[host] = {"lldp_dict": lldp_dict, "name" : name.rstrip('\n')}     
    #Now let's parse and obtain the edges/nodes for the graph
  
    #Create an edge object
    head_node = {"name": name.rstrip('\n'), "ip": host} 

    graph.add_node(head_node["name"]) 
    intf_list = []
    
    for k,v in lldp_dict["lldp"].iteritems():
        intf_list.append(k)
     
    edgelist = []
    for intf in intf_list:
        tail_node = lldp_dict["lldp"][intf]["chassis"]["name"].rstrip('\n') 
        edge_obj = {"tail": tail_node , "head": head_node["name"], "intf": intf}
        graph.add_edge(edge_obj["tail"], edge_obj["head"])
        edgelist.append(edge_obj)
        
    host_dict[host]["edges"] = edgelist


d = json_graph.node_link_data(graph)
json.dump(d, open('/home/akshshar/topo/static/js/topo.json','w'))
print('Wrote node-link JSON data')
print os.stat("/home/akshshar/topo/static/js/topo.json")
