```json
{
  "findings": [
    {
      "line": 34,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "That's a reasonable default for a client, and it's also why the probe can't use it.",
      "why": "Sets up a good design choice only to reverse it with a consequence, following the not-X-but-Y pattern."
    },
    {
      "line": 48,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "whose tools people actually run",
      "why": "The word 'actually' adds stress without changing the meaning; 'whose tools people run' conveys the same point."
    },
    {
      "line": 103,
      "habit": "antithesis",
      "severity": "high",
      "quote": "Every server on a version-one SDK spoke only the old handshake, and every server on version two spoke both.",
      "why": "Direct contrast between SDK versions following the parallel structure of v1 doing X while v2 does Y."
    },
    {
      "line": 107,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "No server advertised a capability it couldn't list. And `server-everything`, which the MCP project uses to demonstrate every protocol feature, was published on 31 August, five weeks after the revision it doesn't speak.",
      "why": "A short statement followed by a longer sentence starting with 'And' creates a pause before revealing the ironic fact about the reference implementation."
    },
    {
      "line": 164,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "the probe exited successfully. In fact it had died on startup before answering anything",
      "why": "Contradicts the initial result to reveal a false positive in probe output, using the successful-but-actually-failed structure."
    },
    {
      "line": 220,
      "habit": "closer",
      "severity": "low",
      "quote": "The table will change as soon as the reference servers move to v2 SDKs. I've dated it for that reason, and would re-run it before quoting it anywhere.",
      "why": "Ends the section with practical takeaway framed as summary/conclusion of why the data is transient."
    }
  ]
}
```

Antithesis appears three times, each following the not-X-but-Y or v1-does-X-while-v2-does-Y structure. They cluster around key points: explaining constraints, summarizing findings in the table, and revealing probe bugs. Dramatic-beat and closer appear once each as structural habits in section transitions.

