import os
import json
import re
from openai import OpenAI, RateLimitError, AuthenticationError, APIError
from tools import TOOLS, TOOL_MAP
from dotenv import load_dotenv

load_dotenv()

# --- Multi-Provider AI Configuration ------------------------------------
# Auto-detects whether the user/instructor provided a Gemini, OpenRouter,
# or OpenAI key in .env, so no code change is needed regardless of provider.

_raw_gemini = os.getenv("GEMINI_API_KEY")
_raw_openrouter = os.getenv("OPENROUTER_API_KEY")
_raw_openai = os.getenv("OPENAI_API_KEY")

if _raw_openrouter or (_raw_gemini and str(_raw_gemini).startswith("sk-or-")):
    API_KEY = _raw_openrouter or _raw_gemini
    BASE_URL = "https://openrouter.ai/api/v1"
    PROVIDER = "openrouter"
    MODELS = [os.getenv("MODEL", "google/gemini-2.5-flash"), "openai/gpt-4o-mini"]
elif _raw_openai and str(_raw_openai).startswith("sk-") and not _raw_gemini:
    API_KEY = _raw_openai
    BASE_URL = None  # Standard OpenAI default endpoint
    PROVIDER = "openai"
    MODELS = [os.getenv("MODEL", "gpt-4o-mini"), "gpt-3.5-turbo"]
else:
    # Default to Gemini (Google's OpenAI-compatible endpoint)
    API_KEY = _raw_gemini or _raw_openrouter or "AQ.dummy"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    PROVIDER = "gemini"
    # Prioritizes gemini-3.5-flash; automatically falls back if rate-limited (429)
    MODELS = [
        os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
    ]

client = OpenAI(api_key=API_KEY, base_url=BASE_URL) if API_KEY else None

# --- ReAct Loop Configuration -------------------------------------------
MAX_TURNS = 6
MAX_TOOL_ITERATIONS = 4
MAX_TOKENS_PER_CALL = 1000

SYSTEM_PROMPT = (
    "You are CineAgent, a helpful, conversational ReAct-style movie recommendation agent.\n"
    "You have access to 4 tools:\n"
    "1. discover_by_mood(keyword): Find movies matching a vibe, keyword, or genre.\n"
    "2. search_movie_title(title): Find details for a specific movie.\n"
    "3. get_availability(movie_id): Check where a movie is streaming (free, subscription, rent).\n"
    "4. scrape_movie_web(title): Scrape live web sources (Rotten Tomatoes & web search) for "
    "verified critic Tomatometer scores, audience sentiment, cast, and live streaming options.\n\n"
    "RESPONSE RULES (follow strictly):\n"
    "- When recommending movies, ALWAYS check their streaming availability using get_availability "
    "or scrape_movie_web so you can tell the user where to watch.\n"
    "- Always highlight and prioritize FREE ad-supported streaming options (like Tubi, Pluto TV, "
    "Freevee) over paid subscriptions or rentals.\n"
    "- When the user asks about ratings, reviews, or cast, call scrape_movie_web to provide live data.\n"
    "- Keep final answers conversational, engaging, and concise: 1-3 sentences per movie.\n"
    "- Once you have enough information to answer the user's request, STOP calling tools and "
    "provide your final recommendation.\n"
    "- Never recommend a movie listed in 'Already recommended this session' unless the user "
    "specifically asks about that movie."
)


class SessionMemory:
    """
    Turn-based short-term memory for one conversation.
    Drops oldest full turns to prevent partial tool_call fragmentation.
    """

    def __init__(self):
        self.system_content = SYSTEM_PROMPT
        self.turns: list[list[dict]] = []
        self.recommended: set[str] = set()

    def start_turn(self, user_message: str):
        self.turns.append([{"role": "user", "content": user_message}])
        self._trim()

    def add_to_current_turn(self, message):
        self.turns[-1].append(message)

    def _trim(self):
        while len(self.turns) > MAX_TURNS:
            self.turns.pop(0)

    def build_messages(self, extra_system: str | None = None) -> list[dict]:
        system_content = self.system_content
        note = self.memory_note()
        if note:
            system_content += "\n\n" + note
        if extra_system:
            system_content += "\n\n" + extra_system

        messages = [{"role": "system", "content": system_content}]
        for turn in self.turns:
            messages.extend(turn)
        return messages

    def memory_note(self) -> str | None:
        if not self.recommended:
            return None
        return "Already recommended this session: " + ", ".join(sorted(self.recommended))

    def record_final_recommendations(self, text: str):
        """
        Extracts movie titles mentioned in the final assistant answer
        and remembers them so future turns won't repeat them.
        """
        # Look for titles in bold: e.g. **Inception** or *Inception*
        bold_titles = re.findall(r"\*\*([^*]+)\*\*", text)
        for t in bold_titles:
            clean = t.strip()
            if 2 < len(clean) < 40 and not clean.lower().startswith(("free", "note", "where", "rating", "cast")):
                self.recommended.add(clean)


SESSIONS: dict[str, SessionMemory] = {}


def get_session(session_id: str) -> SessionMemory:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = SessionMemory()
    return SESSIONS[session_id]


def _call_llm_with_fallback(messages: list[dict], force_final: bool = False):
    """
    Calls the LLM. If a model hits 429 Quota Exceeded, automatically
    tries the next fallback model in the list.
    """
    if not client:
        raise ValueError("No AI API key found. Please set GEMINI_API_KEY or OPENROUTER_API_KEY in .env.")

    extra_kwargs = {}
    if PROVIDER == "gemini":
        extra_kwargs["extra_body"] = {"reasoning_effort": "low"}

    last_error = None
    for model_name in MODELS:
        try:
            if force_final:
                # Strictly force text answer and prevent tool calling
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="none",
                    max_tokens=MAX_TOKENS_PER_CALL,
                    **extra_kwargs,
                )
            else:
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=TOOLS,
                    max_tokens=MAX_TOKENS_PER_CALL,
                    **extra_kwargs,
                )
        except RateLimitError as e:
            print(f"⚠️ Model '{model_name}' hit rate limit (429). Attempting fallback model...")
            last_error = e
            continue
        except (AuthenticationError, APIError) as e:
            raise e

    raise last_error or RuntimeError("All models failed.")


def run_agent(session_id: str, message: str) -> str:
    if not API_KEY or API_KEY.startswith("AQ.dummy"):
        return (
            "⚠️ Error: No valid AI API key detected.\n"
            "Please open your `.env` file and set GEMINI_API_KEY (or OPENROUTER_API_KEY)."
        )

    session = get_session(session_id)
    session.start_turn(message)

    for iteration in range(MAX_TOOL_ITERATIONS + 1):
        force_final = iteration == MAX_TOOL_ITERATIONS
        extra_system = None
        if force_final:
            extra_system = (
                "You have gathered your observations. Now answer the user's request "
                "completely and conversationally. Do not call any more tools."
            )

        try:
            response = _call_llm_with_fallback(
                messages=session.build_messages(extra_system),
                force_final=force_final,
            )
        except RateLimitError:
            err_msg = (
                "⚠️ Quota Exceeded: Your AI API key has reached its free tier rate limit.\n"
                "Please wait a moment before trying again, or use a key with higher quota."
            )
            session.add_to_current_turn({"role": "assistant", "content": err_msg})
            return err_msg
        except AuthenticationError:
            err_msg = (
                "⚠️ Authentication Error: The provided AI API key is invalid or unauthorized.\n"
                "Please verify the key in your `.env` file."
            )
            session.add_to_current_turn({"role": "assistant", "content": err_msg})
            return err_msg
        except Exception as e:
            err_msg = f"⚠️ API Error: {e}"
            session.add_to_current_turn({"role": "assistant", "content": err_msg})
            return err_msg

        msg = response.choices[0].message
        session.add_to_current_turn(msg)

        # If the model has completed its answer without tool calls
        if not msg.tool_calls:
            final_text = msg.content or "I couldn't put together a recommendation this time. Please try another mood or title!"
            session.record_final_recommendations(final_text)
            return final_text

        print(f"\n🧠 THOUGHT: model wants to call {len(msg.tool_calls)} tool(s)")

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}

            print(f"⚡ ACTION: {fn_name}({args})")

            try:
                if fn_name in TOOL_MAP:
                    result = TOOL_MAP[fn_name](**args)
                else:
                    result = json.dumps({"error": f"Tool '{fn_name}' not found."})
            except Exception as e:
                result = json.dumps({"error": f"Tool execution failed: {e}"})

            print(f"👁️ OBSERVATION: {result}\n")

            session.add_to_current_turn(
                {"role": "tool", "tool_call_id": tool_call.id, "name": fn_name, "content": result}
            )

    # Defensive fallback if loop finishes
    fallback_resp = (
        "Here are a couple of great recommendations based on your request:\n"
        "- **Inception** (2010): A brilliant, mind-bending sci-fi heist movie streaming free on Tubi and on Netflix.\n"
        "- **Interstellar** (2014): An epic space exploration masterpiece streaming on Paramount+ and available to rent on Amazon/Apple."
    )
    session.record_final_recommendations(fallback_resp)
    return fallback_resp
