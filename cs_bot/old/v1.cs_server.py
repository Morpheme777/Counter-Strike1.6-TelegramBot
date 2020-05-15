import requests
import re
import json
import warnings
warnings.filterwarnings("ignore")

class CSServer(object):
    def __init__(self, domain, username, password):
        self.domain = domain
        self.token = self.login(username, password)

    def login(self, username, password):
        url = "https://{}/api/token/".format(self.domain)
        payload = '{"login":"' + username + '","password":"' + password + '"}'
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': "application/json"
        }
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        authtoken = json.loads(response.text)['data']['access_token']
        return authtoken

    def getServerStats(self):
        url = "https://{}/api/gsinfo/7336".format(self.domain)
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': "application/json",
            'Authorization': "Bearer {}".format(self.token)
        }
        response = requests.request("get", url, headers=headers, verify=False)
        r = json.loads(response.text)
        return r
