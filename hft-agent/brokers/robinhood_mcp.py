"""Read-only Robinhood Agentic Trading MCP inspector.

Connects with the official MCP SDK (streamable HTTP + OAuth in your browser), lists the
tools Robinhood actually exposes and saves their input schemas to state/robinhood_tools.json.
It never places orders: execution goes through Claude with your confirmation (see
.claude/skills/robinhood-rebalance). Robinhood may not allow OAuth from third-party
clients; if sign-in fails, use the Claude path, which Robinhood supports directly.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp.shared.auth import AuthorizationCodeResult, OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from engine.config import STATE_DIR

DEFAULT_URL = "https://agent.robinhood.com/mcp/trading"
CALLBACK_PORT = 8765
TOKEN_FILE = STATE_DIR / "robinhood_oauth.json"
TOOLS_FILE = STATE_DIR / "robinhood_tools.json"


class FileTokenStorage(TokenStorage):
    """Stores OAuth tokens in state/ (git-ignored) with owner-only permissions."""

    def _read(self) -> dict:
        return json.loads(TOKEN_FILE.read_text()) if TOKEN_FILE.exists() else {}

    def _write(self, data: dict) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(data))
        os.chmod(TOKEN_FILE, 0o600)

    async def get_tokens(self) -> OAuthToken | None:
        t = self._read().get("tokens")
        return OAuthToken(**t) if t else None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._write({**self._read(), "tokens": tokens.model_dump(mode="json")})

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        c = self._read().get("client")
        return OAuthClientInformationFull(**c) if c else None

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._write({**self._read(), "client": client_info.model_dump(mode="json")})


class _Callback:
    def __init__(self) -> None:
        self.result: dict[str, str] = {}
        self.done = threading.Event()

    def serve(self) -> HTTPServer:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                q = parse_qs(urlparse(self.path).query)
                outer.result = {k: v[0] for k, v in q.items()}
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h3>Signed in. You can close this tab.</h3>")
                outer.done.set()

            def log_message(self, *args) -> None:
                pass

        server = HTTPServer(("127.0.0.1", CALLBACK_PORT), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server


async def inspect_tools(url: str = DEFAULT_URL) -> list[dict]:
    cb = _Callback()
    server = cb.serve()

    async def redirect(auth_url: str) -> None:
        print(f"Opening browser to sign in to Robinhood:\n{auth_url}")
        webbrowser.open(auth_url)

    async def callback() -> AuthorizationCodeResult:
        await asyncio.to_thread(cb.done.wait, 300)
        if "code" not in cb.result:
            raise RuntimeError(f"OAuth sign-in did not complete: {cb.result or 'timed out'}")
        return AuthorizationCodeResult(code=cb.result["code"], state=cb.result.get("state"), iss=cb.result.get("iss"))

    oauth = OAuthClientProvider(
        server_url=url,
        client_metadata=OAuthClientMetadata(
            client_name="hft-agent read-only inspector",
            redirect_uris=[f"http://127.0.0.1:{CALLBACK_PORT}/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
        ),
        storage=FileTokenStorage(),
        redirect_handler=redirect,
        callback_handler=callback,
    )
    try:
        async with create_mcp_http_client(auth=oauth) as http:
            async with streamable_http_client(url, http_client=http) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    result = await session.list_tools()
    finally:
        server.shutdown()

    tools = [
        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
        for t in result.tools
    ]
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    TOOLS_FILE.write_text(json.dumps(tools, indent=2))
    return tools
