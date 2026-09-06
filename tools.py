import os
import json
import time
import httpx
from dotenv import load_dotenv
from fallback_data import FALLBACK_BY_TITLE, FALLBACK_BY_MOOD, FALLBACK_AVAILABILITY, DEFAULT_AVAILABILITY

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")  # optional second source, see .env.example

# Basic network resilience: short timeout + one retry with a brief backoff,
# so a transient ISP-level block (e.g. WinError 10054 / "Connection reset by
# peer", or a "timed out") doesn't crash the agent loop — it just surfaces
# as a tool error the LLM (and the loop-control logic in agent.py) can
# react to.
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_RETRY_BACKOFF_SECONDS = 0.6


def _safe_get(url: str, params: dict) -> dict:
    """GET with one retry. Returns parsed JSON, or {'_error': ...} on failure."""
    last_error = None
    for attempt in range(2):
        try:
            res = httpx.get(url, params=params, timeout=_TIMEOUT)
            res.raise_for_status()
            return res.json()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
            last_error = e
            if attempt == 0:
                time.sleep(_RETRY_BACKOFF_SECONDS)
    return {"_error": f"network error after retry: {last_error}"}


# --- Second live data source (OMDb) --------------------------------------
# Deliberately a completely different domain/provider than TMDB. Some
# networks (notably several Indian ISPs, per a long-running court-ordered
# anti-piracy blocklist) block themoviedb.org specifically while the rest
# of the internet works fine. OMDb gives the agent a real second chance at
# live data instead of falling straight to the static local dataset.
# Free key: https://www.omdbapi.com/apikey.aspx (instant, no card needed).


def _omdb_search_title(title: str):
    if not OMDB_API_KEY:
        return None
    try:
        res = httpx.get(
            "https://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "t": title},
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
    except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError):
        return None
    if data.get("Response") == "True" and data.get("imdbID"):
        return {"id": data["imdbID"], "title": data.get("Title", title), "year": data.get("Year", "")}
    return None


def search_movie_title(title: str) -> str:
    data = _safe_get(
        "https://api.themoviedb.org/3/search/movie",
        params={"api_key": TMDB_API_KEY, "query": title},
    )
    if "_error" not in data:
        results = data.get("results", [])
        if results:
            return json.dumps(
                {
                    "id": str(results[0]["id"]),
                    "title": results[0]["title"],
                    "year": results[0].get("release_date", "")[:4],
                    "source": "tmdb",
                }
            )
        return json.dumps({"error": "Movie not found"})

    # TMDB unreachable — try OMDb as a genuine second live source.
    omdb_hit = _omdb_search_title(title)
    if omdb_hit:
        print(f"🌐 TMDB unreachable — found '{title}' via OMDb instead")
        return json.dumps({**omdb_hit, "source": "omdb"})

    # Both live sources failed — last resort, local dataset.
    fallback = FALLBACK_BY_TITLE.get(title.strip().lower())
    if fallback:
        print(f"⚠️  TMDB and OMDb both unreachable — using offline fallback for '{title}'")
        return json.dumps({**fallback, "id": str(fallback["id"]), "source": "offline_fallback"})

    return json.dumps({"error": data["_error"]})


def _mood_fallback(keyword: str):
    key = keyword.strip().lower()
    if key in FALLBACK_BY_MOOD:
        return FALLBACK_BY_MOOD[key]
    # loose match: keyword is a substring of, or contains, a known mood
    for known, movies in FALLBACK_BY_MOOD.items():
        if key in known or known in key:
            return movies
    return None


def discover_by_mood(keyword: str) -> str:
    # OMDb has no genre/mood discovery endpoint on its free tier, so the
    # fallback path here goes straight to the curated local dataset —
    # same as before.
    kw_data = _safe_get(
        "https://api.themoviedb.org/3/search/keyword",
        params={"api_key": TMDB_API_KEY, "query": keyword},
    )
    if "_error" in kw_data:
        fallback = _mood_fallback(keyword)
        if fallback:
            print(f"⚠️  TMDB unreachable — using offline fallback for mood '{keyword}'")
            return json.dumps([{**m, "id": str(m["id"]), "source": "offline_fallback"} for m in fallback])
        return json.dumps({"error": kw_data["_error"]})

    kws = kw_data.get("results", [])
    if not kws:
        return json.dumps({"error": "No keywords matched"})

    data = _safe_get(
        "https://api.themoviedb.org/3/discover/movie",
        params={
            "api_key": TMDB_API_KEY,
            "with_keywords": kws[0]["id"],
            "sort_by": "vote_average.desc",
            "vote_count.gte": 50,
        },
    )
    if "_error" in data:
        fallback = _mood_fallback(keyword)
        if fallback:
            print(f"⚠️  TMDB unreachable — using offline fallback for mood '{keyword}'")
            return json.dumps([{**m, "id": str(m["id"]), "source": "offline_fallback"} for m in fallback])
        return json.dumps({"error": data["_error"]})

    movies = data.get("results", [])[:3]
    return json.dumps(
        [
            {"id": str(m["id"]), "title": m["title"], "overview": m["overview"][:100], "source": "tmdb"}
            for m in movies
        ]
    )


def get_availability(movie_id: str) -> str:
    """
    movie_id may be:
      - a numeric TMDB id (string of digits) returned by a TMDB-sourced search
      - an IMDb id like 'tt1234567' returned by an OMDb-sourced search
      - a numeric local-fallback id (string of digits) from the offline dataset
    """
    movie_id = str(movie_id)

    if movie_id.isdigit():
        data = _safe_get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers",
            params={"api_key": TMDB_API_KEY},
        )
        if "_error" not in data:
            providers = data.get("results", {}).get("US", {})
            return json.dumps(
                {
                    "free": [p["provider_name"] for p in providers.get("free", []) + providers.get("ads", [])],
                    "subscription": [p["provider_name"] for p in providers.get("flatrate", [])],
                    "rent": [p["provider_name"] for p in providers.get("rent", [])],
                    "source": "tmdb",
                }
            )
        # TMDB unreachable — this numeric id might match our local dataset.
        fallback = FALLBACK_AVAILABILITY.get(int(movie_id), DEFAULT_AVAILABILITY)
        print(f"⚠️  TMDB unreachable — using offline fallback availability for id {movie_id}")
        return json.dumps({**fallback, "source": "offline_fallback"})

    # Non-numeric id (e.g. an IMDb id from OMDb). There's no free, reliable
    # live streaming-availability API keyed by IMDb id, so be upfront about
    # the limitation instead of guessing silently.
    print(f"⚠️  No live availability source for id '{movie_id}' — showing common defaults")
    return json.dumps({**DEFAULT_AVAILABILITY, "source": "offline_fallback", "note": "unverified — live lookup unavailable for this id"})


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_movie_title",
            "description": "Use this when the user asks for a specific movie by name.",
            "parameters": {
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_by_mood",
            "description": "Use this when the user describes a vibe, genre, or mood.",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string"}},
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_availability",
            "description": (
                "Checks where a movie is legally streaming. Pass the exact 'id' value "
                "returned by search_movie_title or discover_by_mood for this movie."
            ),
            "parameters": {
                "type": "object",
                "properties": {"movie_id": {"type": "string"}},
                "required": ["movie_id"],
            },
        },
    },
]

TOOL_MAP = {
    "search_movie_title": search_movie_title,
    "discover_by_mood": discover_by_mood,
    "get_availability": get_availability,
}
