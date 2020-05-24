import datetime
import os
import sys

import requests
from dotenv import load_dotenv

from flask import Flask
from flask_cors import CORS
from flask_restx import Api, Resource, reqparse
from flaskext.mysql import MySQL

load_dotenv()

app = Flask(__name__)
CORS(app)
api = Api(app)

app.config['MYSQL_DATABASE_HOST'] = os.getenv('DATABASE_HOST')
app.config['MYSQL_DATABASE_USER'] = os.getenv('DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('DATABASE_DB')
app.config['CORS_HEADERS'] = 'Content-Type'

mysql = MySQL()
mysql.init_app(app)

data_riferimento = datetime.datetime(2019, 12, 1)
arcgis_url = 'https://geocode.arcgis.com/arcgis/rest/services/'
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')


def arcgis_generate_token():
    url = 'https://www.arcgis.com/sharing/rest/oauth2/token'
    payload = 'client_id=' + client_id + '&client_secret=' + client_secret + '&grant_type=client_credentials'
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "application/json",
        'Cache-Control': "no-cache"
    }

    response = requests.request('post', url, data=payload, headers=headers)

    return response


def arcgis_request(method, endpoint, payload='', headers=None):
    token = arcgis_generate_token()
    if token.status_code == 200:
        token = token.json()
        if 'error' not in token:
            token = token['access_token']
        else:
            return None
    else:
        return None

    if headers is None:
        headers = {}

    method = str.lower(method)
    url = arcgis_url + endpoint
    base_headers = {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer ' + token
    }

    for header, value in base_headers.items():
        headers[header] = value

    if method == 'get':
        payload = ''

    response = requests.request(method, url, data=payload, headers=headers)

    if response.status_code == 200:
        if 'error' not in response.json():
            return response
        else:
            return None
    else:
        return None


def arcgis_find_address(address):
    response = arcgis_request('get', 'World/GeocodeServer/findAddressCandidates?f=json&singleLine=' +
                              address + '&outFields=Match_addr,Addr_type')

    if response is None or response.status_code != 200:
        return None
    else:
        return response


# Funzione che crea un Array di indirizzi dal file "indirizzi.txt"
def lista_indirizzi():
    righe = []
    f = open("indirizzi.txt", "r", encoding="utf-8")
    if f.mode == 'r':
        f = f.read()
        lines = f.splitlines()
        for line in lines:
            righe.append(line)
    return righe


# Funzione che controlla e restituisce una data valida o un none
def date_from_datestring(date_string, date_format='%Y-%m-%d %H:%M:%S'):
    try:
        return datetime.datetime.strptime(date_string, date_format)
    except ValueError:
        return None


def fields(cursor):
    """ Dato un oggetto cursore DB API 2.0 che è stato eseguito, restituisce
        un dizionario che associa ciascun nome di campo a un indice di colonna; 0 e fino. """
    results = {}
    column = 0
    for d in cursor.description:
        results[d[0]] = column
        column = column + 1

    return results


@api.route('/v1/segnalazioni')
class Segnalazioni(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('Indirizzo')
        parser.add_argument('Civico')
        parser.add_argument('NomeLocale')
        parser.add_argument('DataInizio')
        parser.add_argument('DataFine')
        args = parser.parse_args()

        if args is None:
            return {}, 400

        civico = (args.get('Civico') or '').strip()
        indirizzo = (args.get('Indirizzo') or '').strip()

        # Controllo l'inserimento dell'indirizzo
        if indirizzo == '' or indirizzo not in lista_indirizzi():
            return {'error': 'Indirizzo non valido'}, 400

        indirizzo = "%" + (indirizzo + " " + civico).strip() + "%"
        nome_locale = "%" + (args.get('NomeLocale') or '').strip() + "%"
        data_inizio_inserita = (args.get('DataInizio') or '').strip()
        data_fine_inserita = (args.get('DataFine') or '').strip()

        oggetto_data_inizio = date_from_datestring(data_inizio_inserita)
        oggetto_data_fine = date_from_datestring(data_fine_inserita)

        # Controllo per l'inserimento della data
        if (oggetto_data_fine is None or oggetto_data_inizio is None) or (oggetto_data_fine <= oggetto_data_inizio):
            return {'error': 'Date invalide'}, 400

        cur = mysql.get_db().cursor()
        cur.execute('SELECT * FROM luogo WHERE Indirizzo LIKE %s AND NomeLocale LIKE %s '
                    'AND ((DataFine BETWEEN %s AND %s) '
                    'OR (DataInizio BETWEEN %s AND %s))', (indirizzo, nome_locale,
                                                           data_inizio_inserita,
                                                           data_fine_inserita,
                                                           data_inizio_inserita, data_fine_inserita))
        righe = cur.fetchall()
        colonne = fields(cur)
        cur.close()
        risultato = []

        for riga in righe:
            oggetto = {}
            oggetto["Indirizzo"] = riga[colonne["Indirizzo"]]
            oggetto["NomeLocale"] = riga[colonne["NomeLocale"]]
            oggetto["DataInizio"] = riga[colonne["DataInizio"]].strftime('%Y-%m-%d %H:%M:%S')
            oggetto["DataFine"] = riga[colonne["DataFine"]].strftime('%Y-%m-%d %H:%M:%S')
            risultato.append(oggetto)

        return risultato, 200 if len(risultato) > 0 else 204

    def post(self):
        data_oggi = datetime.datetime.now()
        payload = api.payload
        civico = (payload.get('Civico') or '').strip()
        indirizzo = (payload.get('Indirizzo') or '').strip()

        # Controllo l'inserimento dell'indirizzo
        if indirizzo == '' or indirizzo not in lista_indirizzi():
            return {'error': 'Indirizzo non valido'}, 400

        indirizzo = ((payload.get('Indirizzo') or '').strip() + civico).strip()

        response = arcgis_find_address('Napoli, ' + indirizzo)
        if response is None:
            return {'error': 'Errore api geocoding'}, 502

        candidates = response.json().get('candidates') or []
        if len(candidates) == 0:
            return {'error': 'Indirizzo non valido'}, 400

        lon = candidates[0]['location']['x']
        lat = candidates[0]['location']['y']

        nome_locale = (payload.get('NomeLocale') or '').strip()
        data_inizio_inserita = (payload.get('DataInizio') or '').strip()
        data_fine_inserita = (payload.get('DataFine') or '').strip()

        oggetto_data_inizio = date_from_datestring(data_inizio_inserita)
        oggetto_data_fine = date_from_datestring(data_fine_inserita)

        # Controllo per l'inserimento della data
        if (oggetto_data_fine is None or oggetto_data_inizio is None) or (oggetto_data_fine <= oggetto_data_inizio)\
                or (oggetto_data_inizio <= data_riferimento) or (oggetto_data_fine <= data_riferimento)\
                or (oggetto_data_fine > data_oggi) or (oggetto_data_inizio > data_oggi):
            return {'error': 'Date invalide'}, 400

        cur = mysql.get_db().cursor()
        cur.execute('INSERT INTO luogo (Indirizzo, NomeLocale, DataInizio, DataFine, Lon, Lat) '
                    'VALUES (%s, %s, %s, %s, %s, %s)', (indirizzo, nome_locale, data_inizio_inserita,
                                                        data_fine_inserita, lon, lat))
        mysql.get_db().commit()
        cur.close()
        return {"Indirizzo": indirizzo, "NomeLocale": nome_locale, "DataInizio": data_inizio_inserita,
                "DataFine": data_fine_inserita}, 200


@api.route('/v1/indirizzi')
class Segnalazioni(Resource):
    def get(self):
        indirizzi = lista_indirizzi()
        return indirizzi, 200 if len(indirizzi) > 0 else 204


if __name__ == '__main__':
    app.run(debug=True)
