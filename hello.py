from cloudant import Cloudant
from cloudant.document import Document
from flask import Flask, render_template, request, jsonify, redirect
import atexit
import os
import json
import requests
import time

app = Flask(__name__, static_url_path='')

strava_client_id = "47678"
strava_secret = "3a34337c2ba671471ba40ef191ec6d94805fdae2"

db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/register', methods=['GET'])
def initiate_registration():
    return app.send_static_file('register.html')

@app.route('/register-result', methods=['GET'])
def registration_result():
    return app.send_static_file('reg-result.html')

# /* Endpoint to register user token to database.
# *  Send a GET request to localhost:8000/api/exchange_token with body
# *  Example: exchange_token?approval_prompt=force&scope=read_all,profile:read_all,activity:read_all
# */
@app.route('/api/exchange_token', methods=['GET'])
def register():
    state = request.args.get('state')
    auth_code = request.args.get('code')
    scope = request.args.get('scope')
    print("state={},code={},scope={}".format(state, auth_code, scope))

    # Validate scope
    print("calling Strava...")
    strava_token_url="https://www.strava.com/oauth/token"
    strava_token_params = {
        'client_id': strava_client_id,
        'client_secret': strava_secret,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    reg_user_resp = requests.post(strava_token_url, params=strava_token_params, headers={'Content-Type':'application/json'})

    print(reg_user_resp)

    if(reg_user_resp.status_code > 200):
        return  "Error registering with strava: {}".format(reg_user_resp.json())

    reg_user_resp_json = reg_user_resp.json()

    data = {
        "_id": str(reg_user_resp_json['athlete']['id']),
        "type": "user",
        "name": reg_user_resp_json['athlete']['username'],
        "firstname": reg_user_resp_json['athlete']['firstname'],
        "lastname": reg_user_resp_json['athlete']['lastname'],
        "access_token": reg_user_resp_json['access_token'],
        "expires_at": reg_user_resp_json['expires_at'],
        "refresh_token": reg_user_resp_json['refresh_token']
    }

    print("checking if user={} exists already...".format(data['_id']))
    if Document(db, data['_id']).exists():
        print("User exists, Updating.")
        user_document = db[data['_id']]
        print(data)
        print(user_document)
        data['lastname'] = 'glynn2'
        user_document.update(data)
        print(user_document)
        user_document.save()
    else:
        print ("Creating User...{}".format(data))
        user_document = db.create_document(data)
        data['_id'] = user_document['_id']

    if user_document.exists():
        print('Doc with _id={}'.format(data['_id']))

    return redirect('/register-result', code=302)

# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8000/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:

        current_ms_time = int(round(time.time()))

        # Retrieve documents where the name field is 'foo'
        users = []
        selector = {'type': {'$eq': 'user'}}
        docs = db.get_query_result(selector)
        for doc in docs:
            print(doc)
            print("Expired? {} < {} ? {}".format(doc['expires_at'], current_ms_time, (doc['expires_at'] < current_ms_time)))
            users.append(doc['_id'])
        return jsonify(users)
        # Get all of the documents from my_database
        #for document in my_database:
        #    print(document)
        #return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('No database')
        return jsonify([])

@app.route('/api/delete', methods=['GET'])
def delete_all():
    for doc in db:
        doc.delete();
    return jsonify("{response: deleted_all}")
# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8000/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    data = {'name':user}
    print("received name={}".format(user))
    if client:
        my_document = db.create_document(data)
        data['_id'] = my_document['_id']
        if my_document.exists():
            print('Created doc with _id={}'.format(data['_id']))
        return jsonify(data)
    else:
        print('No database')
        return jsonify(data)

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
