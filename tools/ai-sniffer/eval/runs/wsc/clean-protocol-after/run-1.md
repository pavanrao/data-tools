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
   "line": 48,
   "habit": null,
   "severity": "n/a",
   "quote": "actually",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 153,
   "habit": null,
   "severity": "n/a",
   "quote": "rather",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 159,
   "habit": null,
   "severity": "n/a",
   "quote": "nearly",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 179,
   "habit": null,
   "severity": "n/a",
   "quote": "normally",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 213,
   "habit": null,
   "severity": "n/a",
   "quote": "a lot",
   "rule": "weaselWords",
   "why": ""
  },
  {
   "line": 37,
   "habit": null,
   "severity": "n/a",
   "quote": "is locked",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 41,
   "habit": null,
   "severity": "n/a",
   "quote": "is recorded",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 41,
   "habit": null,
   "severity": "n/a",
   "quote": "been refused",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 86,
   "habit": null,
   "severity": "n/a",
   "quote": "was published",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 107,
   "habit": null,
   "severity": "n/a",
   "quote": "was published",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 203,
   "habit": null,
   "severity": "n/a",
   "quote": "are kept",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 218,
   "habit": null,
   "severity": "n/a",
   "quote": "was written",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 230,
   "habit": null,
   "severity": "n/a",
   "quote": "was made",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 231,
   "habit": null,
   "severity": "n/a",
   "quote": "was copied",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 232,
   "habit": null,
   "severity": "n/a",
   "quote": "were probed",
   "rule": "passiveVoice",
   "why": ""
  },
  {
   "line": 36,
   "habit": null,
   "severity": "n/a",
   "quote": "The\nconnections have to be separate, because one that has answered `discover` is locked\ninto the new protocol, so asking it for a handshake afterwards tells you about the\nlock and nothing about the server.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 112,
   "habit": null,
   "severity": "n/a",
   "quote": "Before probing any vendor servers, I'd checked the TypeScript side and written down\nthat its SDK hadn't shipped the July revision, because the newest\n`@modelcontextprotocol/sdk` on npm is 1.30.0 and there's no mention of `2026-07-28`\nanywhere in its build.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 123,
   "habit": null,
   "severity": "n/a",
   "quote": "If you maintain a TypeScript server, Dependabot will keep bumping\n`@modelcontextprotocol/sdk` for you and you'll stay on the old protocol, because the\nversion that speaks the new one has a different name.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 150,
   "habit": null,
   "severity": "n/a",
   "quote": "The\nPython v1 SDK models incoming requests as a closed set of known types, which fits the\nunknown method failing validation before anything routes it — though I haven't traced\nthat path through the v1 source, so I'd call it the likely mechanism rather than a\nproven one.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 156,
   "habit": null,
   "severity": "n/a",
   "quote": "Fall back to the old\nhandshake only when you see `-32601`, which is the obvious reading of the spec, and\nevery Python v1 server in this table — dbt Labs' included — looks like a server that\nwon't talk to you at all.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 172,
   "habit": null,
   "severity": "n/a",
   "quote": "The SDK reports a dead server process as an error with the code `-32000` and the\nmessage \"Connection closed\", and my probe treated every SDK error as the server saying\nno.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 226,
   "habit": null,
   "severity": "n/a",
   "quote": "Its design record,\n  <code>docs/011_discover-probe.md</code>, has the full table with versions and the\n  corrections to what I first wrote down, and the raw measurement is in\n  <code>evidence/discover-probe.jsonl</code>.</p>\n  <p><strong>How this was made.</strong> <code>discover-probe</code> and this write-up\n  were both built with Claude Code.",
   "rule": "longSentences",
   "why": ""
  },
  {
   "line": 231,
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
   "line": 27,
   "habit": null,
   "severity": "n/a",
   "quote": "negotiation",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 36,
   "habit": null,
   "severity": "n/a",
   "quote": "connection",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 47,
   "habit": null,
   "severity": "n/a",
   "quote": "reference",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 152,
   "habit": null,
   "severity": "n/a",
   "quote": "validation",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 159,
   "habit": null,
   "severity": "n/a",
   "quote": "negotiation",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 173,
   "habit": null,
   "severity": "n/a",
   "quote": "Connection",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 220,
   "habit": null,
   "severity": "n/a",
   "quote": "reference",
   "rule": "nominalizations",
   "why": ""
  },
  {
   "line": 228,
   "habit": null,
   "severity": "n/a",
   "quote": "measurement",
   "rule": "nominalizations",
   "why": ""
  }
 ]
}
```
