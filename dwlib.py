#!/usr/bin/python3
import http.client
from urllib.parse import urlencode
import json

debug = False

def get_PMDSUSSID(username, password):
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

class DWSession():
    def __init__(self, PMDSUSSID):
        self.token = None
        self.PMDSUSSID = PMDSUSSID
        self.serv = "en"
        
    def get_token(self):
        init = self.request_page("pgl.top.init")
        self.member = init['member']
        self.token = init['token']
        if self.member == None or self.token == None:
            raise RuntimeError("Failed at getting the token.  Run python3 dwbot.py username, or copy the PMDSUSSID cookie for pokemon-gl.com from your browser manually and paste it in ./PMDSUSSID.")
        else:
            print ("Got token!")
            if self.member['member_savedata_id'] == None:
                raise RuntimeError("Please enter the dream world normally first.")
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
