import base64
import asyncio
import datetime

import requests


class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri, *, get_token=True, renew_token=True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.session = requests.Session()

        self.should_get_token = get_token
        self.should_renew_token = renew_token
        self._renew_task = False

        self.auth_token = None
        self.expired_at = None
        self.refresh_token = None

    @staticmethod
    def get_current_time(secs=0, add=False):
        if add:
            return datetime.datetime.now() + datetime.timedelta(seconds=secs)
        else:
            return datetime.datetime.now() - datetime.timedelta(seconds=secs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def get_auth(self, *, basic=False, header=True):
        if basic:
            auth_basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

            if not header:
                return f"Basic {auth_basic}"

            return {
                "Authorization": f"Basic {auth_basic}"
            }

        if not self.auth_token:
            self.get_token(force=True)

        if not header:
            return f"Bearer {self.auth_token}"

        return {"Authorization": f"Bearer {self.auth_token}"}

    async def _renew_token_task(self):
        while True:
            if self.expired_at < self.get_current_time(60):
                self.get_token(refresh_token=self.refresh_token, force=True)

            await asyncio.sleep(60)

    def get_token(self, code=None, refresh_token=None, *, force=False):
        if not self.should_get_token and not force:
            raise Exception("This client is not configured to get token (handle it yourself).")

        if self.auth_token and not force and self.expired_at > self.get_current_time(60):
            return self.auth_token

        url = "https://accounts.spotify.com/api/token"

        headers = {
            "Authorization": self.get_auth(basic=True, header=False),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        if refresh_token:
            data = {
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }

            r = self.session.post(url, data=data, headers=headers)
            js = r.json()

            self.auth_token = js["access_token"]
            self.expired_at = self.get_current_time(js["expires_in"], add=True)
            self.refresh_token = js.get("refresh_token", self.refresh_token)
        else:
            data = {
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }

            r = self.session.post(url, data=data, headers=headers)
            js = r.json()

            self.auth_token = js["access_token"]
            self.expired_at = self.get_current_time(js["expires_in"], add=True)
            self.refresh_token = js["refresh_token"]

            if self.should_renew_token:
                # Changes to asyncio event loops in >=3.10
                # Really hacky way, but idc.
                # If you want to fix this, go on make a PR

                async def main(cls):
                    func = self._renew_token_task()
                    cls._renew_task = asyncio.create_task(func)

                asyncio.run(main(self))

    def get_current_user(self):
        url = "https://api.spotify.com/v1/me"

        r = self.session.get(url, headers=self.get_auth())
        return r.json()

    def get_track(self, track_id, *, market="US"):
        url = f"https://api.spotify.com/v1/tracks/{track_id}"

        params = {
            "market": market
        }

        r = self.session.get(url, headers=self.get_auth(), params=params)
        return r.json()

    def get_playlist_items(self, playlist_id, *, market="US", fields=None, limit=100, offset=0):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        params = {
            "market": market,
            "limit": limit,
            "offset": offset
        }

        if fields:
            params["fields"] = fields

        r = self.session.get(url, headers=self.get_auth(), params=params)
        return r.json()

    def add_playlist_items(self, playlist_id, uris, *, position=None):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        uris = list(uris)

        data = {
            "uris": uris
        }

        if position:
            data["position"] = position

        r = self.session.post(url, headers=self.get_auth(), json=data)
        return r.json()

    def delete_playlist_items(self, playlist_id, uris):
        data = {
            "tracks": [{"uri": uri} for uri in uris]
        }

        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        r = self.session.delete(url, headers=self.get_auth(), json=data)
        return r.json()
