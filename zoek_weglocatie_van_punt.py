import math
import os
import time
import json
import jwt
import jwt.algorithms
import uuid
import requests
from dotenv import load_dotenv

# variabelen uitlezen uit het .env bestand (CLIENT_ID en JWK_KEY_PATH)
load_dotenv()

# de client ID die je in het beheerportaal ontvangt na goedkeuring van de OAuth toegang
client_id = os.getenv('CLIENT_ID')
# path naar het JSON bestand waar de JWK key staat
jwk_key_path = os.getenv('JWK_KEY_PATH')
# URL waar je een access token aanvraagt met een secret (signed JWT token)
auth_token_url = "https://authenticatie.vlaanderen.be/op/v1/token"

print()
print(f"Client ID: {client_id}")
print()


def signed_jwt(client_id, jwk):
    current_time_in_seconds = round(time.time())
    expiry_time_in_seconds = current_time_in_seconds + 60 * 8  # < 10 minuten, langer mag het JWT token niet gebruikt worden
    header = {
        'alg': 'RS256',
        'typ': 'JWT'
    }
    claims = {
        "iat": current_time_in_seconds,
        "exp": expiry_time_in_seconds,
        "iss": client_id,
        "sub": client_id,
        "aud": "https://authenticatie.vlaanderen.be/op",
        "jti": str(uuid.uuid4()),
    }
    private_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)  # alternatief: de PEM private key string.
    signed_jwt = jwt.encode(claims, private_key, algorithm="RS256", headers=header)
    return signed_jwt


def get_access_token(client_id, jwt_token, auth_token_url):
    access_token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_assertion": jwt_token,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "scope": "awv_toep_services"
    }

    r = requests.post(
        url=auth_token_url,
        data=access_token_data,
        headers={
            "content-type": "application/x-www-form-urlencoded"
        }
    )
    access_token_json = r.json()
    print()
    print("Access token JSON response:")
    print(access_token_json)
    return access_token_json


def load_jwk(path):
    with open(path, 'r') as f:
        jwk = json.load(f)
    return jwk

signed_jwt = signed_jwt(client_id, load_jwk(jwk_key_path));
access_token_json = get_access_token(client_id, signed_jwt, auth_token_url)

def print_weg_locatie(result):
    input = result['geometry']['coordinates']
    if 'relatief' not in result:
        print("Punt ligt niet in de buurt van een genummerde weg")
        return

    wegnummer = result['relatief']['wegnummer']['nummer']

    ref_pnt = result['relatief']['referentiepunt']['opschrift']
    afstand_van_refpunt = result['relatief']['afstand']

    punt_op_weg = result['projectie']['coordinates']

    afstand = math.hypot(punt_op_weg[0] - input[0], punt_op_weg[1] - input[1])
    print(f'Punt ligt langs {wegnummer} ter hoogte van hm-paal {ref_pnt} km +{afstand_van_refpunt}m (afstand tot input punt = {afstand}m.)')


def to_geojson(x, y):
    # default CRS in Lambert 72
    return {
        "type": "Point",
        "geometry": {
            "type": "Point",
            "coordinates": [x, y]
        }
    }


def gereference_batch(punten, zoekafstend=20):
    url="https://api.wegenenverkeer.vlaanderen.be/weglocaties/puntlocatie/batch"
    headers = {
        'Authorization': f'Bearer {access_token_json['access_token']}',
        'Accept': 'application/json'
    }
    data = [to_geojson(x, y) for x, y in punten]
    response = requests.post(url, json=data, headers=headers, params={"zoekafstand": zoekafstend, "wegType": "Genummerd"})
    if response.status_code != 200:
        print("Error:")
        print(response.text)
        return
    for res in response.json():
        if 'success' in res:
            print_weg_locatie(res['success'])
        elif 'failure' in res:
            print(f"Failure: {res['failure']['message']}")
        else:
            print(f'feedback: {res['feedback']['message']}')



def georeference(x, y, zoekafstand=20, enkel_genummerde_wegen=True):
    # Zie OpenAPI spec voor '/puntlocatie/via/xy' endpoint
    url = "https://api.wegenenverkeer.vlaanderen.be/weglocaties/puntlocatie/via/xy"
    headers = {
        'Authorization': f'Bearer {access_token_json['access_token']}',
        'Accept': 'application/json'
    }


    weg_type = "Genummerd" if enkel_genummerde_wegen else None
    params = {
        "x": x,
        "y": y,
        "zoekafstand": zoekafstand,
        "wegType": weg_type
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print("Error:")
        print(response.text)
        return
    print_weg_locatie(response.json())

    # De OpenAPI Spec is hier wat misleidend. Het resultaat is eigenlij een WegsegmentPuntLocatie object (zie OpenAPI Schemas).


if __name__ == "__main__":
    print(f"Success case: punt ligt in de buurt van een genummerde weg")
    georeference(153180, 207072)
    print()
    print()
    print(f"Failure case: punt ligt niet in de buurt van een genummerde weg")
    georeference(158547.32, 228905.38)
    print()
    print()
    print('Nu in batch:')
    gereference_batch([(153180, 207072), (158547.32, 228905.38)])