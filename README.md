# segmund

A cruddy thing for aggregating segment data from Strava.

## Getting Started

You'll need two config files locally -- contact @jglynn:

* `vcap-local.json` which contains Cloudant DB connecton details
* `config.json` which contains some Strava settings

Install Python 3

* I've found issues with 3.7.1 and Cloudant
* Locally I've had luck with 3.6.5
* IBM Cloud is running 3.8.2

## Running segmund locally

1. `python -m pip install -r requirements.txt` will install necessary Python deps
2. `python segmund.py` will start up the app, by default it listens on port `8000` locally

## Running on IBM Cloud

Commits to master automatically trigger CICD using [segmund-toolchain](https://cloud.ibm.com/devops/toolchains/09c005ff-2733-48e2-a792-1db8a909f8a2?env_id=ibm:yp:us-south)

[https://segmund.mybluemix.net/](https://segmund.mybluemix.net/)

## Checking logs

Install [IBM Cloud CLI](https://cloud.ibm.com/docs/cli?topic=cloud-cli-getting-started)

`ibmcloud login --sso`

`ibmcloud cf logs segmund-toolchain --recent`
