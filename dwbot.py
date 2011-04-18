#!/usr/bin/python3
from os.path import exists
from sys import argv
import sys
import http.client
from urllib.parse import urlencode
import json


class DWSession():
    def __init__(self):
        self.token = None
        self.PMDSUSSID = None
        self.conn = http.client.HTTPConnection("en.pokemon-gl.com")
        
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
            sys.exit ("Login failed.  Run python3 dwbot.py username.")
        else:
            print ("Got token!")
            if self.member['member_savedata_id'] == None:
                sys.exit("Please enter the dream world normally first.")
            print("{} - game {} ({}), Pokémon {}".format(self.member['pgl_name'], self.member['rom_name'], self.member['player_name'], self.member['pokemon_name']))

    def request_page(self, p, member_id= None):
        url = "/api/?"
        get = [("p", p)]
        if member_id != None:
            get.append(("member_savedata_id", member_id))
        if self.token != None:
            get.append(("token", self.token))
        url += urlencode(get)
        self.conn.request("GET", url, None, {"Cookie": "PMDSUSSID={}; locale=en".format(self.PMDSUSSID)})
        r = self.conn.getresponse()
        data = r.read().decode("utf-8")
        tree = json.loads(data)
        if 'error' in tree:
            error = tree['error']
            raise RuntimeError(error['code'], error['mess'], error['details'])
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
    
def print_berry_stats(croft_list):
    harvestable_berries = 0
    unwatered_berries = 0
    for berry in croft_list:
        if berry['kinomi_state']==3: harvestable_berries+=1
        if int(berry['dirt_hp']) < 50: unwatered_berries+=1
    print (" Harvestable berries: {}".format(harvestable_berries))
    print (" Unwatered berries: {}".format(unwatered_berries))

dw = DWSession()
dw.get_token()

berry_info = dw.request_page("pdw.croft.my_croft_list")
print_berry_stats(berry_info["croft_list"])
map_info = dw.request_page("pdw.home.my_island_area")
print ("List of friends:")
for friend in map_info ['friend_list']:
    print("{} ({})".format(friend['pgl_name'], friend['country_name']))
