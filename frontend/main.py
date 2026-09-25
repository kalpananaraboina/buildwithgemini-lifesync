"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.

Why A2A: agents-cli 1.1.0 (GA) deploys ADK agents to Agent Runtime as A2A agents
and no longer registers the reasoning-engine operation schema the old
`agent_engines.get(...).stream_query()` path relied on (operation_schemas() comes
back empty). The container serves the A2A protocol over the Agent Engine HTTP
passthrough, so this proxy fetches the agent's card and sends messages with the
a2a-sdk client (the same path `agents-cli run --mode a2a` uses). This works for
both A2A and plain ADK 1.1.0 deployments (the container serves A2A either way).

Run:
  pip install -r requirements.txt
  export AGENT_ENGINE_RESOURCE_NAME="projects/.../locations/.../reasoningEngines/..."
  export AGENT_DIRECTORY="app"   # your agent's app directory (agents-cli-manifest.yaml)
  python main.py                 # -> http://localhost:8080
"""

import os
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    FilePart,
    Message,
    Part,
    Role,
    TaskArtifactUpdateEvent,
    TextPart,
    TransportProtocol,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ["AGENT_ENGINE_RESOURCE_NAME"]
# The agent's app directory (matches agent_directory in agents-cli-manifest.yaml).
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
# Location is embedded in the resource name: projects/<p>/locations/<loc>/reasoningEngines/<id>.
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

# A2A endpoint for an Agent Runtime deployment, via the Agent Engine HTTP
# passthrough. The card lives at the well-known path under this base.
A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

# The agent tags its A2UI data parts with this mime type.
_A2UI_MIME = "application/json+a2ui"

# One set of ADC credentials, refreshed per request (access tokens expire ~1h).
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    # Always return JSON so the browser never receives a plain-text 500 page
    # (which shows up in the chat as "Unexpected token 'I', "Internal S"... is
    # not valid JSON"). Any server-side failure now surfaces as a readable
    # message in the chat bubble instead.
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}
# Cache the agent card after the first fetch.
_card: AgentCard | None = None


async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        card = AgentCard(**resp.json())
        # Agent Runtime does not serve a public card URL, so point the client at
        # the passthrough base for message sends.
        card.url = A2A_BASE
        _card = card
    return _card


import json
import re

def _extract_parts(parts: list) -> list[dict]:
    """Turn A2A response parts into structured parts for the chat UI.

    Text parts pass through as {"kind": "text"}. A2UI data parts (tagged
    application/json+a2ui or wrapped in <a2a_datapart_json>) become
    {"kind": "a2ui", "data": <message>} so the UI renders the card;
    each data part is one A2UI message (beginRendering or surfaceUpdate).
    """
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        if isinstance(root, TextPart) and getattr(root, "text", None):
            text = root.text
            if "<a2a_datapart_json>" in text:
                parts_found = False
                for chunk in re.findall(r"<a2a_datapart_json>(.*?)</a2a_datapart_json>", text, re.DOTALL):
                    try:
                        data = json.loads(chunk.strip())
                        if isinstance(data, dict):
                            actual_msg = data.get("data", data)
                            out.append({"kind": "a2ui", "data": actual_msg})
                            parts_found = True
                    except Exception:
                        pass
                cleaned_text = re.sub(r"<a2a_datapart_json>.*?</a2a_datapart_json>", "", text, flags=re.DOTALL).strip()
                if cleaned_text:
                    out.append({"kind": "text", "text": cleaned_text})
                elif not parts_found:
                    out.append({"kind": "text", "text": text})
            elif ("beginRendering" in text or "surfaceUpdate" in text):
                parsed = None
                try:
                    parsed = json.loads(text.strip())
                except Exception:
                    try:
                        import ast
                        parsed = ast.literal_eval(text.strip())
                    except Exception:
                        pass
                if isinstance(parsed, dict):
                    actual_msg = parsed.get("data", parsed)
                    out.append({"kind": "a2ui", "data": actual_msg})
                elif isinstance(parsed, list):
                    for msg in parsed:
                        actual_msg = msg.get("data", msg) if isinstance(msg, dict) else msg
                        out.append({"kind": "a2ui", "data": actual_msg})
                else:
                    out.append({"kind": "text", "text": text})
            else:
                out.append({"kind": "text", "text": text})
        elif getattr(root, "data", None) is not None:
            data_val = root.data
            meta = getattr(root, "metadata", None) or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None

            # Attempt to parse stringified or nested A2UI dict
            parsed = data_val
            if isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed.strip())
                except Exception:
                    try:
                        import ast
                        parsed = ast.literal_eval(parsed.strip())
                    except Exception:
                        pass

            if isinstance(parsed, dict) and ("beginRendering" in parsed or "surfaceUpdate" in parsed):
                out.append({"kind": "a2ui", "data": parsed})
            elif isinstance(parsed, dict) and "data" in parsed and isinstance(parsed["data"], dict) and ("beginRendering" in parsed["data"] or "surfaceUpdate" in parsed["data"]):
                out.append({"kind": "a2ui", "data": parsed["data"]})
            elif isinstance(parsed, list):
                for msg in parsed:
                    actual = msg.get("data", msg) if isinstance(msg, dict) else msg
                    out.append({"kind": "a2ui", "data": actual})
            elif mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": data_val})
            else:
                out.append({"kind": "text", "text": str(data_val)})
        elif isinstance(root, FilePart):
            uri = getattr(getattr(root, "file", None), "uri", None)
            if uri:
                out.append({"kind": "text", "text": uri})
    return out


LOCAL_AGENT_URL = os.environ.get("LOCAL_AGENT_URL", "http://127.0.0.1:8080")
_local_sessions: dict[str, str] = {}


async def _chat_local(
    client: httpx.AsyncClient, message: str, user_id: str
) -> list[dict] | None:
    """Forward chat turn to the local agent playground on port 8080 if available."""
    try:
        session_id = _local_sessions.get(user_id)
        if not session_id:
            resp = await client.post(
                f"{LOCAL_AGENT_URL}/apps/app/users/{user_id}/sessions",
                json={},
                timeout=3.0,
            )
            if resp.status_code == 200:
                session_id = resp.json().get("id")
                _local_sessions[user_id] = session_id
            else:
                return None

        run_payload = {
            "appName": "app",
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message}],
            },
        }
        resp = await client.post(
            f"{LOCAL_AGENT_URL}/run",
            json=run_payload,
            timeout=120.0,
        )
        if resp.status_code != 200:
            return None

        events = resp.json()
        parts: list[dict] = []
        import base64

        for ev in events:
            content = ev.get("content") or {}
            for p in content.get("parts") or []:
                if "inlineData" in p:
                    data_b64 = p["inlineData"].get("data", "")
                    try:
                        raw_text = base64.b64decode(data_b64).decode("utf-8")
                        parts.extend(_extract_parts([TextPart(text=raw_text)]))
                    except Exception:
                        pass
                elif "text" in p:
                    parts.extend(_extract_parts([TextPart(text=p["text"])]))
        return parts if parts else None
    except Exception as e:
        logger.debug("Local playground agent call failed: %s", e)
        return None


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    # 1. Try local agent playground first if running locally (not in Cloud Run)
    if not os.getenv("K_SERVICE"):
        try:
            async with httpx.AsyncClient(timeout=120) as local_http:
                local_parts = await _chat_local(local_http, message, user_id)
                if local_parts is not None and len(local_parts) > 0:
                    return JSONResponse({"parts": local_parts})
        except Exception as e:
            logger.debug("Local agent unavailable: %s", e)

    # 2. Deployed cloud agent fallback over A2A
    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        factory = ClientFactory(
            ClientConfig(
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                httpx_client=client,
            )
        )
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text=message))],
            context_id=_contexts.get(user_id),
        )

        last_task = None
        got_artifact_update = False
        async for event in a2a_client.send_message(msg):
            if not isinstance(event, tuple):
                continue
            task, update = event
            if task is not None:
                last_task = task
                if getattr(task, "context_id", None):
                    _contexts[user_id] = task.context_id
            if isinstance(update, TaskArtifactUpdateEvent):
                got_artifact_update = True
                parts.extend(_extract_parts(update.artifact.parts))

        # Non-streaming fallback: pull parts from the final task's artifacts.
        if not got_artifact_update and last_task is not None:
            for artifact in getattr(last_task, "artifacts", None) or []:
                parts.extend(_extract_parts(artifact.parts))

    if not parts:
        # The turn produced no text or UI (e.g. the agent only ran tools, or a
        # tool stalled). Be honest rather than silent.
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Serve the chat UI (keep this mount last so /chat wins).
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
