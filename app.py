#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

    action = req.get('result').get('action')
    if action == 'menueauskunft':
        res = processMenueAuskunft(req)
    elif action == 'chucknorris':
        res = processChuckNorris(req)
    elif action == 'bundesliga':
        res = processBundesliga(req)
    elif action == 'echo':
        res = processEcho(req)
    else:
        res = {
            'speech': "Ich kann dazu nichts sagen.",
            'displayText': "Ich kann dazu nichts sagen.",
            'source': 'Elfenbeinturm'
        }

    res = json.dumps(res, indent=4)
    print(res)

    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processEcho(req):
    return {
        'speech': req.get('result').get('resolvedQuery'),
        'displayText': req.get('result').get('resolvedQuery'),
        'source': 'Intertubes'
    }


def processChuckNorris(req):
    n = "1"
    if req.get('result').get('parameters').get('number'):
        n = req.get('result').get('parameters').get('number')

    url = 'http://api.icndb.com/jokes/random/' + n
    if req.get('result').get('parameters').get('name'):
        url += "?firstName=%s&lastName=" % req.get('result').get('parameters').get('name')

    r = requests.get(url)
    res = {
        'speech': "Mir fällt gerade keiner ein, sorry.",
        'displayText': "Mir fällt gerade keiner ein, sorry.",
        'source': 'icndb.com'
    }

    if r.status_code == 200 and r.json()['type'] == 'success':
        print(r.json())
        res['speech'] = u" ".join(map(lambda x: x['joke'], r.json()['value']))
        res['displayText'] = res['speech']

    return res


def processBundesliga(req):
    url = 'http://football-data.org/v1/soccerseasons/430/leagueTable'

    r = requests.get(url)
    if r.status_code != 200:
        return {
            'speech': "Do hob ih grad koan Zuagriff.",
            'displayText': "Da habe ich gerade keinen Zugriff.",
            'source': 'footbal-data.org'
        }

    tab = r.json()

    # .leagueCaption
    # .matchday
    # .standing[]{.teamName, .points}

    tabellenfuehrer = req.get('result').get('parameters').get('tabellenfuehrer')
    absteiger = req.get('result').get('parameters').get('absteiger')
    number = req.get('result').get('parameters').get('number')

    text = 'Koan Blahn.'
    if tabellenfuehrer and not number:
        text = u"Am %d. Spieltag führt %s die Tabelle mit %d Punkten an" % \
            (tab['matchday'], tab['standing'][0]['teamName'], tab['standing'][0]['points'])
    elif absteiger and not number:
        text = u"Am %d. Spieltag ist %s das Schlusslicht mit %d Punkten" % \
            (tab['matchday'], tab['standing'][-1]['teamName'], tab['standing'][-1]['points'])
    elif number:
        if absteiger:
            li = tab['standing'][-int(number):]
        else:
            li = tab['standing'][:int(number)]
        text = reduce(lambda a, i: u"%s %s mit %d Punkten, " % (a, i['teamName'], i['points']), li, u"")

    return {
        'speech': text,
        'displayText': text,
        'source': 'football-data.org'
    }


def processMenueAuskunft(req):
    date = req.get('result').get('parameters').get('date')
    today = datetime.date.today().isoformat()

    start = u'Heid gibts '

    if date:
        print("Using specified date " + date + " instead of " + today)
        if date < today:
            start = u'Do gobs '
        elif date > today:
            start = u'Do gibts '
        url = "http://openmensa.org/api/v2/canteens/229/days/%s/meals" % date
    else:
        url = "http://openmensa.org/api/v2/canteens/229/days/%s/meals" % today

    print("Requesting menu from " + url)

    r = requests.get(url)

    # dummy response
    res = {
        'speech': u"Da bin ich überfragt.",
        'displayText': u"Da bin ich überfragt",
        'source': 'openmensa.org'
    }

    if r.status_code == 200:
        print(r.json())
        if req.get('result').get('parameters').get('vegetarisch'):
            gerichte = filter(lambda x: any(w in x['name'].lower() for w in [u'chicken', u'hähnchen', u'hühnchen', u'huhn']) or u'mit Fleisch' not in x['notes'], r.json())
        else:
            gerichte = r.json()
        res['speech'] = start + u", ".join(map(lambda x: x['name'], gerichte[:3]))
        res['displayText'] = res['speech']
    elif r.status_code == 404:
        res['speech'] = u"Des is koa Mensadog, Frischling!"
        res['displayText'] = res['speech']

    return res


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')
