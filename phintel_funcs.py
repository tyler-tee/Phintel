import requests
from config import *

phishtank_api_key = phishtank_api_key
phishtank_baseapi = "http://checkurl.phishtank.com/checkurl/"
phishtank_db_url = f"http://data.phishtank.com/data/{phishtank_api_key}/online-valid.json.bz2"

phishtank_headers = {
    "User-Agent": "phishtank/phintel"
}


def phishtank_query(phishing_url):
    params = {
        "url": phishing_url,
        "format": "json",
        "app_key": phishtank_api_key
    }

    response = requests.post(phishtank_baseapi, headers=phishtank_headers,
                             params=params)

    if response.status_code == 200:
        if 'You must supply' not in response.text:
            return response

    return response
