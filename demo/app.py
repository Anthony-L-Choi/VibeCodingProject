"""
oled-luminance MCP 실제 흐름 테스트용 웹페이지.

사용자 프롬프트(자연어) → [이 앱이 흉내내는 "에이전트"] 규칙 기반 파서로
14개 필드를 추출 → 실제 MCP HTTP 프로토콜로 mcp_server/server.py의
predict_luminance Tool을 호출 → 원본 JSON 응답을 받아 자연어 요약으로 반환.

에이전트의 "자연어 이해" 부분만 정규식 파서로 대체했을 뿐, MCP 서버 호출은
.mcp.json에 등록된 것과 동일한 실제 URL(http://127.0.0.1:8090/mcp)에 매 요청마다
새로 접속한다. Claude Code도 HTTP 서버는 대신 실행해주지 않으므로, 이 데모도
서버를 직접 띄우지 않는다 — 먼저 `py -3.12 mcp_server/server.py`로 실행해둬야 한다.

실행: py -3.12 demo/app.py  (기본 포트 8765, localhost 전용)
"""

import asyncio
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Windows 콘솔 기본 코드페이지(cp949)는 이모지/em-dash 같은 유니코드 문자를
# 못 받아 print()가 UnicodeEncodeError로 죽는다 — stdout/stderr을 UTF-8로 강제한다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from fastmcp import Client

# .mcp.json에 등록된 것과 동일한 URL.
MCP_URL = "http://127.0.0.1:8090/mcp"

STRING_FIELDS = ["host_material_id", "dopant_material_id"]
NUMBER_FIELDS = [
    "host_homo",
    "host_lumo",
    "host_t1",
    "host_s1",
    "dopant_homo",
    "dopant_lumo",
    "dopant_t1",
    "dopant_s1",
    "eml_thickness_nm",
    "dopant_concentration_percent",
    "voltage_v",
    "current_density_ma_cm2",
]
ALL_FIELDS = STRING_FIELDS + NUMBER_FIELDS


def parse_prompt(prompt: str) -> dict:
    """규칙 기반 파서 (실제 LLM 아님): 'field_name: value' 또는 'field_name=value'
    형태로 프롬프트에 적힌 14개 필드를 찾아낸다. 못 찾은 필드는 None으로 남겨
    MCP 서버 자체의 VALIDATION_ERROR 경로를 그대로 타게 한다."""
    values = {}
    for field in ALL_FIELDS:
        match = re.search(rf"{field}\s*[:=]\s*([^\s,;]+)", prompt, re.IGNORECASE)
        if not match:
            values[field] = None
            continue
        raw = match.group(1).strip().strip("\"',")
        if field in STRING_FIELDS:
            values[field] = raw
        else:
            try:
                values[field] = float(raw)
            except ValueError:
                values[field] = None
    return values


async def call_predict_luminance(values: dict) -> dict:
    """실제 MCP HTTP 프로토콜로 predict_luminance Tool을 호출한다.
    서버는 이 데모가 띄우지 않는다 — 이미 떠 있는 서버(MCP_URL)에 매 요청마다 새로 접속한다."""
    async with Client(MCP_URL) as client:
        result = await client.call_tool("predict_luminance", values, raise_on_error=False)
        return result.data


def build_agent_reply(mcp_result: dict) -> str:
    if isinstance(mcp_result, dict) and "error" in mcp_result:
        err = mcp_result["error"]
        details = err.get("details", {})
        return (
            f"요청하신 값으로는 예측할 수 없습니다. "
            f"[{err.get('code')}] {err.get('message')}"
            + (f" (필드: {details.get('field')}, 사유: {details.get('reason')})" if details else "")
        )
    if isinstance(mcp_result, dict) and "luminance_cd_m2" in mcp_result:
        return f"예측된 Luminance는 {mcp_result['luminance_cd_m2']:.2f} cd/m² 입니다."
    return f"알 수 없는 응답: {mcp_result}"


HTML_PAGE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>oled-luminance MCP 흐름 테스트</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, "Segoe UI", sans-serif; max-width: 860px; margin: 40px auto; padding: 0 16px; line-height: 1.5; }
  h1 { font-size: 1.3rem; }
  .flow { font-size: 0.85rem; color: #666; margin-bottom: 8px; }
  .hint { font-size: 0.8rem; color: #888; margin-bottom: 24px; }
  textarea { width: 100%; height: 180px; box-sizing: border-box; font-family: ui-monospace, monospace; font-size: 0.85rem; padding: 8px; }
  button { margin-top: 8px; padding: 8px 20px; font-size: 0.95rem; cursor: pointer; }
  button:disabled { opacity: 0.5; cursor: default; }
  .panel { border: 1px solid #ccc; border-radius: 8px; padding: 12px 16px; margin-top: 16px; }
  .panel h2 { font-size: 0.9rem; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.03em; color: #888; }
  pre { white-space: pre-wrap; word-break: break-all; margin: 0; font-size: 0.85rem; }
  .reply { font-size: 1.05rem; font-weight: 500; }
  .error { color: #c0392b; }
  .missing { color: #c0392b; }
  #status { font-size: 0.85rem; color: #888; margin-top: 8px; }
</style>
</head>
<body>
<h1>oled-luminance MCP 실제 흐름 테스트</h1>
<p class="flow">사용자 프롬프트 → (규칙 기반 파서 = 이 데모의 "에이전트") → 실제 MCP HTTP 호출(predict_luminance) → 응답 → 자연어 요약</p>
<p class="hint">MCP_URL: http://127.0.0.1:8090/mcp — 이 데모는 서버를 대신 띄우지 않는다. 먼저 <code>py -3.12 mcp_server/server.py</code>로 서버를 실행해둬야 한다.</p>

<textarea id="prompt" placeholder="예시:
host_material_id: HOST_001
host_homo: -5.70
host_lumo: -2.60
host_t1: 2.80
host_s1: 3.10
dopant_material_id: DOPANT_001
dopant_homo: -5.50
dopant_lumo: -2.80
dopant_t1: 2.50
dopant_s1: 2.90
eml_thickness_nm: 30.0
dopant_concentration_percent: 8.0
voltage_v: 4.2
current_density_ma_cm2: 10.0"></textarea>
<br>
<button id="run">predict_luminance 실행</button>
<span id="status"></span>

<div class="panel">
  <h2>1. 에이전트가 파싱한 파라미터</h2>
  <pre id="parsed">-</pre>
</div>
<div class="panel">
  <h2>2. MCP 서버(HTTP)의 원본 응답</h2>
  <pre id="raw">-</pre>
</div>
<div class="panel">
  <h2>3. 에이전트의 최종 응답</h2>
  <pre class="reply" id="reply">-</pre>
</div>

<script>
const btn = document.getElementById('run');
const statusEl = document.getElementById('status');
btn.addEventListener('click', async () => {
  const prompt = document.getElementById('prompt').value;
  btn.disabled = true;
  statusEl.textContent = 'MCP 서버 호출 중...';
  document.getElementById('parsed').textContent = '-';
  document.getElementById('raw').textContent = '-';
  document.getElementById('reply').textContent = '-';
  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt})
    });
    const data = await res.json();
    document.getElementById('parsed').innerHTML = Object.entries(data.parsed)
      .map(([k, v]) => `${k}: ${v === null ? '<span class="missing">(추출 실패)</span>' : v}`)
      .join('\\n');
    document.getElementById('raw').textContent = JSON.stringify(data.mcp_result, null, 2);
    const replyEl = document.getElementById('reply');
    replyEl.textContent = data.agent_reply;
    replyEl.className = 'reply' + (data.mcp_result.error ? ' error' : '');
    statusEl.textContent = '완료';
  } catch (e) {
    statusEl.textContent = '오류: ' + e;
  } finally {
    btn.disabled = false;
  }
});
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        body = HTML_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/run":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        prompt = payload.get("prompt", "")

        parsed = parse_prompt(prompt)
        try:
            mcp_result = asyncio.run(call_predict_luminance(parsed))
        except Exception as exc:  # noqa: BLE001 - 데모용 예외를 화면에 그대로 노출
            mcp_result = {
                "error": {
                    "code": "DEMO_CLIENT_ERROR",
                    "message": (
                        f"{MCP_URL} 에 연결할 수 없습니다. 먼저 'py -3.12 mcp_server/server.py'로 "
                        f"서버를 실행해뒀는지 확인하세요. (원본 오류: {exc})"
                    ),
                }
            }
        agent_reply = build_agent_reply(mcp_result)
        self._send_json({"parsed": parsed, "mcp_result": mcp_result, "agent_reply": agent_reply})

    def _send_json(self, response: dict):
        body = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://127.0.0.1:{port} 에서 실행 중 (Ctrl+C로 종료)")
    print(f"MCP_URL={MCP_URL} 서버가 먼저 떠 있어야 한다 (py -3.12 mcp_server/server.py).")
    server.serve_forever()
