import sys      
import requests
from requests.auth import HTTPBasicAuth
import json

project = sys.argv[1]
build_state = sys.argv[2]
commit_hash = sys.argv[3]
build_no = sys.argv[4]
build_url = sys.argv[5]

usr = sys.argv[6] # User for Bitbucket
pws = sys.argv[7] # Password for Bitbucket

bitbucket_url = 'https://api.bitbucket.org/2.0/repositories/zivadynamics/worldtree/commit/'  + commit_hash + '/statuses/build'
headers = {'Content-Type': 'application/json'}

datas = {
    "state": build_state,
	"key": "{0}-AWS".format(project),
	"name": "{0} build in AWS".format(project),
	"url": build_url,
	"description": "{0} build in AWS #{1}".format(project, build_no)
}

r = requests.post(bitbucket_url, json=datas, auth=HTTPBasicAuth(usr, pws), headers=headers)
# Response code 201 - new status added, 200 - existing status updated.
if r.status_code == 200 or r.status_code == 201:
    print("{0} build in AWS #{1} set {2}".format(project, build_no, build_state))
else:
    print("Bitbucket API error - {0}".format(r.status_code))