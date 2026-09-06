import os
import json
from openai import OpenAI
from tools import TOOLS, TOOL_MAP
from dotenv import load_dotenv

load_dotenv()

# NOTE: variable name kept as OPENROUTER_API_KEY on purpose — instructor will
# just drop a valid Gemini key into this same .env slot. base_url is Google's
# OpenAI-compatible endpoint, so the SDK works unchanged.
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODEL = "gemini-3.6-flash"

# --- Short-term memory / loop-control config -----------------------------
# MAX_TURNS: how many full (user -> ... -> final answer) exchanges to keep
#            in context. Whole turns are dropped, never partial ones, so a
#            tool_call is never separated from its tool result.
# MAX_TOOL_ITERATIONS: hard cap on how many times the agent may call a tool
#            while answering a SINGLE user message. This is what stops the
#            "keeps going until it errors" behavior — after this many
#            rounds it is forced to answer with whatever it already has.
# MAX_CONSECUTIVE_TOOL_FAILURES: if the network keeps resetting, stop
#            hammering TMDB and tell the user instead of burning the whole
#            iteration budget on retries.
MAX_TURNS = 6
MAX_TOOL_ITERATIONS = 4
MAX_CONSECUTIVE_TOOL_FAILURES = 2
MAX_TOKENS_PER_CALL = 500

SYSTEM_PROMPT = (
    "You are CineAgent, a ReAct-style movie recommendation agent.\n"
    "For every user request: think (Thought), call a tool if needed (Action), "
    "read the result (Observation), then decide if you have enough to answer.\n"
    "RESPONSE RULES (follow these strictly):\n"
    "- Only call as many tools as needed to satisfy the exact request. If the user "
    "asks for 2 movies, stop searching once you have 2 good candidates.\n"
    "- The moment you have enough information, STOP calling tools and give your "
    "final answer. Do not keep searching 'just in case'.\n"
    "- Keep the final answer short and conversational: 1-3 sentences per movie "
    "(title, why it fits, where to watch). No long essays.\n"
    "- Always prioritize FREE / ad-supported (FAST) streaming options over paid "
    "subscriptions or rentals when presenting availability.\n"
    "- Never recommend a movie that appears in the 'Already recommended this "
    "session' list — pick something else instead.\n"
    "- If a tool returns a network error, do NOT retry the same call. Try at most "
    "one different movie/keyword, and if that also fails, stop and tell the user "
    "TMDB seems unreachable right now rather than continuing to search.\n"
    "- Availability results may include a 'note' field saying live data was "
    "unavailable for that title. If present, mention briefly that this is a "
    "best-guess suggestion rather than confirmed availability."
)


class SessionMemory:
    """
    Turn-based short-term memory for one conversation.

    Each "turn" is the full list of messages generated while answering one
    user message: [user_msg, assistant_msg(tool_calls), tool_msg, tool_msg,
    assistant_msg(tool_calls), tool_msg, ..., assistant_msg(final answer)].

    Trimming always drops the OLDEST WHOLE TURN, never a partial slice —
    this guarantees a tool_call is never separated from its tool response,
    which is what silently breaks the API request format if you trim by
    raw message count instead.
    """

    def __init__(self):
        self.system_content = SYSTEM_PROMPT
        self.turns: list[list[dict]] = []
        self.recommended = set()

    def start_turn(self, user_message: str):
        self.turns.append([{"role": "user", "content": user_message}])
        self._trim()

    def add_to_current_turn(self, message: dict):
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

    def memory_note(self):
        if not self.recommended:
            return None
        return "Already recommended this session: " + ", ".join(sorted(self.recommended))

    def remember_titles_from_tool_result(self, fn_name: str, result: str):
        if fn_name not in ("search_movie_title", "discover_by_mood"):
            return
        try:
            parsed = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return
        if isinstance(parsed, list):
            titles = [m.get("title") for m in parsed if isinstance(m, dict) and m.get("title")]
        elif isinstance(parsed, dict) and parsed.get("title"):
            titles = [parsed["title"]]
        else:
            titles = []
        self.recommended.update(titles)


SESSIONS: dict[str, SessionMemory] = {}


def get_session(session_id: str) -> SessionMemory:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = SessionMemory()
    return SESSIONS[session_id]


def _is_network_error(result_json: str) -> bool:
    try:
        parsed = json.loads(result_json)
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(parsed, dict) and str(parsed.get("error", "")).startswith("network error")


def run_agent(session_id: str, message: str) -> str:
    session = get_session(session_id)
    session.start_turn(message)

    consecutive_failures = 0

    for iteration in range(MAX_TOOL_ITERATIONS + 1):
        force_final = iteration == MAX_TOOL_ITERATIONS
        extra_system = None
        if force_final:
            extra_system = (
                "You have used your tool-call budget for this turn. Answer the user "
                "now using only the observations already gathered above. Do not "
                "request any more tool calls."
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=session.build_messages(extra_system),
            tools=None if force_final else TOOLS,
            max_tokens=MAX_TOKENS_PER_CALL,
        )
        msg = response.choices[0].message
        session.add_to_current_turn(msg)

        if not msg.tool_calls:
            return msg.content or "Sorry, I couldn't put together a recommendation this time."

        print(f"\n🧠 THOUGHT: model wants to call {len(msg.tool_calls)} tool(s)")

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}
            print(f"⚡ ACTION: {fn_name}({args})")

            try:
                result = TOOL_MAP[fn_name](**args)
            except Exception as e:
                result = json.dumps({"error": f"tool execution failed: {e}"})

            print(f"👁️ OBSERVATION: {result}\n")

            if _is_network_error(result):
                consecutive_failures += 1
            else:
                consecutive_failures = 0
                session.remember_titles_from_tool_result(fn_name, result)

            session.add_to_current_turn(
                {"role": "tool", "tool_call_id": tool_call.id, "name": fn_name, "content": result}
            )

        if consecutive_failures >= MAX_CONSECUTIVE_TOOL_FAILURES:
            bail_msg = (
                "I'm having trouble reaching TMDB right now — the connection keeps "
                "getting reset. This is usually a network/ISP block rather than a bug. "
                "Please check your connection or try again shortly."
            )
            session.add_to_current_turn({"role": "assistant", "content": bail_msg})
            return bail_msg

    # Defensive fallback — should rarely trigger since force_final has tools=None.
    return "I got stuck trying to find that one — could you rephrase, or name a different movie/mood?"
