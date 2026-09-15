#!/bin/sh
# Chunked local runs, queued behind local-batch.sh. Same models, no linter report.
cd "$(dirname "$0")/../../.." || exit 1
while pgrep -f local-batch.sh > /dev/null; do sleep 60; done
for spec in "qwen2.5:7b qwen2.5-7b+chunks" "llama3.1:latest llama3.1-8b+chunks"; do
  set -- $spec
  uv run python tools/ai-sniffer/eval/run_local.py --model "$1" --setup "$2" --chunk
done
uv run python tools/ai-sniffer/eval/score.py
echo "chunked batch finished $(date)"
