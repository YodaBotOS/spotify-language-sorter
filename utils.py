import os
import sys
import json
import time
import typing

import requests

import config
import spotify
from gcloud import detect_language_from_audio, detect_language_from_text


class Utils:
    client: spotify.SpotifyClient = None
    logger_func: typing.Callable = print

    class TerminalColors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        RED = '\033[91m'
        ERROR = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

        @classmethod
        def print(cls, text, color=None, colors=None, *args, **kwargs):
            colors = colors or []

            if color and colors:
                raise ValueError("Cannot use both color and colors")

            color = color or ''.join(colors)

            if not color:
                print(text, *args, **kwargs)
            else:
                print(f"{color}{text}{cls.ENDC}", *args, **kwargs)

    @classmethod
    def log(cls, msg, *args, error=False, raw=False, color_on_error=True, color_on_non_error=False, **kwargs):
        if not raw:
            if error:
                msg = f"[-] {msg}"
            else:
                msg = f"[+] {msg}"

        col = cls.TerminalColors.ERROR if error else cls.TerminalColors.OKGREEN

        if error and not color_on_error:
            col = None
        elif not error and not color_on_non_error:
            col = None

        cls.TerminalColors.print(msg, col, *args, **kwargs)

    @staticmethod
    def confirm(prompt: str = "Are you sure? (y/n)", ignore_y: bool = False) -> bool:
        if "-y" in sys.argv and not ignore_y:
            return True # for every prompt, return True

        prompt += "\n> "

        while True:
            ans = input(prompt).lower()

            if ans == "y":
                return True
            elif ans == "n":
                return False
            else:
                print("Invalid input.")

    @staticmethod
    def start_webserver(filename="webserver.py") -> int:
        path = os.path.dirname(os.path.abspath(__file__)) + f"/{filename}"

        return os.system(f"{sys.executable} {path}")

    @staticmethod
    def read_request_file(filename="request.json") -> dict:
        with open(filename, "r") as f:
            return json.load(f)

    @classmethod
    def initialize_spotify_client(cls, code) -> spotify.SpotifyClient:
        cls.client = spotify.SpotifyClient(config.SPOTIFY_CLIENT_ID, config.SPOTIFY_CLIENT_SECRET,
                                           config.SPOTIFY_REDIRECT_URI)
        cls.client.get_token(code, force=True)

        return cls.client

    @classmethod
    def check_is_me(cls):
        me = cls.client.get_current_user()

        confirm = cls.confirm(f"Is this you? \"{me['display_name']}\" - \"{me['external_urls']['spotify']}\" (y/n)")

        if not confirm:
            raise RuntimeError("User does not match.")

    @classmethod
    def get_possible_languages(cls, track):
        title = track["name"]
        preview_url = track.get("preview_url")

        resp_title = detect_language_from_text(title)

        if preview_url:
            preview = requests.get(preview_url).content

            resp_preview = detect_language_from_audio(preview)

        res = []  # code: ..., confidences: [..., ...], sum-confidence: ..., confidence: ...

        for lang in resp_title:
            res.append({
                "code": lang["language"],
                "confidences": [lang["confidence"]],
                "sum-confidence": lang["confidence"],
                "confidence": lang["confidence"]
            })

        if preview_url:
            for lang in resp_preview:  # type: ignore
                if lang["code"] in [r["code"] for r in res]:
                    for r in res:
                        if r["code"] == lang["language"]:
                            r["confidences"].append(lang["confidence"])
                            r["sum-confidence"] += lang["confidence"]
                            r["confidence"] = r["sum-confidence"] / len(r["confidences"])
                else:
                    res.append({
                        "code": lang["language"],
                        "confidences": [lang["confidence"]],
                        "sum-confidence": lang["confidence"],
                        "confidence": lang["confidence"]
                    })

        res.sort(key=lambda x: x["confidence"], reverse=True)

        return res, preview_url is not None

    @staticmethod
    def generate_track_uri(track_id):
        return f'spotify:track:{track_id}'

    @classmethod
    def get_tracks_on_playlist(cls, playlist_id):
        return [x["track"] for x in cls.client.get_playlist_items(playlist_id, limit=1)["items"]]

    @classmethod
    def handle_removed_tracks(cls, tracks):
        d = {}

        track_ids = [x["id"] for x in tracks]

        playlist_ids = config.SORTED_PLAYLIST_IDS.values()

        for playlist_id in playlist_ids:
            tracks = cls.get_tracks_on_playlist(playlist_id)

            for track in tracks:
                if track["id"] not in track_ids:
                    d[track["id"]].append(playlist_id)

        for track_id, playlist_ids in d.items():
            for playlist_id in playlist_ids:
                cls.client.delete_playlist_items(playlist_id, cls.generate_track_uri(track_id))

                cls.log(f"Removed track {track_id} from playlist {playlist_id}.")

                time.sleep(.5)

    @classmethod
    def run(cls):
        while True:
            cls.log("Getting tracks on playlist...")

            tracks = cls.get_tracks_on_playlist(config.PLAYLIST_ID)

            cls.log("Removing tracks (if needed)...")

            cls.handle_removed_tracks(tracks)

            cls.log("Running language sorter...")

            for track in tracks:
                cls.log("Now checking track: " + track["name"] + " - " + track["external_urls"]["spotify"])

                possible_languages, preview_available = cls.get_possible_languages(track)

                if preview_available is False:
                    cls.log("WARNING: No preview available. Only checking for title...", error=True)
                    continue

                for lang in possible_languages:
                    if playlist_id := config.SORTED_PLAYLIST_IDS.get(lang["code"]):
                        cls.client.add_playlist_items(playlist_id, track["uri"])

                        cls.log(f"Added track {track['id']} to playlist {playlist_id}.")

                        break

                time.sleep(.5)

            time.sleep(5)
