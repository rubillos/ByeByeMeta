# FB-Processor - Facebook Data Cleaner

1. [Bqckground](#background)
1. [Features](#features)
2. [Getting your data from Facebook](#data)
3. [Getting the script](#script)
4. [Running the script](#running)
5. [Adjusting the results](#adjusting)
6. [Viewing your posts](#viewing)

## <a name="background"></a>Background

With the moderation changes and general move towards the far-right of the Meta products, I decided it was time to leave. As such, I'm setting up shop on [BlueSky](https://bsky.app/profile/ubillos.bsky.social)

But I have quite a bit of history accumulated on Facebook that I don't want to lose. Hence this project.

Below are instructions for performing your download and for running the FB-Processor script. It's a Python script that is run from the command line. This might sound scary, but I'll walk you through the steps. If you can do the download from Facebook, I'm pretty sure you can handle running the script.

**Note:** Currently the script only runs on a Mac. If you're on Windows, contact me and I'll work with you to get a Windows version working.

## <a name="features"></a>Features

* Takes the data dump that you can download from FaceBook and turns it into a navigable web page where you can see and search all of your posts.
    * (Instagram version coming soon)
* Merges posts, uncategorized entries, photos, and videos into a single collection.
* Cleans up the HTML significantly
* Provides a navigation bar for quickly getting to any potion of any year.
* Removes duplicate entries.
* Provides a method for ommiting specific posts.
* You can see "Memories" - posts with today's month and year by appending "?memories" to the URL.

## <a name="data"></a>Getting your data from Facebook
From your Facebook page on a Mac browser:
1. Click you account icon in the uper right corner.
2. Click "Settings & privacy"
3. Click "Settings"
4. Under "Accounts Center" click "See more in Accounts Center"
5. Click "Your information and permissions"
6. Click "Download your information"
7. Click "Download or transfer information"
8. Click the checkbox next to your Facebook account
9. Click "Next"
10. Click "Specific types of information"
11. Click the "Posts" checkbox
12. Select "Download to device"
13. Click "Date range:, then click "All time", then "Save"
14. Make sure "Format" is set to "HTML"
15. Click "Media quality", then click "High", then "Save"
16. Click the box for "Mobile compatible media"

You'll now see a page saying that your information has been requesdted. It will take a little time for Facebook to process everything, usuualy just a few minutes. You'll get an email and a Facebook notification when your data is ready. When you receive it, select the notification, then:



## <a name="script"></a>Getting the script

## <a name="running"></a>Running the script

## <a name="adjusting"></a>Adjusting the results

## <a name="viewing"></a>Viewing your posts

---

---
## <a name="features"></a>Features

* Connects to the RV-C network in many modern RVs.
    * RV-C is a subset of CAN-Bus running at 250kbps.
* Uses an ESP32 with a CAN-Bus interface.
* Connects lights, fans, switches, and thermostats to HomeKit.
* Fits inside the RV wiring panel.
* Plugs into an unused CAN-Bus socket for power and data.
* STL files for a 3D printed case are included.
