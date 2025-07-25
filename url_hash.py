
import hashlib
import base64

def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    #print(hash_object)
    #print(short_hash)

generate_short_url("https: //www.youtube.com/playlist?list=PLLa_h7BriLH3UiuaiIxJu7gK_h1WDdIHv")
