"""Run the reviewer on local models through Ollama, recording what each run cost.

Each request is exactly what `ai-sniffer review` sends: the agent file's prompt, the
linter's report or a line saying there isn't one, and the numbered draft. Drafts are
copied under neutral names first (runs/manifest.json), as for the subagent runs.

Ollama's own counters are kept beside each reply in run-N.meta.json: prompt and output
tokens, seconds for each, and the model's quantization. A prompt that fills the whole
context window is marked truncated, because Ollama drops the start of an over-long
prompt without saying so.

    uv run python tools/ai-sniffer/eval/run_local.py --model qwen2.5:7b --setup qwen2.5-7b
    uv run python tools/ai-sniffer/eval/run_local.py --model qwen2.5:7b \
        --setup qwen2.5-7b+linter --linter

Existing runs are skipped, so an interrupted batch resumes where it stopped.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import sys
import tempfile
import time
import urllib.request
from collections.abc import Callable, Iterator
from pathlib import Path

HERE = Path(__file__).parent
MANIFEST = HERE / "runs" / "manifest.json"
OLLAMA = "http://localhost:11434"
TRUNCATION_MARGIN = 16

Post = Callable[[str, dict], dict]


def ollama_post(path: str, body: dict) -> dict:
    request = urllib.request.Request(
        OLLAMA + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=3600) as response:
        return json.loads(response.read())


def run_one(model: str, request: str, num_ctx: int, post: Post = ollama_post) -> tuple[str, dict]:
    show = post("/api/show", {"model": model})
    started = time.time()
    r = post(
        "/api/chat",
        {
            "model": model,
            "messages": [{"role": "user", "content": request}],
            "stream": False,
            "options": {"num_ctx": num_ctx},
        },
    )
    meta = {
        "model": model,
        "parameters": show.get("details", {}).get("parameter_size"),
        "quantization": show.get("details", {}).get("quantization_level"),
        "digest": show.get("digest"),
        "num_ctx": num_ctx,
        "prompt_tokens": r.get("prompt_eval_count", 0),
        "output_tokens": r.get("eval_count", 0),
        "seconds": {
            "prompt": round(r.get("prompt_eval_duration", 0) / 1e9, 1),
            "output": round(r.get("eval_duration", 0) / 1e9, 1),
            "total": round(r.get("total_duration", (time.time() - started) * 1e9) / 1e9, 1),
        },
        "truncated": r.get("prompt_eval_count", 0) >= num_ctx - TRUNCATION_MARGIN,
    }
    return r["message"]["content"], meta


@contextlib.contextmanager
def neutral_inputs(mapping: dict[str, str], source: Path) -> Iterator[Path]:
    """Drafts copied under neutral names, each with its linter report beside it."""
    from ai_sniffer.document import read
    from ai_sniffer.signals import check

    with tempfile.TemporaryDirectory() as tmp:
        inputs = Path(tmp)
        for neutral, real in mapping.items():
            shutil.copyfile(source / real, inputs / neutral)
            report = check(read(inputs / neutral)).to_dict()
            (inputs / f"{neutral}.linter.json").write_text(json.dumps(report), encoding="utf-8")
        yield inputs


def request_for(
    inputs: Path,
    neutral: str,
    linter: bool,
    lines: tuple[int, int] | None = None,
    part: tuple[int, int] | None = None,
) -> str:
    from ai_sniffer.review import build_request, load_prompt

    report = None
    if linter:
        report = json.loads((inputs / f"{neutral}.linter.json").read_text(encoding="utf-8"))
    return build_request(load_prompt(), inputs / neutral, report, lines=lines, part=part)


def run_chunked(
    model: str, inputs: Path, neutral: str, linter: bool, num_ctx: int, post: Post
) -> tuple[str, dict]:
    """One request per section; the replies merged into a single reply the scorer reads."""
    from ai_sniffer.review import ReplyError, chunk_ranges, parse_reply

    ranges = chunk_ranges(inputs / neutral)
    findings, summaries, metas, unparseable = [], [], [], 0
    for k, lines in enumerate(ranges, 1):
        reply, meta = run_one(
            model, request_for(inputs, neutral, linter, lines, (k, len(ranges))), num_ctx, post
        )
        metas.append(meta)
        try:
            f, _, summary = parse_reply(reply)
        except ReplyError:
            unparseable += 1
            continue
        findings += f
        summaries.append(f"Lines {lines[0]} to {lines[1]}: {summary}")
    merged = "```json\n" + json.dumps({"findings": findings}, ensure_ascii=False, indent=1)
    merged += "\n```\n\n" + "\n\n".join(summaries) + "\n"
    meta = {
        **metas[0],
        "chunks": len(ranges),
        "unparseable_chunks": unparseable,
        "prompt_tokens": sum(m["prompt_tokens"] for m in metas),
        "output_tokens": sum(m["output_tokens"] for m in metas),
        "seconds": {
            key: round(sum(m["seconds"][key] for m in metas), 1)
            for key in ("prompt", "output", "total")
        },
        "truncated": any(m["truncated"] for m in metas),
    }
    return merged, meta


def run_setup(
    setup: str,
    model: str,
    mapping: dict[str, str],
    source: Path,
    runs_dir: Path,
    run_numbers: list[int],
    linter: bool,
    num_ctx: int,
    post: Post = ollama_post,
    chunk: bool = False,
) -> int:
    written = 0
    with neutral_inputs(mapping, source) as inputs:
        for n in run_numbers:
            for neutral, real in mapping.items():
                out = runs_dir / setup / real.split(".")[0]
                if (out / f"run-{n}.md").exists():
                    continue
                if chunk:
                    reply, meta = run_chunked(model, inputs, neutral, linter, num_ctx, post)
                else:
                    reply, meta = run_one(
                        model, request_for(inputs, neutral, linter), num_ctx, post
                    )
                out.mkdir(parents=True, exist_ok=True)
                (out / f"run-{n}.md").write_text(reply, encoding="utf-8")
                meta |= {
                    "setup": setup,
                    "draft": real,
                    "neutral_name": neutral,
                    "run": n,
                    "linter": linter,
                }
                (out / f"run-{n}.meta.json").write_text(
                    json.dumps(meta, indent=2) + "\n", encoding="utf-8"
                )
                written += 1
                print(
                    f"{setup} run {n} {real}: "
                    f"{meta['prompt_tokens']} + {meta['output_tokens']} tokens, "
                    f"{meta['seconds']['total']}s" + ("  TRUNCATED" if meta["truncated"] else ""),
                    flush=True,
                )
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", required=True, help="an Ollama model name, e.g. qwen2.5:7b")
    parser.add_argument("--setup", required=True, help="directory name under runs/")
    parser.add_argument("--linter", action="store_true", help="send the linter's report")
    parser.add_argument("--runs", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--chunk", action="store_true", help="one request per section")
    args = parser.parse_args(argv)

    mapping = json.loads(MANIFEST.read_text(encoding="utf-8"))["neutral_names"]
    written = run_setup(
        args.setup,
        args.model,
        mapping,
        HERE / "drafts",
        HERE / "runs",
        args.runs,
        args.linter,
        args.num_ctx,
        chunk=args.chunk,
    )
    print(f"{written} runs written for {args.setup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
