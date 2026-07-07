#!/usr/bin/env python3
import sys
from pathlib import Path

if len(sys.argv) != 4:
    print("Usage: inject_widget.py INDEX_HTML JS_URL CSS_URL", file=sys.stderr)
    raise SystemExit(2)

path = Path(sys.argv[1])
js_url = sys.argv[2]
css_url = sys.argv[3]
text = path.read_text(encoding="utf-8")

marker = "callchat-zero-agent-widget"
if marker in text:
    print("Widget already present")
    raise SystemExit(0)

snippet = f"""
<!-- callchat-zero-agent-widget -->
<link rel="stylesheet" href="{css_url}">
<script>
  window.CallChatZeroAgent = window.CallChatZeroAgent || {{
    endpoint: "/api/zero-agent",
    brand: "CallChat Zero"
  }};
</script>
<script src="{js_url}" defer></script>
<!-- /callchat-zero-agent-widget -->
"""

if "</body>" in text:
    text = text.replace("</body>", snippet + "\n</body>", 1)
else:
    text += snippet

path.write_text(text, encoding="utf-8")
print(f"Injected widget into {path}")
