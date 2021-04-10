#!/usr/bin/env python3
import threading
import flask
import ariadne
import time
import os
from flask import Flask, redirect, url_for
from .lib.const import DB_UPDATE_FREQUENCY
from .lib.resolvers import query_resolver, talk_resolver, date_scalar
from db.src import fillDB19 as db_worker

# Flask setup
app = Flask(__name__)

# GraphQL setup
schema_file = ariadne.load_schema_from_path("schema.graphql")
schema = ariadne.make_executable_schema(
    schema_file, query_resolver, talk_resolver, date_scalar, ariadne.snake_case_fallback_resolvers)


@app.route('/')
def hello():
    return redirect(url_for('graphql'))

@app.route("/graphql", methods=["GET"])
def graphql_playground():
    return ariadne.constants.PLAYGROUND_HTML, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = flask.request.get_json()

    success, result = ariadne.graphql_sync(
        schema,
        data,
        context_value=flask.request,
        debug=app.debug
    )

    status_code = 200 if success else 400
    return flask.jsonify(result), status_code


#Backgrund dp updater
def checkDB():
    while True:
        print('Starting DB update check...')
        db_worker.updateDB()
        time.sleep(DB_UPDATE_FREQUENCY)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    worker = threading.Thread(target=checkDB, daemon=True)
    if os.environ['FLASK_ENV'] == 'production':
        worker.start()
    else:
        app.testing = True

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

