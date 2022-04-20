# yts-to-radarr

YES! I'm a dirty pleb and I like YiFY for my personal consumption. If that also describes you, then please feel free to adapt this to your wants.

While I already have an RSS list set up in Radarr, the 6-hour limitation means some new things and all past releases (since the RSS only shows the 100 most recent releases) are missed. I spent a couple hours throwing together this dirty python script to be able to do a one-time pull of more of the YTS catalog and import the lists dirtectly into Radarr. I did make it somewhat user-friendly for individual customization, though!

You'll probably want to make sure that YTS is set up via Prowlarr/Jackett as an indexer in Radarr before using this.

I've got minimal experience with APIs, and had never even looked at the YTS or Radarr API documentation prior to making this. I don't know if the YTS API has rate limits as their documenbtation doesn't specify anything. It seems to randomly stop returning things, but I never get an actual cooldown response in my (admittedly limited) testing. 

I might flesh this out a bit more down the road, but feel free to fork/PR/etc.

USE AT YOUR OWN RISK! I AM NOT RESPONSIBLE FOR WHAT YOU DO WITH THIS SCRIPT OR IF YOUR RADARR INSTALLATION DOESN'T PLAY NICE WITH HOW IT WORKED FOR ME!

FYI, I run Radarr in docker using the lsio/radarr:nightly image. I did not test this on other versions, but it should be perfectly functional as long as your version of Radarr uses v3 of the API (and if yours is so far out of date that is does not support tthe v3 API....update your stuff). 