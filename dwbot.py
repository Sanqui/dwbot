from sys import argv
import http.client
from urllib.parse import urlencode
import json

PMDSUSSID = argv[1] # From cookie
TOKEN = argv[2] # From URL

def request_page(p, member_id= None):
    host = "pdw3.pokemon-gl.com"
    headers = {
    "Cookie": "PMDSUSSID={}; locale=en".format(PMDSUSSID)
    }
    conn = http.client.HTTPConnection(host)
    url = "/api/?"
    get = [("p", p), ("token", TOKEN)]
    if member_id != None:
        get.append(("member_savedata_id", member_id))
    url += urlencode(get)
    conn.request("GET", url, None, headers)
    r = conn.getresponse()
    data = r.read().decode("utf-8")
    tree = json.loads(data)
    if 'error' in tree:
        error = tree['error']
        raise RuntimeError(error['code'], error['mess'], error['details'])
    return tree
    
def print_berry_stats(croft_list):
    harvestable_berries = 0
    unwatered_berries = 0
    for berry in croft_list:
        if berry['kinomi_state']==3: harvestable_berries+=1
        if int(berry['dirt_hp']) < 50: unwatered_berries+=1
        #print(berry['dirt_hp'])
    print (" Harvestable berries: {}".format(harvestable_berries))
    print (" Unwatered berries: {}".format(unwatered_berries))

berry_info = request_page("pdw.croft.my_croft_list")
print_berry_stats(berry_info["croft_list"])
map_info = request_page("pdw.home.my_island_area")
print ("List of friends:")
for friend in map_info ['friend_list']:
    print("{} ({})".format(friend['pgl_name'], friend['country_name']))
    #print_berry_stats(request_page("pdw.croft.friend_croft_list", friend["member_savedata_id"]))













