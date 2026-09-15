#!/bin/sh
# Local eval batch: two installed models, with and without the linter report, three runs each.
cd "$(dirname "$0")/../../.." || exit 1
for spec in "qwen2.5:7b qwen2.5-7b" "llama3.1:latest llama3.1-8b"; do
  set -- $spec
  uv run python tools/ai-sniffer/eval/run_local.py --model "$1" --setup "$2"
  uv run python tools/ai-sniffer/eval/run_local.py --model "$1" --setup "$2+linter" --linter
done
uv run python tools/ai-sniffer/eval/score.py
echo "batch finished $(date)"
