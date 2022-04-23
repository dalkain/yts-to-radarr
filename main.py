import os
import sys
import csv
import json
import math
import requests
import pandas as pd 
from arrapi import RadarrAPI

def get_those_movies():

    ##### IMPORTANT #####
    # At least some of the configurations are case-sensitive, so please just assume they all are 
    # and follow the examples or what is displayed in the comments.

    # What portions to run:
    output_csv = True           # Do you want to output a CSV with all the juicy details from the YTS API?
    grab_torrent_files = True    # Download .torrent file for every result?
    export_magnet_list = True  # Export .txt file with just the generated magnet links  
    radarr_autoadd = True       # Do you want the script to automatically add all found movies
                                    ## to Radarr using the radarr_api_parameters specified below?

   
    yts_query_parameters = {
        # Set up your parameters:   # (default value) [valid values] description of parameter
        'limit': 50,                # (20) [1-50] How many results to return per page
                                        ## Try lowering this if you keep getting errors
        'quality': '1080p',         # (All) [720p, 1080p, 2160p, 3D, All] Filter by a given quality
        'minimum_rating': 8,        # (0) [0-9] Filter movies by a given minimum IMDb rating (inclusive)
        'query_term': '',           # (0) [valid string] Movie search, matching on: Movie Title/IMDb Code, 
                                        ## Actor Name/IMDb Code, Director Name/IMDb Code
                                        ## Seems very unreliable for anything but movie name/imdbid searching
        'genre': '',                # (All) [valid string] Filter by a given genre 
                                        ## (See http://www.imdb.com/genre/ for full list)
        'with_rt_ratings': 'false' # (false) [true, false] Returns the list with the Rotten Tomatoes ratings 
    }
    # Additional YTS filtering options not built into the YTS API. These filters will apply after communication 
    # with the YTS API is completed but before outputting any data.
    yts_earliest_year = 1950            # Set an earliest movie release year to filter the results 
                                            ## Use 4-digit year (e.g. 1950). Set to 0 to include everything
    yts_preferred_release = 'bluray'    # (bluray) [bluray, web] Which YTS release (if both exist) do you prefer
    yts_primary_languages = ['en']      # Only return movies of specified languages. Set to [] for all languages.
    ## LANGUAGE CODES RETURNED BY THE API AS OF 2022-04. Keep in mind YTS primarily releases English ('en') films.
    ## af, ak, am, ar, be, bn, bo, bs, ca, cn, cs, cy, da, de, el, en, es, et, eu, fa, fi, fr, ga, gl, he, hi, ht, 
    ## hu, hy, id, is, it, ja, ka, kk, km, kn, ko, ku, ky, la, lg, lt, lv, mk, ml, mn, mr, ms, mt, nb, nl, no, os, 
    ## pa, pl, ps, pt, ro, ru, sh, sk, sl, so, sr, st, sv, sw, ta, te, th, tl, tr, uk, ur, vi, wo, xx, yi, zh, zu

    # The below trackers will get appended to the generated magnet_url
        ## NOTE: The ones shown here are listed in the YTS API docs as examples, but they may
        ## no longer work. These are only important if you plan to use magnet links to add torrents
        ##  example: 'udp://sometracker.url:80/announce'
    magnet_tracker_announce_urls=[
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
   
    # Radarr Configuration
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
        'tags':['yts-api']                      # List of tags to add to the movie
                                                    ## Set to '' for no tags
    }
    
    
###############################################
### You shouldn't need to modify below here ###
###############################################
    # Do ALL the things
    df_yts = ytsapi(yts_query_parameters)
    df_yts = yts_cleandata(df_yts, magnet_tracker_announce_urls, yts_query_parameters['quality'], yts_earliest_year, yts_preferred_release, yts_primary_languages)
    if len(df_yts['id']) > 0:
        print("  After applying your filters, " + str(len(df_yts['id'])) + " releases were found.")
    if len(df_yts['id']) == 0:
        print("  No movies were found that match all of your criteria.\n  Please change your YTS options and try again.")
        sys.exit(1)
    if output_csv or grab_torrent_files or export_magnet_list:
        # make an output directory only if we expect file output
        output_dir = os.getcwd() + "/output/"
        if not os.path.exists(output_dir):
            try:
                os.mkdir(output_dir)
            except:
                print('''  Unable to create output directory.
  Please make sure to run with proper permissions, 
  or disable all options that output files to your system.
                ''')
                sys.exit(1)
    if output_csv: 
        try:
            df_yts.to_csv(output_dir + "^yts_movies.csv", index=False)
            print("  Successfully wrote ^yts_movies.csv")
        except:
            print("  Either yts_movies.csv or the directory is write-protected. No CSV output this time!")
    if grab_torrent_files:
        download_torr_files(df_yts, output_dir)
    if export_magnet_list:
        try:           
            with open(output_dir + '^yts_magnets.txt', 'w') as f:
                f.write(df_yts['torrent.magnet_url'].str.cat(sep='\n'))
            print("  Successfully wrote ^yts_magnets.csv")
        except:
            print("  Either yts_magnets.csv or the output directory is write-protected. No magnet list output this time!")
    if radarr_autoadd:
        radarrapi_autoadd(df_yts, radarr_api_parameters)


def ytsapi(yts_query_params):
    yts_api_url = "https://yts.mx/api/v2/list_movies.json"
    df = pd.DataFrame()
    pages = ytsapi_getpage(yts_api_url, yts_query_params, mode='pages')
    # pages = 3   # when debugging, you probably don't want to pull every page.
    print("\n  Grabbing " + str(pages) + " pages worth of releases. This may take some time...")
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
    sys.exit(1)
    
def yts_cleandata(df, announce_urls, quality, year, release, languages):
    print("\n  Cleaning up the data. Please wait...")
    magnet_announce_string = ""
    for url in announce_urls:
        magnet_announce_string += "&tr=" + url
    df_sort = {'torrent.quality': ['2160p', '1080p', '720p', '3D']}
    # Set sort order based on preferred release:
    if release.lower() == 'bluray': df_sort['torrent.type'] = ['bluray', 'web']
    if release.lower() == 'web': df_sort['torrent.type'] = ['web', 'bluray']
    # Filter year
    df = df[df['year'] >= year]
    # Filter language, if set
    if len(languages) > 0:
        df = df[df['language'].isin(languages)]
    # Make sure the applied filters haven't emptied the results list.
    if len(df['id']) == 0:
        print("  No movies were found that match all of your criteria.\n  Please change your YTS options and try again.")
        sys.exit(1)
    # Break out torrent data
    torrents_columns = list(pd.DataFrame(df['torrents'].iat[0]).columns)
    df_torrents = df.explode('torrents').reset_index(drop=True)[['id', 'torrents']]
    for column in torrents_columns:
        df_torrents['torrent.' + column] = df_torrents.torrents.apply(lambda x: x[column])
    # Filter down to selected quality.
    if quality != 'All':
        df_torrents = df_torrents[df_torrents['torrent.quality'] == quality]
    # Concatenate quality
    df_torrents['torrent.full_quality'] = df_torrents['torrent.quality'].astype(str).str.upper() + "-" + df_torrents['torrent.type'].astype(str).str.upper()
    # Merge the torrent data back into the main dataframe
    df = df.merge(df_torrents, how='left', on='id', validate='one_to_many')
    df.drop(columns=['torrents_x', 'torrents_y'], inplace=True)
    df['torrent.magnet_url'] = "magnet:?xt=urn:btih:" + df['torrent.hash'] + "&dn=" + df['slug'] + "---" + df['torrent.quality'] + "-" + df['torrent.type'] + magnet_announce_string
    # Sort quality/release and then keep only preferred
    df['torrent.quality'] = pd.Categorical(df['torrent.quality'], df_sort['torrent.quality'])
    df['torrent.type'] = pd.Categorical(df['torrent.type'], df_sort['torrent.type'])
    df.sort_values(['imdb_code','torrent.quality','torrent.type'], inplace=True)
    df.drop_duplicates(['imdb_code','torrent.quality'], keep='first', inplace=True, ignore_index=True)
    return df

def download_torr_files(df, output_dir):
    failed = 0
    print("  Attempting to download " + str(len('torrent.url')) + " torrents. This may take awhile...")
    for tor in df['torrent.url']:
        print(tor)
        try:
            tor = requests.get(tor, allow_redirects=True)
            filename = str.split(tor.headers.get('content-disposition'), '"')[1]
            open(output_dir + filename, 'wb').write(tor.content)
        except:
            failed += 1
            print(filename + " failed to download.")
    print("  Finished downloading! (" + str(failed) + "/" + str(len('torrent.url')) + " failed to download)")

def radarrapi_autoadd(df, radarr_params):
    try: 
        radarr = RadarrAPI(radarr_params['url'], radarr_params['api_key'])
    except Exception as e:
        print(e)
        sys.exit(1)
    imdb_ids = df['imdb_code'].unique().tolist()
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
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    get_those_movies()
