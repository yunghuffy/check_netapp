import os
import time
import sys
import socket
from NetApp.NaServer import *
from optparse import OptionParser


# Defining a main function to call all of our stuff
def main():
	
	# Here we need to sleep to make sure the timestamps
	# Between the two points are at least 1 second off
	#if(command == "read_total"):
	#	read_data = "read_total"
	#elif(command == "write_total"):
	#	read_data = "write_total"
	#else:
	#	print ("Invalid operation \n")
	#	print_usage()
	
	first_reads = get_reads(read_data)
	time.sleep(1.5)
	second_reads = get_reads(read_data)
	metric = per_second(first_reads, second_reads)
	if output_style == "nagios":
		nag_exit(metric[0], metric[1])
	elif output_style == "graphite":
		timestamp = int(time.time())
		message = 'netapp.perf.%s_per_second %s %d\n' % (metric[1], metric[0], timestamp)
		send_msg(message)
# We really need to be taking in args rather than writing down creds.
# We also need to make a user specifically to just query stats


# For starters let's create a function that gets one
# data point at one specific point in time
def get_reads(counter_type):
	
	# We need to build the xml to request nfs reads info
	# Use 'perf-object-get-instances' to get one instance
	
	get_reads = NaElement("perf-object-get-instances")
	get_reads.child_add_string("objectname", "nfsv4")
	counters = NaElement("counters")
	counters.child_add_string("counter", counter_type)
	get_reads.child_add(counters)
	instances = NaElement("instances")
	instances.child_add_string("instance", "vs1_rhev1")
	get_reads.child_add(instances)

	# Now use the above contstructed xml block to query
	# the API

	read_out = server.invoke_elem(get_reads)

	# Error handling, tattle if the call failed
	if(read_out.results_status() == "failed"):
		print (read_out.results_reason() + "\n")
		sys.exit(2)

	# This xml block contains what we are looking for
	# a counter of reads and a timestamp
	# Just need to walk down the tree to get them all

	instances_list = read_out.child_get("instances")
	instances = instances_list.children_get()
	for inst in instances:
		inst_counters = inst.child_get("counters")
		inst_data = inst_counters.child_get("counter-data")
		inst_values = inst_counters.children_get()
		for val in inst_values:
			name = val.child_get_string("name")
			value = val.child_get_string("value")
	
	timestamp = read_out.child_get_string("timestamp")

	return str(name), int(value), int(timestamp)

# Create a function that parses our information into one metric	

def per_second(first_array, second_array):
	
	name = first_array[0]
	first_value = first_array[1]
	first_time = first_array[2]

	second_value = second_array[1]
	second_time = second_array[2]
	per_second_metric = (second_value - first_value) / (second_time - first_time)
	return per_second_metric, name

# A function for proper Nagios exit codes
def nag_exit(metric, name):
	if (metric < warn_limit):
		print "OK - %d %s per second" % (metric, name)
		sys.exit(0)
	elif (metric >= warn_limit) & (metric < crit_limit):
		print "WARNING - %d %s per second" % (metric, name)
		sys.exit(1)
	elif (metric >= crit_limit):
		print "CRITICAL - %d %s per second" % (metric, name)
		sys.exit(2)
	else:
		print "UKNOWN - a bad response was received for %s" % name
		sys.exit(3)

# A function to send info to graphite
def send_msg(message):
	print 'Sending: \n%s' % message
	sock = socket.socket()
	sock.connect((CARBON_SERVER, CARBON_PORT))
	sock.sendall(message)
	sock.close()

# OptionParser is a much better way to handle commandline args

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
parser.add_option("-d", "--data-type", 
		action="store", type="string", dest="data_type",
		help='A counting variable API call to the NetApp')
parser.add_option("-w", "--warning", 
		action="store", type="int", dest="warn",
		help="Number of x per second for the plugin to warn. Must be less than crit")
parser.add_option("-c", "--critical",
		action="store", type="int", dest="critical",
		help="Number of x per second for the plugin to crit. Must be greater than warn")
parser.add_option("-s", "--output-style", dest="output_style",
		help="Choose whether this will be nagios output or graphite")
		
(opts, args) = parser.parse_args()
# push these variables to the main function to determine 
# which check we're doing and where
host = opts.host 
user = opts.user
pw = opts.password
command = opts.data_type
warn_limit = opts.warn
crit_limit = opts.critical
read_data = opts.data_type
output_style = opts.output_style
# Some options are mandatory
if crit_limit <= warn_limit:
	print "The CRITICAL threshold must be greater than the WARNING threshold."
	parser.print_help()
	exit(-1)

# Here is the basic server object for the NetApp
server = NaServer(host, 1, 21)
server.set_transport_type('HTTPS')
server.set_style('LOGIN')
server.set_admin_user(user, pw)


# Set up the carbon socket stuff
CARBON_SERVER = ur_host_here
CARBON_PORT = 2003
DELAY = 15 # secs

# Possible list/dict of metrics this script can parse:
# write_total, read_total

main()
