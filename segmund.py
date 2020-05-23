from cloudant import Cloudant
from cloudant.document import Document
from flask import Flask, render_template, request, jsonify, redirect
import atexit
import os
import json
import requests
import time
import strava

app = Flask(__name__, static_url_path='')

# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

app_cfg = None
if 'APP_CONFIG' in os.environ:
    print('Found ENV APP_CONFIG')
    app_cfg = json.loads(os.getenv('APP_CONFIG'))
elif os.path.isfile('config.json'):
    with open('config.json') as f:
        print('Found local APP_CONFIG')
        app_cfg = json.load(f)

current_domain = "http://localhost:{}".format(str(port))
if 'VCAP_APPLICATION' in os.environ:
    vcap_app = json.loads(os.getenv('VCAP_APPLICATION'))
    current_domain = "https://{}".format(vcap_app['application_uris'][0])

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

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/register', methods=['GET'])
def initiate_registration_process():
    auth_url = strava.get_auth_url(app_cfg['STRAVA_CLIENT_ID'], current_domain)
    return render_template('register.html', auth_url=auth_url)

@app.route('/register-result', methods=['GET'])
def get_registration_result():
    return app.send_static_file('reg-result.html')

@app.route('/results', methods=['GET'])
def get_hop_segment_results():
    # TODO: date input
    leader_results = strava.hop_segment_leaders(app_cfg, "YYYY-MM-DD")
    return render_template('results.html', results=leader_results)


# /* Endpoint to register user token to database.
# *  Send a GET request to /exchange_token with params: state, code, scope
# *  Example: exchange_token?approval_prompt=force&scope=read_all,profile:read_all,activity:read_all
# */
@app.route('/exchange_token', methods=['GET'])
def register_user():
    state = request.args.get('state')
    auth_code = request.args.get('code')
    scope = request.args.get('scope')

    user = strava.register_user(app_cfg['STRAVA_CLIENT_ID'], app_cfg['STRAVA_SECRET'], auth_code)

    if user is None:
        return "Failed to register user with Strava"

    if Document(db, user['_id']).exists():
        print("User id={} exists already, Updating.".format(user['_id']))
        user_document = db[user['_id']]
        user_document.update(user)
        user_document.save()
    else:
        print ("Creating User: {}".format(user))
        user_document = db.create_document(user)
        user['_id'] = user_document['_id']

    if user_document.exists():
        print('Doc with _id={}'.format(user['_id']))

    return redirect('/users?firstname={}'.format(user['firstname']), code=302)

@app.route('/users', methods=['GET'])
def get_users():
    if client:
        firstname = request.args.get('firstname')
        #current_ms_time = int(round(time.time()))
        selector = {'type': {'$eq': 'user'}}
        docs = db.get_query_result(selector)
        return render_template('users.html', users=docs, firstname=firstname)
    else:
        print('No database')
        return jsonify([])

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
