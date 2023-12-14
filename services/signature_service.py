import json
from base64 import b64decode, b64encode

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from configs.config import settings


class SignatureService:
    def sign_payload(self, payload):
        key = RSA.importKey(str.encode('-----BEGIN PRIVATE KEY-----\n'+
                                       settings.WF_SIGN_PRIVATE_KEY+'\n-----END PRIVATE KEY-----'))
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        digest.update(json.dumps(payload).encode('utf-8'))
        return b64encode(signer.sign(digest)).decode("utf-8")

    def verify_signature_response(self, msg, signature, client_public_key):
        key = RSA.importKey(str.encode('-----BEGIN PUBLIC KEY-----\n'+client_public_key+'\n-----END PUBLIC KEY-----'))

        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new(json.dumps(msg).encode('utf-8'))

        try:
            return signer.verify(digest, b64decode(signature))
        except:
            return False

    def verify_signature_request(self, msg, signature, client_public_key):
        key = RSA.importKey(str.encode('-----BEGIN PUBLIC KEY-----\n'+client_public_key+'\n-----END PUBLIC KEY-----'))

        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new(json.dumps(msg).encode('utf-8'))

        try:
            return signer.verify(digest, b64decode(signature))
        except:
            return False
