#!/usr/bin/python3
from os.path import exists
from sys import argv
import sys
import http.client
from urllib.parse import urlencode
import json

debug = False

class DWSession():
    def __init__(self):
        self.token = None
        self.PMDSUSSID = None
        self.serv = "en"
        
    def get_PMDSUSSID(self, username, password):
        form_conn = http.client.HTTPSConnection("sso.pokemon.com")
        form_conn.request("GET", "/sso/login?service=https://www.pokemon.com/us/account/pgllogin&locale=en")
        r = form_conn.getresponse()
        data = r.read().decode("utf-8")
        def get_string(s):
            ret = data[data.find(s)+len(s):]
            return ret[:ret.find('"')]
        params = {"lt":get_string('<input type="hidden" name="lt" value="'), 'username':username, 'password':password, '_eventId':'submit', 'service':''}
        form_conn.request("POST", get_string('<form id="login-form" action="'), urlencode(params), {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"})
        r = form_conn.getresponse()
        data = r.read().decode("utf-8")
        new_url = get_string('top.location.href="')
        if "https://www.pokemon.com/us/account/pgllogin" not in new_url:
            raise ValueError("Wrong username or password.")
        login_conn = http.client.HTTPSConnection("www.pokemon.com")
        def get_relative(url):
            return "/"+"/".join(url.split("/")[3:])
        login_conn.request("GET", get_relative(new_url), None, {"Cookie": r.getheader("Set-Cookie")})
        r = login_conn.getresponse()
        data = r.read().decode("utf-8")
        gl_conn = http.client.HTTPConnection("en.pokemon-gl.com")
        gl_conn.request("GET", get_relative(r.getheader("Location")), None, {"Cookie": r.getheader("Set-Cookie")})
        r = gl_conn.getresponse()
        
        return r.getheader("Set-Cookie").split(";")[0][10:]
        
    def get_token(self):
        if self.PMDSUSSID == None:
            if not exists("PMDSUSSID"):
                sys.exit("Not logged in.  Run python3 dwbot.py username.")
            with open("PMDSUSSID", "r") as f:
                self.PMDSUSSID = f.read().strip()
        
        init = self.request_page("pgl.top.init")
        self.member = init['member']
        self.token = init['token']
        if self.member == None or self.token == None:
            sys.exit ("Failed at getting the token.  Run python3 dwbot.py username, or copy the PMDSUSSID cookie for pokemon-gl.com from your browser manually and paste it in ./PMDSUSSID.")
        else:
            print ("Got token!")
            if self.member['member_savedata_id'] == None:
                sys.exit("Please enter the dream world normally first.")
            self.serv = "pdw"+self.member['world_id']
            print("{} - game {} ({}), Pokémon {}".format(self.member['pgl_name'], self.member['rom_name'], self.member['player_name'], self.member['pokemon_name']))

    def request_page(self, p, action="GET", **kvargs):
        conn = http.client.HTTPConnection(self.serv+".pokemon-gl.com")
        url = "/api/?"
        headers = {"Cookie": "PMDSUSSID={}; locale=en".format(self.PMDSUSSID)}
        get = [("p", p)]
        #if member_id != None:
        #    get.append(("member_savedata_id", member_id))
        if self.token != None:
            get.append(("token", self.token))
        get += kvargs.items()
        if debug: print(get)
        if action == "GET":
            url += urlencode(get)
            data = None
        elif action == "POST":
            headers["Content-type"]='application/x-www-form-urlencoded'
            data = urlencode(get)
        conn.request(action, url, data, headers)
        r = conn.getresponse()
        data = r.read().decode("utf-8")
        tree = json.loads(data)
        if 'error' in tree:
            error = tree['error']
            raise RuntimeError(error['code'], error['mess'], error['details'])
        if debug: print(tree)
        return tree
    
if len(argv)>1:
    if len(argv)==2:
        from getpass import getpass
        password = getpass("Please type your password: ")
    else:
        password = argv[2]
    print("Logging in.")
    dw = DWSession()
    PMDSUSSID = dw.get_PMDSUSSID(argv[1], password)
    with open("PMDSUSSID", "w") as f:
        f.write(PMDSUSSID)
    sys.exit("Successfully logged in, run the script without arguments now.")
    
def berry_stats(croft_list):
    harvestable_berries = 0
    unwatered_berries = 0
    for berry in croft_list:
        if berry['kinomi_state']==4: harvestable_berries+=1
        elif int(berry['dirt_hp']) < 50 : unwatered_berries+=1
    return ("Berries: {} harvestable, {} unwatered, {} total".format(harvestable_berries, unwatered_berries, len(croft_list)))
    
dw = DWSession()
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


