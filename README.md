# yts-to-radarr

YES! I'm a dirty pleb and I like YIFY encodes for my personal consumption. If that also describes you, then please feel free to adapt script this to your wants.

The limitations of the YTS RSS feeds combined with the 6-hour minimum refresh for RSS feeds in Radarr means I occasionally miss some new YTS releases and am unable to automate pulling the back catalog. So, I spent a couple hours throwing together this python script to extract more of the YTS catalog from the YTS API and add them directly into Radarr and initiate an automatic search. I tried to make it somewhat user-friendly for individual customization (or for running multiple times with different criteria)!

TO RUN:
- You'll probably want to make sure that YTS is set up via Prowlarr/Jackett as an indexer in Radarr before using this
- Modify all of the variables at the top of main.py to suit your needs
- No, I didn't make it guided or executable or anything; it's just a flat python script that needs to be run in a terminal. Make sure the pip packages in requirements.txt are installed in your environment.

I run Radarr in docker on UnRAID using the lsio/radarr:nightly image (v4.2.0.6209 when this readme was updated), and I ran this script from my PC running python 3.9. I did not test this on other images/platforms, but it should work fine as long as your version of Radarr uses v3 of the API (and if your Radarr installation is so far out of date that is does not support the v3 API....update your stuff).

I've got minimal experience with APIs, and had never even looked at the YTS or Radarr API documentation prior to making this. I don't know if the YTS API has rate limits as their documenbtation doesn't specify anything. The API seems to randomly stop returning things sometimes, but I've also been able to run a test pull of every 1080p encode they've ever released successfully (which is over 800 GETs). I never get an actual cooldown response in my (admittedly limited) testing. 

I will probably flesh this out a bit or clean it up more at some point down the road, but feel free to modify it for your own use.

DISCLAIMER: USE AT YOUR OWN RISK! I AM NOT RESPONSIBLE FOR WHAT INFORMATION YOU GATHER WITH THIS SCRIPT OR IF YOUR RADARR INSTALLATION DOESN'T PLAY NICE WHEN GETTING HAMMERED WITH API CALLS!
