from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import functools
import io
import yaml
from lyricsgenius import Genius


# Initialize app
app = FastAPI(
    title="ChatGPT Genius Plugin",
    version="0.0.1",
    contact={
        "name": "Nick Clyde",
        "url": "https://github.com/nickclyde/chatgpt-genius-plugin",
        "email": "nick@clyde.tech",
    },
    license_info={
        "name": "Creative Commons Zero v1.0 Universal",
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    description="Use the Genius API to search for song lyrics, discover song meanings and trivia using annotations, get artist and album data, and write song parodies",
)

# Serve static files in .well-known and assets
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="manifest")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# CORS config
origins = [
    "http://localhost:8000",
    "https://chat.openai.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Genius API client
genius = Genius()


# Health check
@app.get("/")
async def health_check():
    return {"message": "Welcome to the ChatGPT Genius Plugin!"}


##### SONGS #####
# Get song lyrics
@app.get(
    "/lyrics",
    summary="Get song lyrics",
    description="Get song lyrics for a given song name. May optionally specify artist name.",
)
async def get_lyrics(song_name: str, artist_name: str):
    song = genius.search_song(song_name, artist_name)
    return {"lyrics": song.lyrics}


# Get song annotations
@app.get(
    "/annotations",
    summary="Get song annotations",
    description="Get song annotations for a given song name. May optionally specify artist name.",
)
async def get_annotations(song_name: str, artist_name: str):
    song = genius.search_song(song_name, artist_name)
    annotations = genius.song_annotations(song.id)
    return {"annotations": annotations}


# Get song comments
@app.get(
    "/comments",
    summary="Get song comments",
    description="Get song comments for a given song name. May optionally specify artist name.",
)
async def get_comments(song_name: str, artist_name: str):
    song = genius.search_song(song_name, artist_name)
    comments = genius.song_comments(song)
    return {"comments": comments}


# Get song metadata
@app.get(
    "/metadata",
    summary="Get song metadata",
    description="Get song metadata for a given song name. May optionally specify artist name.",
)
async def get_metadata(song_name: str, artist_name: str):
    song = genius.search_song(song_name, artist_name)
    return {"metadata": song.to_dict()}


# Find song by lyrics
@app.get(
    "/find-by-lyrics",
    summary="Find song by lyrics",
    description="Find song by lyrics",
)
async def find_by_lyrics(lyrics: str):
    search_results = genius.search_lyrics(lyrics)
    return {"search_results": search_results}


##### ARTISTS #####
# Get artist metadata
@app.get(
    "/artist",
    summary="Get artist metadata",
    description="Get artist metadata for a given artist name.",
)
async def get_artist(artist_name: str):
    artist = genius.search_artist(artist_name)
    return {"artist": artist.to_dict()}


##### ALBUMS #####
# Get album metadata
@app.get(
    "/album",
    summary="Get album metadata",
    description="Get album metadata for a given album name. May optionally specify artist name.",
)
async def get_album(album_name: str, artist_name: str):
    search_term = f"{album_name} {artist_name}"
    search_results = genius.search_albums(search_term=search_term)
    album = search_results[0]
    return {"album": album}


##### MISC #####
# additional yaml version of openapi.json
@app.get("/openapi.yaml", include_in_schema=False)
@functools.lru_cache()
def read_openapi_yaml() -> Response:
    openapi_json = app.openapi()
    yaml_s = io.StringIO()
    yaml.dump(openapi_json, yaml_s)
    return Response(yaml_s.getvalue(), media_type="text/yaml")
