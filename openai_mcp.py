"""Claude Code <-> OpenAI 연결용 최소 MCP 서버 (stdio, 표준 라이브러리만 사용).

도구: generate_image(prompt, size?, output?) -> 이미지를 파일로 저장
환경변수: OPENAI_API_KEY, OPENAI_IMAGE_MODEL
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

TOOL = {
    "name": "generate_image",
    "description": "OpenAI 이미지 모델로 이미지를 생성해 파일로 저장합니다.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "이미지 생성 프롬프트"},
            "size": {"type": "string", "default": "1024x1536"},
            "output": {"type": "string", "default": "output/image.png"},
        },
        "required": ["prompt"],
    },
}


def generate(args):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    model = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.5-sunburst")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({"model": model, "prompt": args["prompt"],
                         "size": args.get("size", "1024x1536"), "n": 1}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API 오류 {e.code} (model={model}): {e.read().decode()}")
    out = args.get("output", "output/image.png")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(data["data"][0]["b64_json"]))
    return f"저장됨: {out} (model={model})"


def reply(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    msg["error" if error else "result"] = error or result
    print(json.dumps(msg), flush=True)


for line in sys.stdin:
    if not line.strip():
        continue
    m = json.loads(line)
    method, id_ = m.get("method"), m.get("id")
    if method == "initialize":
        reply(id_, {"protocolVersion": m["params"].get("protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "openai", "version": "0.1.0"}})
    elif method == "tools/list":
        reply(id_, {"tools": [TOOL]})
    elif method == "tools/call":
        try:
            text, bad = generate(m["params"].get("arguments", {})), False
        except Exception as e:
            text, bad = str(e), True
        reply(id_, {"content": [{"type": "text", "text": text}], "isError": bad})
    elif id_ is not None:
        reply(id_, error={"code": -32601, "message": f"Unknown method: {method}"})
