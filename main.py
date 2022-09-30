import os
import sys
import time

import config
from utils import Utils
from gcloud import set_service_account_path

set_service_account_path(config.GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH)

utils = Utils()

if "-y" in sys.argv:
    utils.log("You have used the \"-y\" flag. This means that it will proceed with any prompt as an assumed yes.",
              error=True, raw=True)
    utils.log("This is not recommended and this can be very dangerous. Please use this with caution.",
              error=True, raw=True)

    # if not utils.confirm("Do you want to continue? (y/n)", ignore_y=True):
    #     utils.log("Please remove the \"-y\" flag and try again.", error=True)
    #     utils.log("Exiting...", error=True)
    #     os._exit(0)  # type: ignore

    time.sleep(7.5)

    utils.log("", raw=True)

utils.log("""Welcome to the Spotify Language Sorter!

This project is made by YodaBotOS. You can find the source code here: https://github.com/YodaBotOS/spotify-language-sorter

This project is licensed under the MPL 2.0 License.

This project uses Google Cloud's Translate API and Speech API as well as Spotify's API.

This project is not affiliated/endorsed with Google or Spotify in any way.


Note: This project is still in beta. This is not 100% accurate because of how Spotify API only gives us 30 seconds of preview audio and how artist named their songs.
""", raw=True)

if not utils.confirm("Do you want to continue? (y/n)"):
    utils.log("Exiting...", error=True)
    os._exit(0)  # type: ignore

utils.log("Starting webserver")

status_code = utils.start_webserver()

if status_code != 0:
    utils.log("Failed to start webserver (exited with non-zero status code)", error=True)
    os._exit(1)  # type: ignore

utils.log("Webserver has been shutdown")

utils.log("Getting access token")

request = utils.read_request_file()

client = utils.initialize_spotify_client(request["code"])

utils.check_is_me()


