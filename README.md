proxy_slave_graphite
=========
Multiple components within the project.

Primarily a python flask server which plugs into a python lldp topology visualizer using Networkx and D3.js with auto-refresh capabilities.

Further flask server also extracts data via graphite's REST end points and runs topology_gathering and graphite_tree extraction in background threads.

This python_server will plug into slave_proxies for mesos/swarm etc. as a resource end-point.
As it grows, the server will support data gathering from a variety of tools, thereby keeping telemetry sources and Cluster Scheduler dependencies completely isolated.
More to come.
