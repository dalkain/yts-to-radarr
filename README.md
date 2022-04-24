# yts-to-radarr

YES! I'm a filthy pleb and I like YIFY encodes for my personal consumption. If that also describes you, then please feel free to adapt script this to your wants.

## What does this do?
Grabs a list of movies released by YTS using their API based on configurable criteria. It also allows for a few more filtering options than the YTS API natively supports
  
With this data, you are given the option to do any combination of the following:
- Export all of the details from the YTS API to a CSV
- Automatically grab all related torrent files from YTS
- Export a txt file with a list of magnet links to the related torrents from YTS
- Automatically add all of the movies to your Radarr installation via its API (with configurable options)
  - If you want, it can even initiate search-on-add in Radarr

## Why does this exist?
The limitations of the YTS RSS feeds combined with the 6-hour minimum refresh for Lists in Radarr means I occasionally miss some new YTS releases and was unable to automate pulling the back catalog. I spent a couple hours throwing together this python script to extract more of the YTS catalog from the YTS API and add them directly into Radarr and initiate an automatic search. I tried to make it somewhat user-friendly for individual customization (or for running multiple times with different criteria)!

## How to run:
- Requires python3 (I personally use 3.9) and the pip packages listed in requirements.txt
- You'll probably want to make sure that YTS is set up via Prowlarr/Jackett as an indexer in Radarr before using this
- Download main.py
- Modify all of the variables at the beginning of main.py to suit your needs (there are quite a few options)
- Run main.py
  - No, I didn't make it guided or executable or anything like that (maybe one day); it's just a flat python script that needs to be run in a terminal.

### Other Notes
- I run Radarr in docker on UnRAID using the lsio/radarr:nightly image (v4.2.0.6209 when this readme was created), and I ran this script on my Windows PC running python 3.9. I did not test this on other images/platforms, but it should work fine as long as your version of Radarr uses v3 of the API _(and if your Radarr installation is so far out of date that is does not support the v3 API....update your stuff)_
- I don't know if the YTS API has rate limits as their documenbtation doesn't specify anything. The API seems to randomly stop returning things randomly sometimes, but I've also been able to run a test pull of every 1080p encode they've ever released successfully (which is over 800 GETs even at the max page size).
