import json

from composio_mcp import _parse_rpc_body


def test_parses_sse_event():
    body = ': connected\n\nevent: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n\n'
    assert _parse_rpc_body(body) == {"ok": True}


def test_keeps_unicode_line_separators_inside_json():
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"text": "a b\u0085c"}}, ensure_ascii=False)
    assert _parse_rpc_body(f"event: message\ndata: {payload}\n\n")["text"] == "a b\u0085c"


def test_plain_json_body():
    assert _parse_rpc_body('{"jsonrpc":"2.0","id":1,"result":{"x":1}}') == {"x": 1}
