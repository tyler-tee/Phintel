import datetime
import requests
import pandas as pd
from io import StringIO
from config import *

phishtank_baseapi = "https://checkurl.phishtank.com/checkurl/"
phishtank_db_url = f"http://data.phishtank.com/data/{phishtank_api_key}/online-valid.csv"
phish_init_url = "https://phishing-initiative.lu/api/"


def openphish_update():  # Updated every 12 hours
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    response = requests.get("https://openphish.com/feed.txt")

    if response.status_code == 200:
        openphish_feed = response.text.split('\n')

        df_openphish = pd.DataFrame(columns=['URL', 'Source'])
        df_openphish['URL'] = openphish_feed
        df_openphish['Source'] = 'openphish'
        df_openphish['Date'] = timestamp
        df_openphish['Notes'] = 'Free Dataset'
        df_openphish['Target'] = 'Other'
        df_openphish['IP'] = 'N/A'

        return df_openphish


def phishstats_update():  # Updated every 1.5 hours
    response = requests.get("https://phishstats.info/phish_score.csv")

    if response.status_code == 200:
        data = StringIO(response.content.decode("utf-8"))
        df_phishstats = pd.read_csv(data, skiprows=9)
        df_phishstats.columns = ["Date", "Notes", "URL", "IP"]
        df_phishstats = df_phishstats[~df_phishstats['Date'].str.contains(',')]
        df_phishstats['Notes'] = 'Score: ' + df_phishstats['Notes'].astype(str)
        df_phishstats['Source'] = 'phishstats'
        df_phishstats['Target'] = 'Other'

        return df_phishstats


def phishtank_update():  # Updated every 1 hour
    phishtank_cols = ['url', 'phish_detail_url', 'submission_time', 'target']

    df_phishtank = pd.read_csv(phishtank_db_url, usecols=phishtank_cols)

    df_phishtank.rename(columns={"url": "URL", "phish_detail_url": "Notes",
                                 "submission_time": "Date", "target": "Target"},
                        inplace=True)
    df_phishtank['Source'] = 'phishtank'

    return df_phishtank


def primary_db_update():
    df_openphish = openphish_update()
    df_phishstats = phishstats_update()
    df_phishtank = phishtank_update()

    df_primary = df_openphish.append(df_phishstats)
    df_primary = df_primary.append(df_phishtank)

    df_primary['URL'].drop_duplicates(inplace=True)
    df_primary['Date'] = pd.to_datetime(df_primary['Date'])

    df_primary.to_csv('primary.csv', index=False)

    return df_primary


def primary_db_search(search_term, column, dataframe):
    results = dataframe[dataframe[column].str.contains(search_term, na=False)]

    return results


def phishtank_query(phishing_url):
    payload = {
        "url": phishing_url,
        "format": "json",
        "app_key": phishtank_api_key
    }

    response = requests.post(phishtank_baseapi, data=payload)

    if response.status_code == 200:
        return response.json()
    else:
        print(response.headers)
        print(response.text)


def phish_init_check(phishing_url):
    headers = {
        "Authorization": f"Token {phish_init_api_key}"
    }

    response = requests.get(phish_init_url + "v1/urls/lookup", headers=headers,
                            params={"url": phishing_url})

    if response.status_code == 200:
        return response.json()
    else:
        print(response.headers)
        print(response.text)
