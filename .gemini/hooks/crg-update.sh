#!/usr/bin/env bash
# code-review-graph: incremental update after write/replace (Gemini CLI hook)
# Must output ONLY JSON on stdout. Low-noise: no systemMessage.
set -euo pipefail

cat > /dev/null || true

code-review-graph update --skip-flows --repo "D:/OneDrive - The Energy and Resources Institute/Desktop/My_Files/Projects/Agentic-RAG-Chatbot" >/dev/null 2>&1 || true
echo '{"suppressOutput": true}'
exit 0
