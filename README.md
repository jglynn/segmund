# segmund-py

A cruddy thing for aggregating segment data from Strava.

## Getting Started

You'll need two config files locally -- contact @jglynn:

`vcap-local.json` which contains Cloudant DB connecton details

`config.json` which contains some Strava settings

Python 3+ is ideal although I found issues with 3.7.1 and Cloudant.

Locally I've had luck with 3.6.5 and it's running 3.8.2 on IBM Cloud.

## Running segmund locally

`python -m pip install -r requirements.txt` will install necessary Python deps

`python segmund.py` will start up the app, by default it listens on port 8000 locally

## Running on IBM Cloud CF

[https://segmund.mybluemix.net/](https://segmund.mybluemix.net/)

## Deploying

`ibmcloud login --sso`

`ibmcloud cf push`


## Checking logs

`ibmcloud cf logs segmund-py --recent`
