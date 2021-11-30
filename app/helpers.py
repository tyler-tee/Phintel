import datetime
from io import StringIO
import pandas as pd
import requests
import sqlite3
from urllib.parse import urlparse
from config import config


def domain_parser(url):
    t = urlparse(str(url))
    parsed = '.'.join(t.netloc.split('.')[-2:])

    if parsed == 'com':
        return t
    else:
        return parsed


##### Database Functions #####


def openphish_update() -> pd.DataFrame:  # Updated every 12 hours
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    response = requests.get("https://openphish.com/feed.txt")

    if response.status_code == 200:
        openphish_feed = response.text.split('\n')

        df_openphish = pd.DataFrame(columns=['URL', 'Source'])

        df_openphish['URL'] = openphish_feed
        df_openphish = df_openphish.drop_duplicates(subset='URL', keep='first')
        df_openphish['URL'] = df_openphish['URL'].str.lower()

        df_openphish['Source'] = 'openphish'
        df_openphish['Date'] = timestamp
        df_openphish['Notes'] = 'Free Dataset'
        df_openphish['Target'] = 'Other'

        return df_openphish


def phishstats_update() -> pd.DataFrame:  # Updated every 1.5 hours
    # We're doing this with requests to handle our headers - PhishStats is sensitive
    response = requests.get("https://phishstats.info/phish_score.csv")
    phishstats_cols = ['Date', 'Notes', 'URL', 'IP']

    if response.status_code == 200:
        try:
            data = StringIO(response.content.decode("utf-8"))
            df_phishstats = pd.read_csv(data, skiprows=9)
        except Exception as e:
            print(e)
            df_phishstats = pd.DataFrame(columns=phishstats_cols, data=None)

        df_phishstats.columns = phishstats_cols
        df_phishstats.drop(columns=['IP'], inplace=True)

        df_phishstats['URL'] = df_phishstats['URL'].str.lower()
        df_phishstats = df_phishstats.drop_duplicates(subset='URL', keep='first')  # Remove duplicate URL's
        df_phishstats = df_phishstats[~df_phishstats['Date'].str.contains(',')]  # Remove anomalies

        # Establish standardized columns
        df_phishstats['Notes'] = 'Score: ' + df_phishstats['Notes'].astype(str)
        df_phishstats['Source'] = 'phishstats'
        df_phishstats['Target'] = 'Other'

        return df_phishstats


def phishtank_update() -> pd.DataFrame:  # Updated every 1 hour
    phishtank_db_url = f"http://data.phishtank.com/data/{config['phishtank_api_key']}/online-valid.csv"
    phishtank_cols = ['url', 'phish_detail_url', 'submission_time', 'target']  # Expected columns

    try:
        df_phishtank = pd.read_csv(phishtank_db_url, usecols=phishtank_cols)  # Read csv into dataframe from url
    except Exception as e:
        print(e)
        df_phishtank = pd.DataFrame(columns=phishtank_cols, data=None)

    # Standardize our column names
    df_phishtank.rename(columns={"url": "URL", "phish_detail_url": "Notes",
                                 "submission_time": "Date", "target": "Target"},
                        inplace=True)

    df_phishtank['URL'] = df_phishtank['URL'].str.lower()
    df_phishtank = df_phishtank.drop_duplicates(keep='first', subset='URL')  # Get rid of duplicate URL's
    df_phishtank['Source'] = 'phishtank'  # Tag data with source

    return df_phishtank


def urlhaus_update() -> pd.DataFrame:  # Updated every 5 minutes
    try:
        df_haus = pd.read_csv('https://urlhaus.abuse.ch/downloads/csv/',
                              compression='zip', skiprows=8)

        df_haus.rename(columns={"url": "URL", "dateadded": "Date",
                                "threat": "Notes"}, inplace=True)
        df_haus['URL'] = df_haus['URL'].str.lower()
        df_haus = df_haus.drop_duplicates(keep='first', subset='URL')
        df_haus = df_haus[['URL', 'Date', 'Notes']]
        df_haus['Source'] = 'urlhaus'
        df_haus['Target'] = 'Other'

        return df_haus
        
    except Exception as e:
        print(e)


def primary_db_update() -> pd.DataFrame:
    # Gather our initial dataframes from all available sources
    df_openphish = openphish_update()
    df_phishstats = phishstats_update()
    df_phishtank = phishtank_update()
    df_haus = urlhaus_update()

    # Create primary dataframe from our component dataframes
    df_primary = pd.concat([df_openphish, df_phishstats, df_phishtank, df_haus])

    # Try and append dataframe based on established data - Move on if the file isn't available
    try:
        prev_primary = pd.read_csv('./data/primary.csv', on_bad_lines='skip')
        df_primary = df_primary.append(prev_primary)
    except FileNotFoundError:
        pass
    
    try:
        conn = sqlite3.connect('./data/primary.sqlite')
        primary_db = pd.read_sql('SELECT * FROM main', con=conn)
        df_primary = df_primary.append(primary_db)
    except Exception as e:
        print(e)

    
    df_primary['URL'] = df_primary['URL'].str.lower()  # Just to ensure consistency among our URL's
    df_primary = df_primary.drop_duplicates(subset='URL', keep='first')  # Filter out any duplicate URL's
    df_primary['Domain'] = df_primary['URL'].apply(lambda x: domain_parser(x)) # Parse domains from our URL's
    df_primary['Date'] = pd.to_datetime(df_primary['Date'])  # Make sure our date is in ISO 8601
    df_primary['Source'] = df_primary['Source'].str.lower()

    if not df_primary.empty:
        df_primary.to_csv('./data/primary.csv', index=False)  # Write primary dataframe to disk as a csv
        df_primary.to_sql('main', conn, if_exists='replace', index=False)

    return df_primary


def primary_db_aggregate(dataframe: pd.DataFrame, agg_value: str) -> pd.DataFrame:
    df_aggregate = dataframe.groupby(agg_value).agg({'URL': 'nunique'}).reset_index()  # Aggregate targets by attempts

    df_aggregate = df_aggregate.sort_values('URL', ascending=False)

    return df_aggregate


def primary_db_search(search_term: str, dataframe: pd.DataFrame,
                      search_type: str = 'exact', column: str = 'URL'):
    if search_type != 'exact':
        results = dataframe[dataframe[column].str.contains(search_term, na=False)]
    else:
        results = dataframe.loc[dataframe[column] == search_term]

    return not results.empty


##### OSINT Functions #####
def otx_domain_search(domain: str, section: str = 'general') -> dict:
    otx_headers = {'X-OTX-API-KEY': config['otx_key']}
    response = requests.get(f'https://otx.alienvault.com/api/v1/indicators/domain/{domain}/{section}',
                            headers=otx_headers)

    if response.status_code == 200 and 'endpoint not found' not in response.text:
        return response.json()


def otx_url_search(url: str, section: str = 'general') -> dict:
    otx_headers = {'X-OTX-API-KEY': config['otx_key']}
    response = requests.get(f'https://otx.alienvault.com/api/v1/indicators/url/{url}/{section}',
                            headers=otx_headers)

    if response.status_code == 200 and 'endpoint not found' not in response.text:
        return response.json()


def rawhttp_sub(url: str) -> str:
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; WOW64)"
                  "AppleWebKit/537.36 (KHTML, like Gecko)"
                  "Chrome/53.0.2785.143 Safari/537.36")

    payload = {'ua': user_agent,
               'url': url}

    endpoint = 'https://rawhttp.com/getimage'

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200 and 'errorMessage' not in response.text:
        return response.text
    

def urlscan_url_search(url: str) -> dict:
    if config['urlscan_key']:
        headers = {"API-Key": config['urlscan_key']}
    else:
        headers = {}
        
    if url.startswith('http'):
        url = url.replace('http://', '').replace('https://', '')
    
    url = url.replace('/', '\/')
    response = requests.get(f"https://urlscan.io/api/v1/search/?q=page.url:{url}", headers=headers)
    
    if response.status_code == 200:
        results = response.json()['results']
        if results:
            results = [i['result'] for i in results]
            return results
        else:
            return None
    else:
        print('URLScan.io Error:', response.status_code)


def vt_url_search(url: str) -> dict:
    pass
