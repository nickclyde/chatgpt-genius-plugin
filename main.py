from fastapi import Depends, FastAPI, Request
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
    description="Use the Genius API to search for song lyrics, discover song meanings and trivia using annotations, get artist and album data, and write song parodies",
)

# Serve static files in .well-known and assets
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="manifest")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# CORS config
origins = [
    "https://chat.openai.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auth middleware
@app.middleware("http")
async def auth(request: Request, call_next):
    # Skip auth for health check and static files
    if (
        request.url.path == "/"
        or request.url.path.startswith("/.well-known")
        or request.url.path.startswith("/assets")
    ):
        response = await call_next(request)
        return response
    # Check for auth header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return Response("Missing Authorization header", status_code=401)
    if not auth_header.startswith("Bearer "):
        return Response("Invalid Authorization header", status_code=401)
    # Check for valid access token
    access_token = request.headers.get("Authorization").replace("Bearer ", "", 1)
    request.state.genius = Genius(access_token)
    response = await call_next(request)
    return response


# Dependency
def get_genius(request: Request):
    return request.state.genius


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
async def get_lyrics(song_name: str, artist_name: str, genius=Depends(get_genius)):
    song = genius.search_song(song_name, artist_name)
    return {"lyrics": song.lyrics}


# Get song annotations
@app.get(
    "/annotations",
    summary="Get song annotations",
    description="Get song annotations for a given song name. May optionally specify artist name.",
)
async def get_annotations(song_name: str, artist_name: str, genius=Depends(get_genius)):
    song = genius.search_song(song_name, artist_name)
    annotations = genius.song_annotations(song.id)
    return {"annotations": annotations}


# Get song comments
@app.get(
    "/comments",
    summary="Get song comments",
    description="Get song comments for a given song name. May optionally specify artist name.",
)
async def get_comments(song_name: str, artist_name: str, genius=Depends(get_genius)):
    song = genius.search_song(song_name, artist_name)
    comments = genius.song_comments(song)
    return {"comments": comments}


# Get song metadata
@app.get(
    "/metadata",
    summary="Get song metadata",
    description="Get song metadata for a given song name. May optionally specify artist name.",
)
async def get_metadata(song_name: str, artist_name: str, genius=Depends(get_genius)):
    song = genius.search_song(song_name, artist_name)
    return {"metadata": song.to_dict()}


# Find song by lyrics
@app.get(
    "/find-by-lyrics",
    summary="Find song by lyrics",
    description="Find song by lyrics",
)
async def find_by_lyrics(lyrics: str, genius=Depends(get_genius)):
    search_results = genius.search_lyrics(lyrics)
    return {"search_results": search_results}


##### ARTISTS #####
# Get artist id
@app.get(
    "/artist-id",
    summary="Get artist id",
    description="Get artist id for a given artist name.",
)
async def get_artist_id(artist_name: str, genius=Depends(get_genius)):
    artist = genius.search_artist(artist_name, max_songs=1, get_full_info=False)
    return {"artist_id": artist.id}


# Get artist metadata
@app.get(
    "/artist-metadata",
    summary="Get artist metadata",
    description="Get artist metadata for a given artist name.",
)
async def get_artist_metadata(artist_name: str, genius=Depends(get_genius)):
    artist = genius.search_artist(artist_name, max_songs=1, get_full_info=False)
    artist_metadata = artist.to_dict()
    artist_metadata.pop("songs", None)
    artist_metadata.pop("description_annotation", None)
    return {"artist": artist_metadata}


# Get artist's top songs
@app.get(
    "/artist-top-songs",
    summary="Get artist's top songs",
    description="Get artist's top songs for a given artist name.",
)
async def get_artist_top_songs(artist_name: str, genius=Depends(get_genius)):
    artist = genius.search_artist(artist_name, max_songs=5, get_full_info=False)
    top_songs = artist.to_dict()["songs"]
    return {"top_songs": top_songs}


##### ALBUMS #####
# Get album id
@app.get(
    "/album-id",
    summary="Get album id",
    description="Get album id for a given album name. May optionally specify artist name.",
)
async def get_album_id(album_name: str, artist_name: str, genius=Depends(get_genius)):
    search_term = f"{album_name} {artist_name}"
    search_results = genius.search_albums(search_term=search_term)
    album_id = search_results["sections"][0]["hits"][0]["result"]["id"]
    return {"album_id": album_id}


# Get album metadata
@app.get(
    "/album-metadata",
    summary="Get album metadata",
    description="Get album metadata for a given id.",
)
async def get_album_metadata(album_id: str, genius=Depends(get_genius)):
    album = genius.album(album_id)["album"]
    album.pop("description_annotation", None)
    album.pop("song_performances", None)
    album.pop("cover_arts", None)
    return {"album": album}


# Get album tracks
@app.get(
    "/album-tracks",
    summary="Get album tracks",
    description="Get album tracks for a given album id.",
)
async def get_album_tracks(album_id: str, genius=Depends(get_genius)):
    tracks = genius.album_tracks(album_id)
    return {"tracks": tracks}


# Get album art
@app.get(
    "/album-art",
    summary="Get album art image url",
    description="Get album art image url for a given album id.",
)
async def get_album_art(album_id: str, genius=Depends(get_genius)):
    arts = genius.album_cover_arts(album_id)
    album_art = arts["cover_arts"][0]["image_url"]
    return {"album_art": album_art}


# Get album by song
@app.get(
    "/album-id-by-song",
    summary="Get album id by song",
    description="Get album id for a given song name. May optionally specify artist name.",
)
async def get_album_by_song(
    song_name: str, artist_name: str, genius=Depends(get_genius)
):
    search_term = f"{song_name} {artist_name}"
    search_results = genius.search_albums(search_term=search_term)
    album_id = search_results["sections"][0]["hits"][0]["result"]["id"]
    return {"album_id": album_id}


##### MISC #####
# additional yaml version of openapi.json
@app.get("/openapi.yaml", include_in_schema=False)
@functools.lru_cache()
def read_openapi_yaml() -> Response:
    openapi_json = app.openapi()
    yaml_s = io.StringIO()
    yaml.dump(openapi_json, yaml_s)
    return Response(yaml_s.getvalue(), media_type="text/yaml")
