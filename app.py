#!/usr/bin/env python

from __future__ import print_function

from flask import Flask
from flask import request
from flask import make_response

import json
import os
import requests
import datetime

from future.standard_library import install_aliases
install_aliases()

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)
    res = json.dumps(res, indent=4)

    print(res)

    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get('result').get('action') != 'speiseplan':
        return {}

    date = req.get('result').get('parameters').get('date')
    today = datetime.date.today().isoformat()
    start = 'Heit gibts '
    if date:
        print("Using specified date " + date)
        if date < today:
            start = 'Do gobs '
        elif date > today:
            start = 'Do gibts '
        url = "http://openmensa.org/api/v2/canteens/229/days/%s/meals" % date
    else:
        url = "http://openmensa.org/api/v2/canteens/229/days/%s/meals" % today

    print("Requesting menu from " + url)

    r = requests.get(url)

    # dummy response
    res = {
        'speech': "Nix wissen.",
        'displayText': "Nix wissen.",
        'source': 'openmensa.org'
    }

    if r.status_code == 200:
        print(r.json())
        res['speech'] = start + ", ".join(map(lambda x: x['name'], r.json()[:3]))
        res['displayText'] = res['speech']
    elif r.status_code == 404:
        res['speech'] = "Des is koa Mensadog, Depp!"
        res['displayText'] = res['speech']

    return res


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
