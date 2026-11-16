"""OpenAI 이미지 생성 스크립트 (표준 라이브러리만 사용).

환경변수: OPENAI_API_KEY (필수), OPENAI_IMAGE_MODEL (기본: gpt-image-2.6-sunburst)
사용법:   python generate_image.py "프롬프트" [출력파일] [크기]
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.6-sunburst")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    prompt = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "output/image.png"
    size = sys.argv[3] if len(sys.argv) > 3 else "1024x1536"

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({"model": MODEL, "prompt": prompt, "size": size, "n": 1}).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API 오류 {e.code} (model={MODEL}): {e.read().decode()}")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(data["data"][0]["b64_json"]))
    print(f"저장됨: {out} (model={MODEL})")


if __name__ == "__main__":
    main()
