# CineAgent

CineAgent is a terminal-based, ReAct-style movie recommendation agent. You describe a mood or name a movie, and it reasons step by step, calls tools to look up real data, and replies with a short, conversational recommendation — prioritizing free/ad-supported streaming over paid options.

---

## 1. What's inside

```
cine-agent/
├── agent.py          # ReAct loop, LLM config, short-term memory, loop-control
├── tools.py          # search_movie_title, discover_by_mood, get_availability
├── fallback_data.py  # small offline dataset used only if live sources fail
├── main.py           # terminal entry point
├── requirements.txt  # dependencies
└── .env.example      # required environment variables (copy to .env)
```

## 2. Setup (do this once)

**Step 1 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2 — Create your `.env` file**
Copy `.env.example` to a new file named `.env` in the same folder, and fill in your keys:
```
TMDB_API_KEY=your_tmdb_key_here
OPENROUTER_API_KEY=your_gemini_key_here
OMDB_API_KEY=your_omdb_key_here
```

| Key | Where to get it | Required? |
|---|---|---|
| `TMDB_API_KEY` | https://www.themoviedb.org/settings/api (free account) | Yes |
| `OPENROUTER_API_KEY` | A Gemini API key from Google AI Studio. The variable name is kept as `OPENROUTER_API_KEY` on purpose — the code points at Google's endpoint, so whatever valid Gemini key you paste here just works. | Yes |
| `OMDB_API_KEY` | https://www.omdbapi.com/apikey.aspx (free, instant, no card) | Optional but recommended — see "Why OMDb?" below |

**Step 3 — Run it**
```bash
python main.py
```
You should see:
```
🎬 CineAgent (terminal mode) — type 'exit' or 'quit' to end

Agent: What kind of mood are you in? (or name a movie)
```
Type a message and press Enter. Type `exit` or `quit` to stop.

---

## 3. How it works (ReAct loop)

For every message you send, the agent repeats:

1. **Thought** — the model decides what it needs to do next.
2. **Action** — it calls one of three tools:
   - `search_movie_title(title)` — look up a specific movie (by name you gave, or one the model itself recalled as a good fit for your mood).
   - `discover_by_mood(keyword)` — optional keyword-based discovery via TMDB.
   - `get_availability(movie_id)` — check where a movie is streaming.
3. **Observation** — the tool's result is fed back to the model.
4. It repeats this until it has enough to answer, then gives you a short final recommendation.

All of this prints live to the terminal so you can see the reasoning:
```
🧠 THOUGHT: model wants to call 1 tool(s)
⚡ ACTION: search_movie_title({'title': 'Hereditary'})
👁️ OBSERVATION: {"id": "tt7784604", "title": "Hereditary", "year": "2018", "source": "omdb"}
```

**Short-term memory:** the agent remembers your whole conversation (up to the last 6 exchanges) so it won't repeat a movie it already suggested, and understands follow-ups like "something lighter than that."

**Loop safety:** each message gets at most 4 rounds of tool calls before the agent is forced to answer with whatever it already has — so it can never spin forever or blow up your API quota on one message.

---

## 4. Why three data sources?

Each tool tries sources in this order, falling through only on failure:

```
search_movie_title:   TMDB  →  OMDb  →  local dataset (fallback_data.py)
discover_by_mood:     TMDB  →  local dataset
get_availability:     TMDB  →  local dataset
```

**Why OMDb?** TMDB (`themoviedb.org`) has a documented history of being blocked on some ISPs (notably in India, via anti-piracy court orders that mistakenly flag it). OMDb is a completely different provider/domain, so it isn't affected by that specific block — it gives the agent a genuine second chance at live data before ever touching the offline dataset.

**Why the local dataset?** So a demo never dies mid-conversation. If both live sources are unreachable, the agent still produces a coherent, on-topic response using a small curated set of ~29 well-known movies across 18 mood/genre categories. You'll see this flagged clearly in the terminal:
```
⚠️  TMDB unreachable — using offline fallback for mood 'horror'
```
This is intentional and visible — nothing is silently faked. If you don't set `OMDB_API_KEY`, everything still works; it just skips straight from TMDB to the local dataset.

---

## 5. Troubleshooting

**"network error after retry: timed out" / "Connection reset by peer"**
This is a network-level issue (often an ISP or firewall block of `themoviedb.org`), not your code or key. Try:
- A different network (mobile hotspot, VPN)
- Switching DNS to `1.1.1.1`
- Just continuing — the agent will fall back to OMDb, then local data, automatically

**A quota/rate-limit error from the Gemini API**
Free-tier Gemini keys have a daily request cap (e.g. 20 requests/day for some models). If you hit it, the agent will now tell you plainly instead of crashing. Wait for the quota to reset, or use a key with billing enabled.

**"Movie not found" from `search_movie_title`**
Means the title genuinely doesn't match anything on any of the three sources — try a different title or check spelling.

**Nothing happens / import errors on startup**
Make sure you ran `pip install -r requirements.txt` and that `.env` is in the same folder as `main.py`.

---

## 6. Example session

```
Agent: What kind of mood are you in? (or name a movie)

You: I want a good gothic horror movie

🧠 THOUGHT: model wants to call 1 tool(s)
⚡ ACTION: search_movie_title({'title': 'Crimson Peak'})
👁️ OBSERVATION: {"id": "232181", "title": "Crimson Peak", "year": "2015", "source": "tmdb"}

🧠 THOUGHT: model wants to call 1 tool(s)
⚡ ACTION: get_availability({'movie_id': '232181'})
👁️ OBSERVATION: {"free": [], "subscription": [], "rent": ["Amazon Video", "Apple TV"], "source": "tmdb"}

Agent: Crimson Peak (2015) is a great gothic horror pick — a young woman is
drawn into a decaying, haunted mansion. It's not free right now, but you can
rent it on Amazon Video or Apple TV.
```
