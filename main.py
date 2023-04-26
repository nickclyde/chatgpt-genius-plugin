from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import functools
import io
import os
from pydantic import BaseModel
import yaml
from lyricsgenius import Genius


app = FastAPI()
genius = Genius()

# Serve static files in .well-known and assets
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="static")

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


@app.get("/")
async def root():
    return {"message": "Welcome to the ChatGPT Genius Plugin!"}


# Get song lyrics
@app.get("/lyrics")
async def get_lyrics(song: str, artist: str):
    song = genius.search_song(song, artist)
    return {"lyrics": song.lyrics}


# additional yaml version of openapi.json
@app.get("/openapi.yaml", include_in_schema=False)
@functools.lru_cache()
def read_openapi_yaml() -> Response:
    openapi_json = app.openapi()
    yaml_s = io.StringIO()
    yaml.dump(openapi_json, yaml_s)
    return Response(yaml_s.getvalue(), media_type="text/yaml")
