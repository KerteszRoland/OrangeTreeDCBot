import spotipy
from dotenv import load_dotenv
from os import environ


load_dotenv()
CLIENT_ID = environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:3000/login"


def get_test_sp():
    scopes = ["playlist-modify-public", "user-library-read", "user-read-private", "user-read-currently-playing",
              "user-read-playback-state", "user-modify-playback-state"]
    o_auth = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        show_dialog=False,
        scope=scopes,
        open_browser=False)
    sp = spotipy.client.Spotify(oauth_manager=o_auth)
    return sp


def next_song(sp):
    device_id = get_active_device(sp)["id"]
    sp.next_track(device_id)


def get_current_playing_song(sp):
    return sp.current_user_playing_track()


def get_current_playing_song_name(sp):
    song = get_current_playing_song(sp)
    try:
        artists_names = ", ".join([x["name"] for x in song["item"]["artists"]])
        return f'{artists_names} - {song["item"]["name"]}'
    except Exception as e:
        print("error", e)
        return None


def get_active_device(sp):
    device = [x for x in sp.devices()["devices"] if x["is_active"] == True]
    return device[0]


def set_repeat(sp, mode="track"):
    sp.repeat(mode, device_id=get_active_device(sp)["id"])
