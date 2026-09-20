```json
{
  "findings": [
    {
      "line": 38,
      "habit": "antithesis",
      "severity": "low",
      "quote": "tells you about the lock and nothing about the server",
      "why": "sets up what the second connection would tell you only to deny it, a compact affirm/negate pivot."
    },
    {
      "line": 48,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "companies whose tools people actually run",
      "why": "\"actually\" intensifies without adding checkable information about who runs them or how much."
    },
    {
      "line": 53,
      "habit": "fragment",
      "severity": "low",
      "quote": "Microsoft's Playwright server first:",
      "why": "verbless phrase standing in as a lead-in sentence before the code block."
    },
    {
      "line": 70,
      "habit": "fragment",
      "severity": "low",
      "quote": "Upstash's Context7, run the same way:",
      "why": "a second verbless lead-in of the same shape as line 53, forming a parallel pair before code blocks."
    },
    {
      "line": 165,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "the probe exited successfully. In fact it had died on startup before answering anything, because I'd left off a flag it needs",
      "why": "states the apparent result only to knock it down with the real one in the next clause, the classic 'seemed X, in fact Y' pivot."
    },
    {
      "line": 175,
      "habit": "triad",
      "severity": "low",
      "quote": "A crashed server now reads as unreachable, exits with a failure code, and shows the tail of its stderr.",
      "why": "three parallel verb clauses land with the rhythm of a finished list more than the content strictly requires."
    },
    {
      "line": 184,
      "habit": "closer",
      "severity": "high",
      "quote": "A server that never answers at all times out twice.",
      "why": "a crisp, quotable line that wraps up the paragraph's point rather than continuing to report what happened."
    },
    {
      "line": 186,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "I also made a mistake outside the probe.",
      "why": "a short standalone confession-sentence placed to create a reveal before the explanation, when the next sentence could simply state the mistake."
    }
  ]
}
```

The clearest cluster is the debugging section ("What running it on real servers taught me about the probe," lines 162-189), which holds four of the eight findings: an antithesis reveal about the MotherDuck crash, a three-clause triad describing the fix, a closer line about timeouts, and a dramatic-beat opener for the summary-script mistake. The other recurring shape is the verbless colon lead-in before a code block, used twice in parallel ("Microsoft's Playwright server first:" and "Upstash's Context7, run the same way:") in the "Twelve servers" section. Outside those two clusters the draft is largely free of the catalogued habits — no hedges, reader-instructions, or generic-detail passages turned up, and only one mild emphasis-word ("actually") and one low-grade antithesis appear in the earlier sections.
