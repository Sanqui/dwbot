#!/usr/bin/python3
from os.path import exists
from sys import argv
import sys

from dwlib import *
    
if len(argv)>1:
    if len(argv)==2:
        from getpass import getpass
        password = getpass("Please type your password: ")
    else:
        password = argv[2]
    print("Logging in.")
    PMDSUSSID = get_PMDSUSSID(argv[1], password)
    with open("PMDSUSSID", "w") as f:
        f.write(PMDSUSSID)
    sys.exit("Successfully logged in, run the script without arguments now.")
    
if not exists("PMDSUSSID"):
    sys.exit("Not logged in.  Run python3 dwbot.py username.")
    
def berry_stats(croft_list):
    harvestable_berries = 0
    unwatered_berries = 0
    for berry in croft_list:
        if berry['kinomi_state']==4: harvestable_berries+=1
        elif int(berry['dirt_hp']) < 50 : unwatered_berries+=1
    return ("Berries: {} harvestable, {} unwatered, {} total".format(harvestable_berries, unwatered_berries, len(croft_list)))
    
with open("PMDSUSSID", "r") as f:
    dw = DWSession(f.read().strip())
dw.get_token()

visitor_data = dw.request_page("pdw.home.footprint_list", rowcount=28, offset=0)
requests = []
for visitor in visitor_data['list']:
    if visitor['friend_type'] == '1':
        requests.append(visitor['pgl_name']) 
print("Friend request from: {}.".format(", ".join(requests)))
berry_info = dw.request_page("pdw.croft.my_croft_list")
print(berry_stats(berry_info["croft_list"]))
map_info = dw.request_page("pdw.home.my_island_area")
print ("List of friends:")
for friend in map_info ['friend_list']:
    member_id = friend['member_savedata_id']
    area = dw.request_page("pdw.home.friend_island_area", friend_member_savedata_id=member_id)
    berries = dw.request_page("pdw.croft.friend_croft_list", member_savedata_id=member_id)['croft_list']
    print(" {} ({}) - {} friends, {}".format(friend['pgl_name'], friend['country_name'], len(area['friend_list']), berry_stats(berries)))
    
if input("Do you want to automatically water berries? ").lower().strip()=="y":
    try:
        visited_ids = []
        def recurs(friend, route):
            member_id = friend['member_savedata_id']
            if member_id not in visited_ids:
                visited_ids.append(member_id)
                area = dw.request_page("pdw.home.friend_island_area", friend_member_savedata_id=member_id)
                berries = dw.request_page("pdw.croft.friend_croft_list", member_savedata_id=member_id)['croft_list']
                unwatered_berries = 0
                for berry in berries:
                    if int(berry['dirt_hp']) < 50 and berry['kinomi_state'] != 4: 
                        unwatered_berries+=1
                        remains = dw.request_page("pdw.croft.friend_kinomi_watering", action="POST", member_savedata_id=member_id, my_croft_id=berry["my_croft_id"])['remains_watering']
                        print ("Remains watering: {}".format(remains))
                        if remains == 0:
                            sys.exit("Done watering!  Traversed over {} people.".format(len(visited_ids)))
                if unwatered_berries != 0:
                    print("{} > {} ({}) - {} unwatered berries".format(" > ".join(route), friend['pgl_name'], friend['country_name'], unwatered_berries))
                for friend2 in area['friend_list']:
                    recurs(friend2, route+[friend['pgl_name']]) 

        for friend in map_info ['friend_list']:
            recurs(friend, [])
    except KeyboardInterrupt:
        print("Search aborted.  Traversed over {} people.".format(len(visited_ids)))
