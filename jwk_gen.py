# Zie: https://authenticatie.vlaanderen.be/docs/beveiligen-van-toepassingen/integratie-methoden/oidc/technische-info/client-authenticatie/#voorbeeld-van-een-publieke-sleutel-jwk-zoals-te-bezorgen-aan-het-integratieteam

from jwcrypto.jwk import JWK

key = JWK.generate(kty='RSA', alg='RS256', size=4096)
public_key = key.export_public()
private_key = key.export_private()

print("")
print("Public json web key te bezorgen aan het integratieteam:")
print(public_key)

print("")
print("Private json web key op een veilige plaats bewaren:")
print(private_key)
