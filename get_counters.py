from NetApp.NaServer import *

# Let's gather all the counters for perf_objects
def get_counters(na_object):

    # Start out by building the xml necessary for the request
    get_counters = NaElement("perf-object-counter-list-info")
    get_counters.child_add_string("objectname", na_object)
    get_counters.sprintf()
    # Invoke the server
    counters_out = server.invoke_elem(get_counters)
    

    # Lot of shit to walk down here
    counters_list = counters_out.children_get()
    count_dict = {}
    for i in counters_list:
	counter_info = i.children_get()
	for count in counter_info:
        	count_desc = count.child_get_string("desc")
        	count_name = count.child_get_string("name")
        	count_unit = count.child_get_string("unit")
    		count_list = [count_desc, count_unit]
		count_dict[count_name] = count_list
	return count_dict


# Function to gather all performance objects into one array	
def get_all_obj():	
    
    # Very simple API call here
    get_obj = NaElement("perf-object-list-info")
    
    # Invoke the server
    obj_out = server.invoke_elem(get_obj)
    obj_out.sprintf()
    
    # Walk down the xml
    obj_list = obj_out.children_get()
    obj_name_list = []
    for i in obj_list:
        obj_info = i.children_get()
        for obj in obj_info:
            obj_name = obj.child_get_string("name")
            obj_name_list.append(obj_name)
    return obj_name_list


# Replace this with your info
server = NaServer(host, 1, 21)
# Only used for testing
server.set_port(443)
user = user_name
pw = password
# Basic server details
server.set_transport_type('HTTPS')
server.set_style('LOGIN')
server.set_admin_user(user, pw)


# Define a main function, more 'pythonicly'
if __name__ == "__main__":
    for i in get_all_obj():
        print get_counters(i)    
