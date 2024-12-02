import os
import json

from dotenv import load_dotenv

from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives import serialization


def jwk_to_pem(jwk_dict):
    """
    Convert a JWK dictionary to a PEM format string.
    
    Args:
        jwk_dict (dict): JWK key as a dictionary
        
    Returns:
        str: The key in PEM format
    
    Example jwk_dict format:
    {
        "kty": "RSA",
        "n": "base64_modulus",
        "e": "base64_exponent",
        "kid": "key_id",
        ...
    }
    """
    # Convert JWK to a cryptography key object
    private_key = RSAAlgorithm.from_jwk(jwk_dict)
    
    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Convert bytes to string and return
    return pem_bytes.decode('utf-8')


def load_jwk(path):
    with open(path, 'r') as f:
        jwk = json.load(f)
    return jwk


load_dotenv()
jwk_key_path = os.getenv('JWK_KEY_PATH')
print(jwk_to_pem(load_jwk(jwk_key_path)))
