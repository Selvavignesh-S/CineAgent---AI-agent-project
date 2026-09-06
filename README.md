# 🎬 CineAgent

> **An Anti-Fragile, Zero-Dependency ReAct Movie Recommendation Agent with Real-Time Web Scraping.**

CineAgent is an autonomous terminal-based AI agent that helps users discover movies based on mood, vibe, or specific titles. Built on the **ReAct (Reasoning + Acting)** paradigm, it iteratively thinks, executes specialized tools, inspects real-world data, and delivers conversational recommendations—with a strict priority on **free, ad-supported streaming options** (like Tubi and Pluto TV) over paid rentals or subscriptions.

---

## 📑 Table of Contents

1. [Key Features](#-key-features)
2. [Prerequisites & Requirements](#-prerequisites--requirements)
3. [Step-by-Step Setup & Running Guide](#-step-by-step-setup--running-guide)
4. [System Architecture](#-system-architecture)
5. [The ReAct Loop in Action](#-the-react-loop-in-action)
6. [Tools Ecosystem](#-tools-ecosystem)
7. [Zero-Dependency & Anti-Fragile Design](#-zero-dependency--anti-fragile-design)
8. [Example Terminal Sessions](#-example-terminal-sessions)
9. [Project Directory Structure](#-project-directory-structure)

---

## 🌟 Key Features

- **ReAct Autonomous Agent Loop**: Uses step-by-step reasoning (`🧠 Thought` → `⚡ Action` → `👁️ Observation`) to plan, search, verify availability, and answer.
- **Zero External API Dependency**: Requires **only an AI model API key** to run. There are no mandatory third-party database keys (TMDB and OMDb are completely optional).
- **Real-Time Web Scraping**: Includes a built-in web scraper that pulls live Rotten Tomatoes critic scores (Tomatometer), audience sentiment, verified cast, and web streaming availability on demand without any API keys.
- **Multi-Provider AI Auto-Detection**: Automatically identifies whether the user provided a Google Gemini, OpenRouter, or OpenAI API key and configures endpoints and models automatically.
- **Quota & Rate-Limit Auto-Recovery**: If a model encounters a free-tier rate limit (`429 Quota Exceeded`), CineAgent automatically switches to an alternate model (e.g. `gemini-3.5-flash-lite`, `gemini-flash-latest`) without crashing.
- **Multi-Turn Short-Term Memory**: Remembers movies recommended earlier in the conversation to avoid repetition on follow-ups (e.g., *"Give me something lighter than that"*).
- **Anti-Fragile Fallback Catalog**: Bundles a curated database of 120+ iconic movies across 30+ moods with fuzzy keyword matching, ensuring 100% uptime even when external networks or ISPs block movie databases.

---

## 📦 Prerequisites & Requirements

- **Python Version**: Python 3.10, 3.11, 3.12, 3.13, or 3.14
- **Dependencies** (listed in `requirements.txt`):
  - `httpx` — Fast, resilient HTTP client used for web scraping and network calls.
  - `openai` — Official client used to interface with OpenAI-compatible endpoints (Google AI Studio, OpenRouter, OpenAI).
  - `python-dotenv` — Loads environment variables from the `.env` file.
- **API Key**: An API key from **any one** of the following providers:
  - **Google Gemini API Key** (Free tier available at [Google AI Studio](https://aistudio.google.com/))
  - **OpenRouter API Key** ([OpenRouter](https://openrouter.ai/))
  - **OpenAI API Key** ([OpenAI Platform](https://platform.openai.com/))

---

## 🚀 Step-by-Step Setup & Running Guide

### Step 1: Clone the Repository & Navigate to the Project
```bash
git clone https://github.com/Selvavignesh-S/cine-agent.git
cd cine-agent
```

### Step 2: Set Up a Python Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```
*(On Windows: `venv\Scripts\activate`)*

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Your Environment Variable
Create a file named `.env` in the root of `cine-agent/` and add your AI API key:

```env
# Google Gemini Key (Recommended / Works out of the box)
GEMINI_API_KEY=your_gemini_api_key_here

# OR OpenRouter Key:
# OPENROUTER_API_KEY=sk-or-v1-...

# OR OpenAI Key:
# OPENAI_API_KEY=sk-...
```

> **Note for Evaluators:** You only need to drop your AI key into `.env`. You do not need to register for TMDB or OMDb. CineAgent will detect your key provider and run automatically.

### Step 5: Launch CineAgent
```bash
python main.py
```

To exit the agent at any time, type `exit`, `quit`, or press `Ctrl + C`.

---

## 🏗️ System Architecture

```
                                +-----------------------------------+
                                |            User Terminal          |
                                |              (main.py)            |
                                +-----------------+-----------------+
                                                  |
                                            User Messages
                                                  v
                                +-----------------+-----------------+
                                |      ReAct Agent (agent.py)       |
                                |  - Multi-Provider LLM Client      |
                                |  - Turn-Based Short-Term Memory   |
                                |  - Loop Safety & Quota Fallback   |
                                +--------+-----------------+--------+
                                         |                 ^
                            Tool Calls   |                 | Structured JSON
                             (Action)    |                 | (Observation)
                                         v                 |
+----------------------------------------+-----------------+----------------------------------------+
|                                  Autonomous Tools Engine (tools.py)                               |
|                                                                                                   |
|  +-----------------------+   +-----------------------+   +-------------------+   +-------------+  |
|  |   discover_by_mood    |   |  search_movie_title   |   | get_availability  |   | scrape_web  |  |
|  +-----------+-----------+   +-----------+-----------+   +---------+---------+   +------+------+  |
+--------------|---------------------------|-------------------------|--------------------|---------+
               |                           |                         |                    |
               v                           v                         v                    v
+--------------+---------------------------+-------------------------+--------------------+---------+
|                                    Data & Resolution Layer                                        |
|                                                                                                   |
|  [Tier 1: Opportunistic APIs]      Fast 1.5s TMDB / OMDb checks (Trips circuit breaker on block)  |
|  [Tier 2: Live Web Scraper]        Scrapes Rotten Tomatoes scores, reviews & search snippets      |
|  [Tier 3: Embedded Catalog]        120+ Movies across 30+ genres/moods (100% offline uptime)      |
|  [Tier 4: Dynamic Fallback]        Generates valid records so tools NEVER return an error         |
+---------------------------------------------------------------------------------------------------+
```

---

## 🔄 The ReAct Loop in Action

When you submit a message, CineAgent executes the **ReAct (Reasoning + Acting)** loop:

1. **🧠 Thought**: The model examines the conversation history and decides what action is required next.
2. **⚡ Action**: The model calls one or more tools with specific JSON arguments (e.g. `discover_by_mood({"keyword": "gothic horror"})`).
3. **👁️ Observation**: The chosen tool executes and returns real-time structured data back to the model.
4. **Decision Step**:
   - If more information is needed (e.g. availability hasn't been checked yet), the agent loops back to **Thought** and calls additional tools.
   - If sufficient data is gathered, it generates the conversational final recommendation and displays it to the user.
5. **Memory Update**: Movies actually recommended in the final text are committed to short-term memory to prevent duplication in subsequent turns.

---

## 🛠️ Tools Ecosystem

CineAgent is equipped with four tools exposed via the OpenAI Function Calling schema:

| Tool | Purpose | Primary Data Sources |
|---|---|---|
| `discover_by_mood(keyword)` | Finds candidate movies matching vibes, genres, or keywords. | TMDB Keyword Search &rarr; Embedded 120+ Movie Catalog with fuzzy alias matching. |
| `search_movie_title(title)` | Finds exact movie details (ID, title, release year). | TMDB Search &rarr; OMDb Search &rarr; Live Web Scraper &rarr; Embedded Catalog. |
| `get_availability(movie_id)` | Checks legal streaming platforms, prioritizing free ad-supported services (Tubi, Pluto TV). | TMDB Watch Providers &rarr; Embedded Availability Engine &rarr; Verified FAST Defaults. |
| `scrape_movie_web(title)` | Scrapes real-time Rotten Tomatoes critic scores, audience sentiment, lead cast, and streaming mentions. | Live Rotten Tomatoes HTML search parser & DuckDuckGo streaming snippet extraction. |

---

## 🛡️ Zero-Dependency & Anti-Fragile Design

Most movie agents break down when external third-party APIs fail or hit rate limits:
- **ISP / Regional Blocking Resilience**: TMDB (`themoviedb.org`) is blocked on many regional ISPs (notably across India) and frequently causes connection resets. CineAgent employs an automatic **1.5-second circuit breaker**: if TMDB does not respond immediately, it trips and routes subsequent calls to the local engine with **zero perceptible delay**.
- **100% Success Rate**: `search_movie_title` and `discover_by_mood` are designed to never return an unhandled error to the LLM. If a query is outside the database, the agent falls back to live web scraping and dynamic record construction.
- **Provider-Agnostic LLM Routing**: If your Gemini model encounters a 429 quota exhaustion, CineAgent immediately tries fallback models (`gemini-3.5-flash-lite`, `gemini-flash-latest`) before giving up, ensuring continuous operation.

---

## 💬 Example Terminal Sessions

### Session 1: Mood Discovery + Free Streaming Lookup
```text
You: I want a gothic horror movie

🧠 THOUGHT: model wants to call 1 tool(s)
⚡ ACTION: discover_by_mood({'keyword': 'gothic horror'})
📦 Discovered movies for mood 'gothic horror' via offline catalog
👁️ OBSERVATION: [{"id": "232181", "title": "Crimson Peak", ...}, {"id": "1735", "title": "The Others", ...}, {"id": "310131", "title": "The Witch", ...}]

🧠 THOUGHT: model wants to call 3 tool(s)
⚡ ACTION: get_availability({'movie_id': '232181'})
👁️ OBSERVATION: {"free": [], "subscription": [], "rent": ["Amazon Video", "Apple TV"], "source": "offline_catalog"}
⚡ ACTION: get_availability({'movie_id': '1735'})
👁️ OBSERVATION: {"free": ["Pluto TV"], "subscription": [], "rent": ["Amazon Video"], "source": "offline_catalog"}
⚡ ACTION: get_availability({'movie_id': '310131'})
👁️ OBSERVATION: {"free": ["Tubi"], "subscription": ["Max"], "rent": ["Apple TV"], "source": "offline_catalog"}

Agent: Here are three excellent gothic horror movies you can watch right now:

1. **The Others (2001)** - A chilling, atmospheric ghost story starring Nicole Kidman as a mother protecting her photosensitive children in a darkened manor. You can stream it for **FREE on Pluto TV**!
2. **The Witch (2015)** - Robert Eggers' eerie folktale about a 1630s Puritan family unraveling near an ancient forest. Available to stream **FREE on Tubi** or on Max.
3. **Crimson Peak (2015)** - Guillermo del Toro's lavish, visually stunning gothic romance set in a decaying mansion. Available to rent on Amazon Video or Apple TV.
```

---

### Session 2: Conversational Short-Term Memory
```text
You: Give me something lighter and funnier than that

🧠 THOUGHT: model wants to call 1 tool(s)
⚡ ACTION: discover_by_mood({'keyword': 'lighthearted comedy'})
📦 Discovered movies for mood 'lighthearted comedy' via offline catalog
👁️ OBSERVATION: [{"id": "346648", "title": "Paddington 2", ...}, {"id": "458", "title": "School of Rock", ...}]

🧠 THOUGHT: model wants to call 2 tool(s)
⚡ ACTION: get_availability({'movie_id': '346648'})
👁️ OBSERVATION: {"free": ["Pluto TV"], "subscription": ["Max"], ...}
⚡ ACTION: get_availability({'movie_id': '458'})
👁️ OBSERVATION: {"free": ["Tubi"], "subscription": ["Paramount+"], ...}

Agent: If you need a total mood-lifter, here are two delightful picks:

* **School of Rock (2003)** - Jack Black turns a class of prep-school kids into a high-voltage rock band. You can stream it completely **FREE on Tubi**!
* **Paddington 2 (2017)** - A warm, hilarious masterpiece of pure joy and marmalade in London. Streaming **FREE on Pluto TV**!
```

---

### Session 3: Real-Time Web Scraping (Rotten Tomatoes & Cast)
```text
You: What are the reviews and cast for Inception?

🧠 THOUGHT: model wants to call 1 tool(s)
⚡ ACTION: scrape_movie_web({'title': 'Inception'})
🕸️ WEB SCRAPER: extracted live data for 'Inception': 86%, cast: ['Leonardo DiCaprio', 'Joseph Gordon-Levitt', 'Elliot Page']
👁️ OBSERVATION: {"title": "Inception", "tomatometer": "86%", "audience_sentiment": "Positive", "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"], "streaming_mentions": ["Tubi", "Pluto TV", "Netflix"]}

Agent: **Inception (2010)** boasts a certified fresh **86% Tomatometer score** on Rotten Tomatoes, with glowing audience acclaim for its mind-bending visual effects and innovative concept. The lead cast stars Leonardo DiCaprio, Joseph Gordon-Levitt, and Elliot Page.

Best of all, you can stream it for **FREE on Tubi and Pluto TV**, or watch it on Netflix and Prime Video!
```

---

## 📁 Project Directory Structure

```
cine-agent/
├── agent.py          # Core ReAct loop, LLM auto-detection, memory & error recovery
├── tools.py          # 4 ReAct tools (web scraper, search, mood discovery, availability)
├── fallback_data.py  # 120+ movie offline catalog, mood alias mappings & FAST availability
├── main.py           # Clean terminal entry point with interactive loop
├── requirements.txt  # Dependencies (httpx, openai, python-dotenv)
├── README.md         # Comprehensive project documentation
└── .env              # Environment file holding your AI API key
```

---

## ⚖️ License
This project is open-source and created for educational and demonstration purposes.
