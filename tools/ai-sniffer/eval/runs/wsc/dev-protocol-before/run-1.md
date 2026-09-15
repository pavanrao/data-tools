```json
{
 "findings": [
  {
   "line": 21,
   "habit": null,
   "severity": "n/a",
   "quote": "just",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 23,
   "habit": null,
   "severity": "n/a",
   "quote": "actually",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 36,
   "habit": null,
   "severity": "n/a",
   "quote": "just",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 53,
   "habit": null,
   "severity": "n/a",
   "quote": "actually",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 56,
   "habit": null,
   "severity": "n/a",
   "quote": "actually",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 91,
   "habit": null,
   "severity": "n/a",
   "quote": "reasonably",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 134,
   "habit": null,
   "severity": "n/a",
   "quote": "simply",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 141,
   "habit": null,
   "severity": "n/a",
   "quote": "just",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 167,
   "habit": null,
   "severity": "n/a",
   "quote": "rather",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 173,
   "habit": null,
   "severity": "n/a",
   "quote": "nearly",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 174,
   "habit": null,
   "severity": "n/a",
   "quote": "a lot",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 195,
   "habit": null,
   "severity": "n/a",
   "quote": "normally",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 219,
   "habit": null,
   "severity": "n/a",
   "quote": "rather",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 226,
   "habit": null,
   "severity": "n/a",
   "quote": "rather",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 228,
   "habit": null,
   "severity": "n/a",
   "quote": "a lot",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 41,
   "habit": null,
   "severity": "n/a",
   "quote": "is locked",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 46,
   "habit": null,
   "severity": "n/a",
   "quote": "is kept",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 108,
   "habit": null,
   "severity": "n/a",
   "quote": "is entirely predicted",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 118,
   "habit": null,
   "severity": "n/a",
   "quote": "was published",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 233,
   "habit": null,
   "severity": "n/a",
   "quote": "was written",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 247,
   "habit": null,
   "severity": "n/a",
   "quote": "was made",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 248,
   "habit": null,
   "severity": "n/a",
   "quote": "was copied",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 249,
   "habit": null,
   "severity": "n/a",
   "quote": "were probed",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 40,
   "habit": null,
   "severity": "n/a",
   "quote": "Separate\nconnections matter more than they look: one that has answered `discover` is locked\ninto the new protocol, so asking it for a handshake afterwards tells you about the\nlock and nothing about the server.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 164,
   "habit": null,
   "severity": "n/a",
   "quote": "The\nPython v1 SDK models incoming requests as a closed set of known types, which fits the\nunknown method failing validation before anything routes it — though I haven't traced\nthat path through the v1 source, so I'd call it the likely mechanism rather than a\nproven one.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 170,
   "habit": null,
   "severity": "n/a",
   "quote": "Fall back to the old\nhandshake only when you see `-32601`, which is the obvious reading of the spec, and\nevery Python v1 server in this table — dbt Labs' included — looks like a server that\nwon't talk to you at all.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 188,
   "habit": null,
   "severity": "n/a",
   "quote": "The SDK reports a dead server process as an error with the code `-32000` and the\nmessage \"Connection closed\", and my probe treated every SDK error as the server saying\nno.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 243,
   "habit": null,
   "severity": "n/a",
   "quote": "Its design record,\n  <code>docs/011_discover-probe.md</code>, has the full table with versions and the\n  corrections to what I first wrote down, and the raw measurement is in\n  <code>evidence/discover-probe.jsonl</code>.</p>\n  <p><strong>How this was made.</strong> <code>discover-probe</code> and this write-up\n  were both built with Claude Code.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 248,
   "habit": null,
   "severity": "n/a",
   "quote": "Every piece of terminal output here was copied from\n  a run on 14 September 2026, and all twelve servers were probed on the same build of\n  the tool.</p>\n  <p>Written against MCP protocol revision 2026-07-28.</p>\n</div>",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 14,
   "habit": null,
   "severity": "n/a",
   "quote": "specification",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 15,
   "habit": null,
   "severity": "n/a",
   "quote": "connection",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 29,
   "habit": null,
   "severity": "n/a",
   "quote": "negotiation",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 40,
   "habit": null,
   "severity": "n/a",
   "quote": "connection",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 52,
   "habit": null,
   "severity": "n/a",
   "quote": "reference",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 117,
   "habit": null,
   "severity": "n/a",
   "quote": "reference",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 166,
   "habit": null,
   "severity": "n/a",
   "quote": "validation",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 173,
   "habit": null,
   "severity": "n/a",
   "quote": "negotiation",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 189,
   "habit": null,
   "severity": "n/a",
   "quote": "Connection",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 236,
   "habit": null,
   "severity": "n/a",
   "quote": "reference",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 245,
   "habit": null,
   "severity": "n/a",
   "quote": "measurement",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 108,
   "habit": null,
   "severity": "n/a",
   "quote": "entirely",
   "rule": "adverbs",
   "why": ""
  },
  {
   "line": 112,
   "habit": null,
   "severity": "n/a",
   "quote": "necessarily",
   "rule": "adverbs",
   "why": ""
  },
  {
   "line": 190,
   "habit": null,
   "severity": "n/a",
   "quote": "precisely",
   "rule": "adverbs",
   "why": ""
  },
  {
   "line": 200,
   "habit": null,
   "severity": "n/a",
   "quote": "genuinely",
   "rule": "adverbs",
   "why": ""
  },
  {
   "line": 117,
   "habit": null,
   "severity": "n/a",
   "quote": "showcase",
   "rule": "aiTells",
   "why": ""
  }
 ]
}
```
