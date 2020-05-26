"""Services and utilities for Cloudant database."""
import os
import json
import warnings

import cloudant
import flask
from flask import current_app, _app_ctx_stack


class FlaskCloudant(object):
    """Flask extension that connects to CloudantDB."""
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: flask.Flask):
        """Initialize the extension.

        Based on VCAP_SERVICES in environment or vcap-local.json (if present)
        sets the following default app config parameters:
            CLOUDANT_DB_NAME
            CLOUDANT_USERNAME
            CLOUDANT_PASSWORD
            CLOUDANT_URL

        If necessary, these can be overridden by setting the repsective
        parameters in the Flask app config.
        """
        if 'VCAP_SERVICES' in os.environ:
            vcap = json.loads(os.getenv('VCAP_SERVICES'))
            if 'cloudantNoSQLDB' in vcap:
                creds = vcap['cloudantNoSQLDB'][0]['credentials']
                app.logger.info(
                    "Setting default Cloudant user, password, and host "
                    "based on file VCAP_SERVICES.")
        elif os.path.isfile('vcap-local.json'):
            with open('vcap-local.json') as f:
                vcap = json.load(f)
                creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
                app.logger.info(
                    "Setting default Cloudant user, password, and host "
                    "based on file vcap-local.json.")
        else:
            app.logger.warning(
                "Failed to access VCAP credentials to set defaults"
                "for Cloudant extension.")

        app.config.setdefault('CLOUDANT_DB_NAME', 'mydb')
        app.config.setdefault('CLOUDANT_USERNAME', creds['username'])
        app.config.setdefault('CLOUDANT_PASSWORD', creds['password'])
        app.config.setdefault('CLOUDANT_URL', f"https://{creds['host']}")
        app.teardown_appcontext(self.teardown)

    def connect(self):
        """Connect to the database based on app configuration."""
        client = cloudant.Cloudant(current_app.config['CLOUDANT_USERNAME'],
                                   current_app.config['CLOUDANT_PASSWORD'],
                                   url=current_app.config['CLOUDANT_URL'],
                                   connect=True)
        return client

    def teardown(self, exception):
        ctx = _app_ctx_stack.top
        if hasattr(ctx, 'cloudant_client'):
            ctx.cloudant_client.disconnect()

    @property
    def client(self):
        """The Cloudant client object connected to the database host."""
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'cloudant_client'):
                ctx.cloudant_client = self.connect()
            return ctx.cloudant_client

    @property
    def db(self):
        """The Cloudant DB connection connected through the client."""
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'cloudant_db'):
                ctx.cloudant_db = self.client.create_database(
                    current_app.config['CLOUDANT_DB_NAME'],
                    throw_on_exists=False)
            return ctx.cloudant_db
