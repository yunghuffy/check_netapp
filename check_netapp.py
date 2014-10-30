import os
from NetApp.NaServer import *
from optparse import OptionParser


# Main function to handle our other functions
def main():
    if check == "vserver":
        vserver_check(vserver_name)
    elif check == "api":
        api_check()
    elif check == "cluster":
        cluster_check()
    else:
        volume_check(vol_name)
# Use this to test if the API is available
# Better than just a simple ping test
def api_check():
	get_api_status = NaElement("system-get-ontapi-version")
	api_status_out = server.invoke_elem(get_api_status)

	if (api_status_out.results_status() == "failed"):
		print ("CRITICAL - " + api_status_out.results_reason() + "\n")
		sys.exit(2)
	else:
		maj_vers = api_status_out.child_get_string("major-version")
		min_vers = api_status_out.child_get_string("minor-version")
		print "OK - API version %s.%s" % (maj_vers, min_vers)
		sys.exit(0)

# Getting more granular, check for cluster/node status
def cluster_check():
	
	# Query the API for cluster information
	get_cluster = NaElement("cluster-node-get-iter")
	get_cluster_out = server.invoke_elem(get_cluster)

	# Get cluster health if the API query completes and
	# add it to a dictionary with the key as cluster name
	cluster_health = {}
	if (get_cluster_out.results_status() != "passed"):
		print ("UKNOWN - unable to retrieve cluster status" 
				+ "\n" + api_status_out.results_reason())
		sys.exit(3)
	else:
		attr_list = get_cluster_out.child_get("attributes-list")
		cluster_node_info = attr_list.children_get()
		for clust in cluster_node_info:
			node_name = clust.child_get_string("node-name")
			node_health = clust.child_get_string("is-node-healthy")
			cluster_health[node_name] = node_health
	
	# Start a list of good nodes and bad nodes
	bad_node = []
	good_node = []
	for node in cluster_health:
		if cluster_health[node] != "true":
			bad_node.append(node)
		else:
			good_node.append(node)
	
	# If we have any bad nodes we need to crit
	# otherwise all clear
	if len(bad_node) >= 1:
		print ("CRITICAL - " + ', '.join(map(str, bad_node)) +
                " not in healthy state")
		sys.exit(2)
	else:
		print ("OK - " + ', '.join(map(str, good_node)) + " healthy")
		sys.exit(0)

def vserver_check(vs_name):
	# Here let's build a request to get specific
	# vserver information
	get_vs = NaElement("vserver-get-iter")
	get_vs_query = NaElement("query")
	get_vs_info = NaElement("vserver-info")
	get_vs_info.child_add_string("vserver-name", vs_name)
	get_vs_query.child_add(get_vs_info)
	get_vs.child_add(get_vs_query)

	# Now use the above xml block to quyery
	# the API

	vs_out = server.invoke_elem(get_vs)

	# Handle any errros with API, exit unkown if so
	if(vs_out.results_status()  == "failed"):
		print ("UKNOWN - " + vs_out.results_reason() + "\n")
		sys.exit(3)
       	
	# Walk down the xml tree to get name and state
	vs_attr = vs_out.child_get("attributes-list")
	vs_info = vs_attr.children_get()
	for vs in vs_info:
		name = vs.child_get_string("vserver-name")
		state = vs.child_get_string("state")
	
	# Nagios exit codes depending on state	
	if state == 'running':
		print "OK - vserver %s is running" % name
		sys.exit(0)
	else:
		print "CRITICAL - vserver %s is %s" % (name, state)
		sys.exit(2)
	
def volume_check(vol_name):
    # As usual, let's build the actual request xml
    # using volume-get-iter
    get_vol = NaElement("volume-get-iter")
    get_vol_query = NaElement("query")
    get_vol_query_attr = NaElement("volume-attributes")
    get_vol_id_attr = NaElement("volume-id-attributes")
    get_vol_id_attr.child_add_string("name", vol_name)
    get_vol_query_attr.child_add(get_vol_id_attr)
    get_vol_query.child_add(get_vol_query_attr)
    get_vol.child_add(get_vol_query)

    # Query the API
    vol_out = server.invoke_elem(get_vol)

    # Error handling again
    if(vol_out.results_status() == 'failed'):
        print ( "UNKNOWN - " + vol_out.results_reason() + "\n")
        sys.exit(3)

    # Walk down the tree and get the disk usage
    vol_alist = vol_out.child_get("attributes-list")
    vol_attr = vol_alist.child_get("volume-attributes")
    vol_space_attr = vol_attr.child_get("volume-space-attributes")
    vol_id_attr = vol_attr.child_get("volume-id-attributes")
    vol_name = vol_id_attr.child_get_string("name")
    vol_vs_name = vol_id_attr.child_get_string("owning-vserver-name")
    vol_uuid = vol_id_attr.child_get_string("uuid")
    vol_used_perc = vol_space_attr.child_get_string("percentage-size-used")
    vol_long_name = vol_vs_name + ":" + vol_name
    used_perc = int(vol_used_perc)

    # Nag handling
    if used_perc < warn_perc:
        print "OK - %s %d%% disk used." % (vol_long_name, used_perc)
        sys.exit(0)
    elif (used_perc >= warn_perc) & (used_perc < crit_perc):
        print "WARNING - %s %d%% disk used." % (vol_long_name, vol_used_perc)
        sys.exit(1)
    elif used_perc >= crit_perc:
        print "CRITICAL - %s %d%% disk used." % (vol_long_name, vol_used_perc)
        sys.exit(2)
    else:
        print "UNKOWN - unable to get disk stats."
        sys.exit(3)

# Use OptionParser to give us nice command line args

usage = "usage: %prog [options] arg1 arg2"
parser = OptionParser()
parser.add_option("-o", "--host",
                action="store", type="string", dest="host",
                help="The IP or hostname of the filer")
parser.add_option("-u", "--user",
                action="store", type="string", dest="user",
                help="Username with API access")
parser.add_option("-p", "--password",
                action="store", type="string", dest="password",
                help="A password")
parser.add_option("-k", "--check", 
                action="store", type="string", dest="check",
		        help="Which check to perform including vserver, api, cluster, volume")
parser.add_option("-s", "--vserver-name",
		        action="store", type="string", dest="vserver_name",
		        help="Define a vserver to check")
parser.add_option("-m", "--volume-name",
                action="store", type="string", dest="volume_name",
                help="Define a volume to check")
parser.add_option("-c", "--critical",
                action="store", type="string", dest="crit_perc",
                help="Critical threshold")
parser.add_option("-w", "--warning",
                action="store", type="string", dest="warn_perc",
                help="Critical threshold")

(opts, args) = parser.parse_args()
if not opts.host:
	parser.error('Host not given')
else:
	host = opts.host

if not opts.user:
	parser.error('User not given')
else:
	user = opts.user

if not opts.password:
	parser.error('Password not given')
else:
	pw = opts.password

if not opts.check:
	parser.error('No check defined')
else:
	check = opts.check		

if (check == "vserver") and not opts.vserver_name:
	parser.error('vserver requires a veserver name')
else:
	vserver_name = opts.vserver_name

if (check == "volume") and not opts.crit_perc:
    parser.error('You must set a critical threshold to check volume')
elif (check == "volume") and not opts.warn_perc:
    parser.error('You must set a warning threshold to check volume')
elif (check == "volume") and not opts.volume_name:
    parser.error('You must set a volume to check')
elif opts.volume_name:
    vol_name = opts.volume_name
    warn_perc = int(opts.warn_perc)
    crit_perc = int(opts.crit_perc)
# Instantiate our NetApp session
server = NaServer(host, 1, 21)
server.set_transport_type('HTTPS')
server.set_style('LOGIN')
server.set_admin_user(user,pw)
#Testing port for local machine
server.set_port('8080')
main()
