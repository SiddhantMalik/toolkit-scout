"""Minimal client for Composio Connect MCP (https://connect.composio.dev/mcp).

Auth: a Connect consumer key (ck_...) in the COMPOSIO_CONSUMER_KEY env var, sent as
x-consumer-api-key. The key is never written to disk by this module.

Usage as a library:
    mcp = ComposioMCP()
    mcp.search_tools("fetch the text of a public web page")
    mcp.execute([{"tool_slug": "...", "arguments": {...}}])
"""
import json
import os

import requests

URL = "https://connect.composio.dev/mcp"


class ComposioError(RuntimeError):
    pass


class ComposioMCP:
    def __init__(self, key=None, timeout=180):
        self.key = key or os.environ.get("COMPOSIO_CONSUMER_KEY")
        if not self.key:
            raise ComposioError("set COMPOSIO_CONSUMER_KEY to your Composio Connect key (ck_...)")
        self.timeout = timeout
        self.session_id = None   # Composio meta-tool session (not the MCP transport session)
        self._next_id = 0
        self._rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "toolkit-scout", "version": "1"}})

    def _rpc(self, method, params):
        self._next_id += 1
        resp = requests.post(URL, timeout=self.timeout, headers={
            "x-consumer-api-key": self.key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }, json={"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params})
        if resp.status_code != 200:
            raise ComposioError(f"{method}: HTTP {resp.status_code} {resp.text[:200]}")
        return _parse_rpc_body(resp.content.decode("utf-8"))   # SSE has no charset header; it is UTF-8

    def call_tool(self, name, arguments):
        """Call one MCP tool and return its JSON payload (the text content, parsed)."""
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text, "isError": result.get("isError", False)}

    def search_tools(self, use_case, strategy="auto"):
        session = {"id": self.session_id} if self.session_id else {"generate_id": True}
        out = self.call_tool("COMPOSIO_SEARCH_TOOLS", {
            "queries": [{"use_case": use_case}], "session": session, "search_strategy": strategy})
        self.session_id = (out.get("data") or {}).get("session", {}).get("id", self.session_id)
        return out

    def execute(self, tools, thought="fetch developer docs"):
        """Run up to 50 independent tool calls; returns the list of per-tool results."""
        args = {"tools": tools, "sync_response_to_workbench": False, "thought": thought}
        if self.session_id:
            args["session_id"] = self.session_id
        out = self.call_tool("COMPOSIO_MULTI_EXECUTE_TOOL", args)
        return (out.get("data") or {}).get("results", []), out


def _parse_rpc_body(body):
    """The server answers as SSE or plain JSON; return the JSON-RPC result.

    In SSE an event's payload may span several 'data:' lines, which are joined with newlines.
    """
    events, current = [], []
    for line in body.split("\n"):   # not splitlines(): it also breaks on U+2028 etc. inside JSON strings
        if line.startswith("data:"):
            current.append(line[5:].removeprefix(" "))
        elif not line.strip() and current:
            events.append("\n".join(current))
            current = []
    if current:
        events.append("\n".join(current))
    for raw in events or [body]:
        msg = json.loads(raw)
        if "error" in msg:
            raise ComposioError(json.dumps(msg["error"])[:300])
        if "result" in msg:
            return msg["result"]
    raise ComposioError("no JSON-RPC result in response")
