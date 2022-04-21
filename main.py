import sys
import csv
import json
import math
import requests
import pandas as pd 
from arrapi import RadarrAPI

def get_those_movies():
    # Change these parameters to suit your needs
    yts_query_parameters = {
        # Set up your parameters:   # (default value) [valid values] description of parameter
        'limit': 50,                # (20) [1-50] How many results to return per page
                                        ## Try lowering this if you keep getting errors
        'quality': '1080p',         # (All) [720p, 1080p, 2160p, 3D, All] Filter by a given quality
        'minimum_rating': 8,        # (0) [0-9] Filter movies by a given minimum IMDb rating (inclusive)
        'query_term': '',           # (0) [valid string] Movie search, matching on: Movie Title/IMDb Code, 
                                        ## Actor Name/IMDb Code, Director Name/IMDb Code
        'genre': '',                # (All) [valid string] Filter by a given genre 
                                        ## (See http://www.imdb.com/genre/ for full list)
        'sort_by': 'year',          # (date_added) [title, year, rating, peers, seeds, download_count, 
                                        ## like_count, date_added] Sorts the results by choosen value
        'order_by': 'desc',         # (desc) [desc, asc] Orders results by either Ascending or Descending order
        'with_rt_ratings': 'false', # (false) [true, false] Returns the list with the Rotten Tomatoes rating included  
    }
    # These trackers will get appended to the magnet_url that ends up in the DataFrame and CSV output
    # NOTE: The ones shown here are listed in the official YTS API docs as examples, but I'm pretty sure most 
    # (or all) of them no longer work. These are only important if you plan to manually add magnets to your 
    # torrent client from the CSV output instead of letting Radarr do the searching.
    # example: 'udp://sometracker.url:80/announce'
    open_tracker_announce_urls=[
        'udp://open.demonii.com:1337/announce',
        'udp://tracker.openbittorrent.com:80',
        'udp://tracker.coppersurfer.tk:6969',
        'udp://glotorrents.pw:6969/announce',
        'udp://tracker.opentrackr.org:1337/announce',
        'udp://torrent.gresille.org:80/announce',
        'udp://p4p.arenabg.com:1337',
        'udp://tracker.leechers-paradise.org:6969',
        'udp://tracker.internetwarriors.net:1337',
        'udp://p4p.arenabg.ch:1337'
    ]
    # Various settings
    only_english = True     # Only return movies that are primarily in English? 
                                ## NOTE: The YTS API doesn't actually support filtering on this value, so it will still
                                ## initially need to return all language results. The script will filter the list after 
                                ## it's done with the YTS API and before outputting a CSV or adding movies to Radarr
    output_csv = True       # Do you want to output a CSV with all the juicy details from the YTS API?
    radarr_autoadd = True   # Do you want the script to automatically add all found movies
                                ## to Radarr using the radarr_api_parameters specified below?
    # Change these parameters for your Radarr instance/preferences
    radarr_api_parameters = {
        'url': 'http://192.168.10.2:7878',      # Protocol, IP/hostname, and port used to access Radarr
        'api_key': 'REDACTED',                  # Copy directly from Radarr 
                                                    ## Settings > General > Security > API Key
        'root_folder': '/data/media/Movies',    # Must match Path exactly as shown in Radarr
                                                    ## Settings > Media Management > Root Folders > Path
        'quality_profile': 'HD-1080p YTS',      # Must match Name of a Quality Profile in Radarr
                                                    ## Settings > Profiles > Quality Profiles
        'monitor':True,                         # True/False, add movie in Monitored state
        'search':True,                          # True/False, auto-search for movie on add
        'tags':['yts-api2']                      # OPTIONAL - list of tags to add to the movie
                                                    ## Set to '' for no tags
    }
    
    
    
###############################################
### You shouldn't need to modify below here ###
###############################################
    # Do ALL the things
    df_yts = ytsapi(yts_query_parameters)
    df_yts = yts_cleandata(df_yts, open_tracker_announce_urls, yts_query_parameters['quality'], only_english)
    if output_csv: 
        try:
            df_yts.to_csv("yts_movies.csv", index=False)
            print("  Successfully wrote yts_movies.csv")
        except:
            print("  Either yts_movies.csv or the directory is write-protected. No CSV output this time!")
    if radarr_autoadd:
        radarrapi_autoadd(df_yts, radarr_api_parameters)


def ytsapi(yts_query_params):
    yts_api_url = "https://yts.mx/api/v2/list_movies.json"
    
    df = pd.DataFrame()

    pages = ytsapi_getpage(yts_api_url, yts_query_params, mode='pages')

    # pages = 3   # when debugging, you probably don't want to pull every page.
    print("\n  Grabbing " + str(pages) + " pages worth of results. This may take some time...")
    for page in range(pages):
        page += 1
        # print("Grabbing page " + str(page) + "...") # might come in handy when debugging
        if page % 10 == 0:
            # Rudimentary progress display ༼ つ ◕_◕ ༽つ
            print("  Grabbing page " + str(page) + "/" + str(pages) + "... (~" + str(math.ceil(((page-1)/pages)*100)) + "% complete)")
        pagedata = ytsapi_getpage(yts_api_url, yts_query_params, page=page).json()['data']
        df = pd.concat([df, pd.DataFrame(pagedata['movies'])], axis=0)      
    return df

def ytsapi_getpage(url, query_params, page=1, mode='data'):
    query_params['page'] = page
    try:
        response = requests.get(url, params=query_params, timeout=60.0)
        response.raise_for_status()
        if mode == 'pages':
            movie_count = response.json()['data']['movie_count']
            page_count = int(math.ceil(response.json()['data']['movie_count']/response.json()['data']['limit']))
            print("  Found " + str(movie_count) + " movies that match query parameters. (" + str(page_count) + " pages)")
            input("  Press ENTER to continue with pulling data.")
            return page_count
        else:
            return response
    except requests.exceptions.HTTPError as errh:
        print(errh)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
    except requests.exceptions.Timeout as errt:
        print(errt)
    except requests.exceptions.RequestException as err:
        print(err)
    print("  Please check your query parameters or wait a little while and try again.")
    
def yts_cleandata(df, announce_urls, quality, only_english):
    print("\n  Cleaning up the data. Please wait...")
    magnet_announce_string = ""
    for url in announce_urls:
        magnet_announce_string += "&tr=" + url
        
    # Drop duplicate YTS movie ids, if they exist
    df.drop_duplicates(['id'], keep='first', ignore_index=True, inplace=True)
    # Drop unnecessary movies columns
    df.drop(columns=['summary','description_full','background_image','background_image_original',
                            'small_cover_image','medium_cover_image','large_cover_image'], inplace=True)
    if only_english:
        # Just saving this list here for potential future changes. All languages found via the YTS API:
        # af, ak, am, ar, be, bn, bo, bs, ca, cn, cs, cy, da, de, el, en, es, et, eu, fa, fi, fr, ga, gl, 
        # he, hi, ht, hu, hy, id, is, it, ja, ka, kk, km, kn, ko, ku, ky, la, lg, lt, lv, mk, ml, mn, mr, 
        # ms, mt, nb, nl, no, os, pa, pl, ps, pt, ro, ru, sh, sk, sl, so, sr, st, sv, sw, ta, te, th, tl, 
        # tr, uk, ur, vi, wo, xx, yi, zh, zu
        df = df[(df['language'] == 'en') | (df['language'] == 'uk')]

    # Break out torrent data
    df_torrents = df.explode('torrents').reset_index(drop=True)[['id', 'torrents']]
    df_torrents['torrent.url'] = df_torrents.torrents.apply(lambda x: x['url'])
    df_torrents['torrent.hash'] = df_torrents.torrents.apply(lambda x: x['hash'])
    df_torrents['torrent.quality'] = df_torrents.torrents.apply(lambda x: x['quality'])
    df_torrents['torrent.type'] = df_torrents.torrents.apply(lambda x: x['type'])
    df_torrents['torrent.seeds'] = df_torrents.torrents.apply(lambda x: x['seeds'])
    df_torrents['torrent.peers'] = df_torrents.torrents.apply(lambda x: x['peers'])
    df_torrents['torrent.size'] = df_torrents.torrents.apply(lambda x: x['size'])
    # df_torrents['torrent.size_bytes'] = df_torrents.torrents.apply(lambda x: x['size_bytes'])
    df_torrents['torrent.date_uploaded'] = df_torrents.torrents.apply(lambda x: x['date_uploaded'])
    df_torrents['torrent.date_uploaded_unix'] = df_torrents.torrents.apply(lambda x: x['date_uploaded_unix'])

    # Drop duplicate torrent hashes, if they exist
    df_torrents.drop_duplicates(['torrent.hash'], keep='first', ignore_index=True, inplace=True)
    # Filter down to selected quality
    if quality.lower() != 'all':
        df_torrents = df_torrents[df_torrents['torrent.quality'] == quality.lower()]
    # Concatenate quality
    df_torrents['torrent.full_quality'] = df_torrents['torrent.quality'].astype(str).str.upper() + "-" + df_torrents['torrent.type'].astype(str).str.upper()
    # Drop extra torrent columns
    df_torrents.drop(columns=['torrents','torrent.quality','torrent.type'], inplace=True)
    # Merge the torrent data back into the main dataframe
    df = df.merge(df_torrents, how='left', on='id', validate='one_to_many')
    df.drop(columns=['torrents'], inplace=True)
    df['torrent.magnet_url'] = "magnet:?xt=urn:btih:" + df['torrent.hash'] + "&dn=" + df['slug'] + magnet_announce_string
    return df

def radarrapi_autoadd(df, radarr_params):
    # old code for adding movies one-at-a-time
    # radarr = RadarrAPI(radarr_params['url'], radarr_params['api_key'])
    # for imdb_id in df['imdb_code'].unique():
    #     search = radarr.search_movies("imdb:" + imdb_id)
    #     if search:
    #         print("\nADDING MOVIE: " + str(search[0]))
    #         try:
    #             search[0].add(root_folder=radarr_params['root_folder'], quality_profile=radarr_params['quality_profile'], monitor=radarr_params['monitor'], search=radarr_params['search'], tags=radarr_params['tags'])
    #             print("SUCCESS!")
    #         except Exception as e:
    #             print(e)
    imdb_ids = df['imdb_code'].unique().tolist()
    try: 
        radarr = RadarrAPI(radarr_params['url'], radarr_params['api_key'])
    except Exception as e:
        sys.exit(e)
    print("  Trying to add " + str(len(imdb_ids)) + " movies to Radarr...")
    if str(len(imdb_ids)) > 50: print("  Please be patient. This may take awhile...")
    try:
        add_movies_results = radarr.add_multiple_movies(ids=imdb_ids, root_folder=radarr_params['root_folder'], quality_profile=radarr_params['quality_profile'], monitor=radarr_params['monitor'], search=radarr_params['search'], tags=radarr_params['tags'])
        print('''
  Completed successfully!
  Added ''' + str(len(add_movies_results[0])) + ''' new movies to Radarr
  ''' + str(len(add_movies_results[1])) + ''' movies were already in Radarr
  ''' + str(len(add_movies_results[2])) + ''' movies could not be found or were excluded.''')
    except Exception as e:
        sys.exit(e)

if __name__ == "__main__":
    get_those_movies()
