"""
Offline fallback dataset for CineAgent.

This is used ONLY when a live TMDB call fails after retry (network reset /
timeout). It exists so the agent still produces a real, sensible
conversation during a demo even if the network to TMDB is blocked in that
room/network — the moment TMDB is reachable again, the live API path is
used as normal (see tools.py: fallback is the last resort, not the default).

IDs below are best-effort real TMDB ids for well-known films, but since this
data only ever surfaces during a network outage (never checked against live
TMDB in that moment), exact-id accuracy isn't load-bearing — what matters is
that the agent keeps producing a coherent, on-topic conversation.
"""

# title.lower() -> {id, title, year}   (used by search_movie_title fallback)
FALLBACK_BY_TITLE = {
    "shaun of the dead": {"id": 747, "title": "Shaun of the Dead", "year": "2004"},
    "what we do in the shadows": {"id": 240832, "title": "What We Do in the Shadows", "year": "2014"},
    "paddington 2": {"id": 346648, "title": "Paddington 2", "year": "2017"},
    "school of rock": {"id": 458, "title": "School of Rock", "year": "2003"},
    "get out": {"id": 419430, "title": "Get Out", "year": "2017"},
    "the cabin in the woods": {"id": 22970, "title": "The Cabin in the Woods", "year": "2012"},
    "crimson peak": {"id": 232181, "title": "Crimson Peak", "year": "2015"},
    "the others": {"id": 1735, "title": "The Others", "year": "2001"},
    "knives out": {"id": 546554, "title": "Knives Out", "year": "2019"},
    "the grand budapest hotel": {"id": 120467, "title": "The Grand Budapest Hotel", "year": "2014"},
    "interstellar": {"id": 157336, "title": "Interstellar", "year": "2014"},
    "inception": {"id": 27205, "title": "Inception", "year": "2010"},
    "parasite": {"id": 496243, "title": "Parasite", "year": "2019"},
    "joker": {"id": 475557, "title": "Joker", "year": "2019"},
    "the dark knight": {"id": 155, "title": "The Dark Knight", "year": "2008"},
    "avengers infinity war": {"id": 299536, "title": "Avengers: Infinity War", "year": "2018"},
    "mad max fury road": {"id": 76341, "title": "Mad Max: Fury Road", "year": "2015"},
    "pulp fiction": {"id": 680, "title": "Pulp Fiction", "year": "1994"},
    "the godfather": {"id": 238, "title": "The Godfather", "year": "1972"},
    "schindler's list": {"id": 424, "title": "Schindler's List", "year": "1993"},
    "la la land": {"id": 313369, "title": "La La Land", "year": "2016"},
    "your name": {"id": 372058, "title": "Your Name", "year": "2016"},
    "spirited away": {"id": 129, "title": "Spirited Away", "year": "2001"},
    "toy story": {"id": 862, "title": "Toy Story", "year": "1995"},
    "soul": {"id": 508442, "title": "Soul", "year": "2020"},
    "luca": {"id": 508943, "title": "Luca", "year": "2021"},
    "the lord of the rings the return of the king": {"id": 122, "title": "The Lord of the Rings: The Return of the King", "year": "2003"},
    "home alone": {"id": 771, "title": "Home Alone", "year": "1990"},
    "the good the bad and the ugly": {"id": 429, "title": "The Good, the Bad and the Ugly", "year": "1966"},
}

# keyword/mood.lower() -> list of {id, title, overview}  (used by discover_by_mood fallback)
FALLBACK_BY_MOOD = {
    "horror comedy": [
        {"id": 747, "title": "Shaun of the Dead", "overview": "A man's zombie-apocalypse plan is foiled by his own ineptitude and undead ex-neighbors."},
        {"id": 240832, "title": "What We Do in the Shadows", "overview": "Vampire flatmates struggle with modern life, roommates, and the club scene."},
    ],
    "gothic horror": [
        {"id": 232181, "title": "Crimson Peak", "overview": "A young woman is drawn into a decaying mansion haunted by its own dark history."},
        {"id": 1735, "title": "The Others", "overview": "A woman and her children living in a darkened house begin to suspect it's haunted."},
    ],
    "feel good comedy": [
        {"id": 346648, "title": "Paddington 2", "overview": "A lovable bear ends up in prison after being framed, and wins everyone over anyway."},
        {"id": 120467, "title": "The Grand Budapest Hotel", "overview": "A concierge and his protege get caught up in a farcical, colorful murder-mystery caper."},
    ],
    "violent horror": [
        {"id": 22970, "title": "The Cabin in the Woods", "overview": "Five friends at a remote cabin become pawns in a horror-ritual bigger than they know."},
    ],
    "witty mystery": [
        {"id": 546554, "title": "Knives Out", "overview": "A detective investigates the death of a wealthy crime novelist surrounded by a scheming family."},
    ],
    "sci-fi": [
        {"id": 157336, "title": "Interstellar", "overview": "A crew travels through a wormhole to find a new home for humanity as Earth dies."},
        {"id": 27205, "title": "Inception", "overview": "A thief who steals secrets through dream-sharing takes on one final, impossible job."},
    ],
    "psychological thriller": [
        {"id": 496243, "title": "Parasite", "overview": "A poor family schemes to infiltrate the household of a wealthy one, with dark consequences."},
        {"id": 419430, "title": "Get Out", "overview": "A young man uncovers a disturbing secret during a visit to his girlfriend's family estate."},
    ],
    "romantic": [
        {"id": 313369, "title": "La La Land", "overview": "An aspiring actress and a jazz musician fall in love while pursuing their dreams in LA."},
        {"id": 372058, "title": "Your Name", "overview": "Two teenagers form a deep, fated connection after mysteriously swapping bodies."},
    ],
    "epic fantasy": [
        {"id": 122, "title": "The Lord of the Rings: The Return of the King", "overview": "The final battle for Middle-earth unfolds as the fellowship's quest reaches its end."},
    ],
    "war drama": [
        {"id": 424, "title": "Schindler's List", "overview": "A businessman saves the lives of over a thousand Jewish refugees during the Holocaust."},
    ],
    "crime drama": [
        {"id": 238, "title": "The Godfather", "overview": "The aging patriarch of a crime dynasty transfers control to his reluctant son."},
        {"id": 680, "title": "Pulp Fiction", "overview": "The lives of two hitmen, a boxer, and a gangster's wife intertwine in four tales of violence."},
    ],
    "superhero": [
        {"id": 155, "title": "The Dark Knight", "overview": "Batman faces the Joker, a criminal mastermind bent on plunging Gotham into anarchy."},
        {"id": 299536, "title": "Avengers: Infinity War", "overview": "The Avengers race to stop a cosmic tyrant from wiping out half of all life."},
    ],
    "action": [
        {"id": 76341, "title": "Mad Max: Fury Road", "overview": "A woman rebels against a tyrant in a post-apocalyptic wasteland alongside a drifter."},
        {"id": 155, "title": "The Dark Knight", "overview": "Batman faces the Joker, a criminal mastermind bent on plunging Gotham into anarchy."},
    ],
    "family animated": [
        {"id": 862, "title": "Toy Story", "overview": "A cowboy doll's world is turned upside down when a spaceman action figure arrives."},
        {"id": 508943, "title": "Luca", "overview": "Two sea monsters disguised as boys spend a summer of freedom in an Italian seaside town."},
    ],
    "feel good animated": [
        {"id": 508442, "title": "Soul", "overview": "A jazz musician's soul ends up in the cosmic realm and must find its way back to his body."},
        {"id": 508943, "title": "Luca", "overview": "Two sea monsters disguised as boys spend a summer of freedom in an Italian seaside town."},
    ],
    "japanese animation": [
        {"id": 129, "title": "Spirited Away", "overview": "A girl wanders into a spirit world and must work in a bathhouse to save her parents."},
        {"id": 372058, "title": "Your Name", "overview": "Two teenagers form a deep, fated connection after mysteriously swapping bodies."},
    ],
    "holiday family": [
        {"id": 771, "title": "Home Alone", "overview": "An eight-year-old boy defends his home against bumbling burglars after being left behind."},
    ],
    "classic western": [
        {"id": 429, "title": "The Good, the Bad and the Ugly", "overview": "Three gunslingers compete to find a fortune in gold buried in a Civil War-era cemetery."},
    ],
}

# movie id -> providers   (used by get_availability fallback)
FALLBACK_AVAILABILITY = {
    747: {"free": ["Tubi", "Pluto TV"], "subscription": ["Netflix"], "rent": ["Amazon Video"]},
    240832: {"free": ["Tubi"], "subscription": ["Hulu"], "rent": ["Apple TV"]},
    346648: {"free": ["Pluto TV"], "subscription": ["Max"], "rent": ["Amazon Video"]},
    458: {"free": ["Tubi"], "subscription": [], "rent": ["Apple TV"]},
    419430: {"free": [], "subscription": ["Peacock"], "rent": ["Amazon Video"]},
    22970: {"free": ["Tubi"], "subscription": [], "rent": ["Apple TV"]},
    232181: {"free": [], "subscription": [], "rent": ["Amazon Video", "Apple TV"]},
    1735: {"free": ["Pluto TV"], "subscription": [], "rent": ["Amazon Video"]},
    546554: {"free": [], "subscription": ["Prime Video"], "rent": ["Apple TV"]},
    120467: {"free": [], "subscription": ["Hulu"], "rent": ["Amazon Video"]},
    157336: {"free": [], "subscription": ["Paramount+"], "rent": ["Amazon Video"]},
    27205: {"free": [], "subscription": ["Netflix"], "rent": ["Apple TV"]},
    496243: {"free": ["Tubi"], "subscription": ["Hulu"], "rent": ["Amazon Video"]},
    475557: {"free": [], "subscription": ["Max"], "rent": ["Apple TV"]},
    155: {"free": [], "subscription": ["Max"], "rent": ["Amazon Video"]},
    299536: {"free": [], "subscription": ["Disney+"], "rent": ["Apple TV"]},
    76341: {"free": ["Pluto TV"], "subscription": ["Max"], "rent": ["Amazon Video"]},
    680: {"free": ["Tubi"], "subscription": [], "rent": ["Apple TV"]},
    238: {"free": [], "subscription": ["Paramount+"], "rent": ["Amazon Video"]},
    424: {"free": [], "subscription": ["Peacock"], "rent": ["Apple TV"]},
    313369: {"free": [], "subscription": ["Netflix"], "rent": ["Amazon Video"]},
    372058: {"free": [], "subscription": ["Crunchyroll"], "rent": ["Apple TV"]},
    129: {"free": [], "subscription": ["Max"], "rent": ["Amazon Video"]},
    862: {"free": [], "subscription": ["Disney+"], "rent": ["Apple TV"]},
    508442: {"free": [], "subscription": ["Disney+"], "rent": []},
    508943: {"free": [], "subscription": ["Disney+"], "rent": []},
    122: {"free": [], "subscription": ["Max"], "rent": ["Amazon Video"]},
    771: {"free": ["Pluto TV"], "subscription": ["Disney+"], "rent": ["Amazon Video"]},
    429: {"free": ["Tubi"], "subscription": [], "rent": ["Apple TV"]},
}

DEFAULT_AVAILABILITY = {"free": ["Tubi", "Pluto TV"], "subscription": [], "rent": []}
