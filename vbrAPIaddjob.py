import sys
import time
import json
import requests

veeam_url = 'https://192.168.15.30:9419/api/'
APIUser = ".\Administrator"
APIUserPassword = 'Elkhart0!'

#
# request authentication token from the VBR Rest API
#
def login():
    accessToken = ""

    vHeaders = {'x-api-version': '1.0-rev2', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
    r = veeam_session.post(veeam_url+'oauth2/token', headers=vHeaders, data="grant_type=password&username=" + APIUser + "&password=" + APIUserPassword, verify=False)
    if r.status_code == 200:
        responseJSON = json.loads(r.text)
        accessToken = responseJSON["access_token"]

    return accessToken

#
# logoff session
#
def logoff(authHeaders):
    logoutResponse = veeam_session.post(veeam_url+'oauth2/logout', headers=authHeaders, verify=False)

    return logoutResponse.status_code


def lookupVM(authHeaders, vcenterAddy, vmName):
    try:
        getViObjects = veeam_session.get(veeam_url+'v1/inventory/vmware/hosts/' + vcenterAddy, headers=authHeaders, verify=False)
        ViObjects = json.loads(getViObjects.text)
        for obj in ViObjects['data']:
            #print('object - ' + str(obj['inventoryObject']['name']) + ' type - ' + str(obj['inventoryObject']['type']))
            if obj['inventoryObject']['name'] == vmName:
                return obj['inventoryObject']['objectId']
        return 0

    except:
       print('Exception in lookupVM')
       return 0

def lookupRepo(authHeaders, repoName):
    try:

        getRepos = veeam_session.get(veeam_url+'v1/backupInfrastructure/scaleOutRepositories', headers=authHeaders, verify=False)
        repos = json.loads(getRepos.text)
        for repo in repos['data']:
            #print('repo - ' + str(repo['name']))
            if repo['name'] == repoName:
                return repo['id']
        return 0

    except:
        print('Exception in lookupRepo')
        return 0

def addJob(authHeaders, backupRepoID, vCenter, vmName, vmID, jobName):
    try: 
        jobData = {'name':jobName,
                   'description':'API-added backup job',
                   'type':'Backup',
		   'isHighPriority':False,
                   'virtualMachines': {
			'includes': 
				[
					{'hostname': vCenter,
					'name': vmName,
					'type': 'VirtualMachine',
					'objectId': vmID}
				]
		   },
 		   'storage': {
			'backupRepositoryID': backupRepoID,
			'backupProxies' : {
				'autoselection': True 
			},
			'retentionPolicy': {
				'type': 'Days',
				'quantity': 8
			},
			'advancedSettings': {
				'backupModeType': 'Incremental',
				'storageData': {
					'excludeSwapFileBlocks': True,
					'storageOptimization': 'Auto'
				}
			}
		   },
		   'guestProcessing': {
			'appAwareProcessing': {
				'isEnabled': False
			},
			'guestFSIndexing': {
				'isenabled': False
			}
		   },
		   'schedule': {
			'runAutomatically': True
		   }
 	   }

        authHeaders = {'x-api-version': '1.0-rev2', 'Accept': 'application/json', 'Authorization': 'Bearer ' + aToken}
        jobAddResponse = veeam_session.post(veeam_url+'v1/jobs', headers=authHeaders, json=jobData, verify=False)
      
        if jobAddResponse.status_code == 201:
            return True
        else:
            errJSON = json.loads(serverAddResponse.text)
            print "Add job error - " + errJSON["errorCode"] + ":" + errJSON["message"]
            return False

    except:
        print("Exception in addJob() - " + str(jobAddResponse.text))
        return False

def xxx(a,b,c,d,e,f):
    print('xxx('+a+', '+b+', '+c+', '+d+', '+e+', '+f+')')
    return
    
#
# retrieve certificate thumbprint from ESXi, vCenter server to avoid
#
# MAIN
#
# cmdline <reponame> <vcenter> <vm> <jobname>
#
veeam_session = requests.session()
try:
    if len(sys.argv) > 3:
        aToken = login()
        if aToken != "":
            authHeaders = {'x-api-version': '1.0-rev2', 'Accept': 'application/json', 'Authorization': 'Bearer ' + aToken}
            repoID = lookupRepo(authHeaders, sys.argv[1])
            if repoID != 0:
                print('found repo')
                vmID = lookupVM(authHeaders, sys.argv[2], sys.argv[3])
                if vmID != 0:
                    print('found vm')
                    print('addJob('+str(authHeaders)+', '+repoID+', '+sys.argv[2]+', '+sys.argv[3]+', '+vmID+', '+sys.argv[4]+')')
                    addJob(authHeaders, repoID, sys.argv[2], sys.argv[3], vmID, sys.argv[4])
                else:
                    print('VM not found!')
            else:
                print('repo not found!')
            logoff(authHeaders)
        else:
            print "Login / authentication failure"
    else:
        print 'USAGE: vbrAPIaddjob.py <reponame> <vcenter> <vm> <jobname>'

except:
    print "Exception in main"
