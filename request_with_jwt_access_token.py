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
    expiry_time_in_seconds = current_time_in_seconds + 60 * 10 # 10 minuten, langer mag het JWT token niet gebruikt worden
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
    private_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk) # alternatief: de PEM private key string.
    signed_jwt = jwt.encode(claims, private_key, algorithm="RS256", headers=header)
    return signed_jwt


def get_access_token(client_id, jwt_token, auth_token_url): 
    access_token_data = {
        "grant_type": "client_credentials", 
        "client_id": client_id, 
        "client_assertion": jwt_token,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer", 
        "scope": "awv_toep_services" # alternatief: "vo_info" voor een key op de PUB omgeving
    }
    
    r = requests.post(
        url=auth_token_url, 
        data=access_token_data, 
        headers={
            "content-type":"application/x-www-form-urlencoded"
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
print()
print("Signed JWT:")
print(signed_jwt)

access_token_json = get_access_token(client_id, signed_jwt, auth_token_url)
print()
print(f"Access token: {access_token_json['access_token']}, geldig voor {access_token_json['expires_in'] // 60} minuten")

# OPGELET: de PROD URL is helemaal anders dan de DEV en TEI URLs (wegenenverkeer.be versus mow.vlaanderen.be)!
# url = "https://api.wegenenverkeer.vlaanderen.be/weglocaties/weg/N0080001/lijnlocaties"
# url = "https://api.apps-tei.mow.vlaanderen.be/weglocaties/weg/N0080001/lijnlocaties"
url = "https://api.apps-dev.mow.vlaanderen.be/weglocaties/weg/N0080001/lijnlocaties"

headers = {
        'Authorization': f'Bearer {access_token_json['access_token']}',
    }

response = requests.get(url, headers=headers)
print()
print(f"Call with bearer response status {response.status_code}")
print("Content:")
print(f"{response.text[0:100]} ...")
print()
