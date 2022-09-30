SPOTIFY_CLIENT_ID = ""  # Required
SPOTIFY_CLIENT_SECRET = ""  # Required

PLAYLIST_ID = ""  # Required

SORTED_PLAYLIST_IDS = {  # Required
    # Language Code: Playlist ID
    # https://cloud.google.com/translate/docs/languages
    # This can only have a maximum of 4 languages (due to GCP speech API limitations)
    # Note that language code string must be lowercase, or else it will not work.
}

SPOTIFY_OAUTH_HOST = {  # Required
    "host": "127.0.0.1",
    "port": 8080,
}

SPOTIFY_STATE = ""  # Required (just fill in random things)

SPOTIFY_SCOPES = [  # Required
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
]

SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080/callback"  # Required

# Google Cloud requires us to use a service account, so we need to create one and save it. The code will handle the rest.
# If you are running this on GCE (Google Compute Engine) VM or other GCP products, you can put it as an empty string or None as it is optional.
# For other platforms/products, you need to create a service account and put the path here.
GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH = ""  # Optional* (look at the comments above this line)

GOOGLE_CLOUD_PROJECT_NUMBER_OR_ID = ""  # Required
