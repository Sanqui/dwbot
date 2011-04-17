#!/usr/bin/python3
from sys import argv
import http.client
from urllib.parse import urlencode
import json

if len(argv)<4:
    raise ValueError("Usage: python3 dwbot.py username password token")
    

class DWSession():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.conn = http.client.HTTPConnection("pdw3.pokemon-gl.com")
        
    def login(self):
        print("Logging in.")
        form_conn = http.client.HTTPSConnection("sso.pokemon.com")
        form_conn.request("GET", "/sso/login?service=https://www.pokemon.com/us/account/pgllogin&locale=en") #/us/account/logout?next=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Flogin%3Fservice%3Dhttps%3A%2F%2Fwww.pokemon.com%2Fus%2Faccount%2Fpgllogin%26locale%3Den%26renew%3Dtrue
        r = form_conn.getresponse()
        data = r.read().decode("utf-8")
        def get_string(s):
            ret = data[data.find(s)+len(s):]
            return ret[:ret.find('"')]
        action = get_string('<form id="login-form" action="')
        lt = get_string('<input type="hidden" name="lt" value="')
        params = {"lt":lt, 'username':self.username, 'password':self.password, '_eventId':'submit', 'service':''}
        form_conn.request("POST", action, urlencode(params), {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"})
        r = form_conn.getresponse()
        data = r.read().decode("utf-8")
        new_url = get_string('top.location.href="')
        if "https://www.pokemon.com/us/account/pgllogin" not in new_url:
            raise ValueError("Failed to login.")
        cookie = r.getheader("Set-Cookie")
        login_conn = http.client.HTTPSConnection("www.pokemon.com")
        def get_relative(url):
            return "/"+"/".join(url.split("/")[3:])
        login_conn.request("GET", get_relative(new_url), None, {"Cookie": cookie})
        r = login_conn.getresponse()
        cookie = r.getheader("Set-Cookie")
        new_url = r.getheader("Location")
        data = r.read().decode("utf-8")
        gl_conn = http.client.HTTPConnection("en.pokemon-gl.com")
        gl_conn.request("GET", get_relative(new_url), None, {"Cookie": cookie})
        r = gl_conn.getresponse()
        self.PMDSUSSID = r.getheader("Set-Cookie").split(";")[0][10:]
        print ("Got PMDSUSSID!: {}".format(self.PMDSUSSID))
        #self.PMDSUSSID = argv[1] # From cookie
        self.TOKEN = argv[3] # PWD-specific token, from URL

    def request_page(self, p, member_id= None):
        url = "/api/?"
        get = [("p", p), ("token", self.TOKEN)]
        if member_id != None:
            get.append(("member_savedata_id", member_id))
        url += urlencode(get)
        self.conn.request("GET", url, None, {"Cookie": "PMDSUSSID={}; locale=en".format(self.PMDSUSSID)})
        r = self.conn.getresponse()
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
    print (" Harvestable berries: {}".format(harvestable_berries))
    print (" Unwatered berries: {}".format(unwatered_berries))

dw = DWSession(argv[1], argv[2])
dw.login()

berry_info = dw.request_page("pdw.croft.my_croft_list")
print_berry_stats(berry_info["croft_list"])
map_info = dw.request_page("pdw.home.my_island_area")
print ("List of friends:")
for friend in map_info ['friend_list']:
    print("{} ({})".format(friend['pgl_name'], friend['country_name']))
    #print_berry_stats(request_page("pdw.croft.friend_croft_list", friend["member_savedata_id"]))
