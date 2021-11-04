import json
import requests
import sys

from arango import ArangoClient

# retrieving credentials from ArangoDB tutorial service
def getTempCredentials(
    tutorialName=None,
    credentialProvider="https://d383fa0b596a.arangodb.cloud:8529/_db/_system/tutorialDB/tutorialDB",
):
    with open("creds.dat", "r+") as cacheFile:
        contents = cacheFile.readline()
        if len(contents) > 0:
            login = None
            url = ""

            # check if credentials are still valid
            try:
                login = json.loads(contents)
                url = "https://" + login["hostname"] + ":" + str(login["port"])
            except:
                # Incorrect data in cred file and retrieve new credentials
                cacheFile.truncate(0)
                pass

            if login:
                try:
                    ArangoClient(hosts=url).db(
                        login["dbName"],
                        username=login["username"],
                        password=login["password"],
                    )
                    print("Reusing cached credentials.")
                    return login
                except:
                    print("Credentials expired.")
                    pass  # Ignore and retrieve new

        # Retrieve new credentials from Foxx Service
        print("Requesting new temp credentials.")
        if tutorialName:
            body = {"tutorialName": tutorialName}
        else:
            body = "{}"

        url = credentialProvider
        x = requests.post(url, data=json.dumps(body))

        if x.status_code != 200:
            print("Error retrieving login data.")
            sys.exit()
        # Caching credentials
        cacheFile.truncate(0)
        cacheFile.write(x.text)
        print("Temp database ready to use.")
        return json.loads(x.text)


# Using python-arango driver
def connect(login):
    url = "https://" + login["hostname"] + ":" + str(login["port"])
    client = ArangoClient(hosts=url)
    return client.db(
        login["dbName"], username=login["username"], password=login["password"]
    )
