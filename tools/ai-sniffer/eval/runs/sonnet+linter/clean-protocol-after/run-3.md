```json
{
  "findings": [
    {
      "line": 159,
      "habit": "hedge",
      "severity": "medium",
      "quote": "falls back on nearly any error",
      "why": "The claim about which errors trigger fallback is softened to 'nearly any' without naming which ones, so it can't be checked."
    },
    {
      "line": 48,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "actually",
      "why": "'Actually' adds emphasis to 'run' without contributing information beyond what naming real companies already carries."
    },
    {
      "line": 53,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Microsoft's Playwright server first:",
      "why": "A verbless noun phrase stands in for a sentence to introduce the code block, a construction the draft repeats at line 70."
    },
    {
      "line": 70,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Upstash's Context7, run the same way:",
      "why": "The same verbless lead-in-to-code-block construction as line 53, marking it as a repeated device rather than a one-off."
    },
    {
      "line": 234,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Written against MCP protocol revision 2026-07-28.",
      "why": "A third verbless fragment, here closing the piece with a bare version stamp instead of a full sentence."
    },
    {
      "line": 164,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "MotherDuck's first result was `neither`, meaning it had answered and refused both protocols, and the probe exited successfully. In fact it had died on startup before answering anything, because I'd left off a flag it needs:",
      "why": "States an apparently ordinary result, then pivots on 'In fact' to reveal the real cause, the same two-sentence reveal shape the draft uses again at line 186."
    },
    {
      "line": 181,
      "habit": "antithesis",
      "severity": "low",
      "quote": "That would have made any server I probed for the first time look more old-fashioned than it is.",
      "why": "Sets up an apparent characteristic of the server only to negate it with 'than it is', a compressed version of the seems-like-X-but-isn't shape used more explicitly elsewhere in the section."
    },
    {
      "line": 186,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "I'd concluded that the Python servers' error code and message contradicted each other, because the message read \"Invalid request\". My own summary script had cut every message at 40 characters, and the full text was \"Invalid request parameters\", which matches the code.",
      "why": "States a mistaken conclusion, then pivots to the real explanation, repeating the reveal shape used for MotherDuck earlier in the same section."
    },
    {
      "line": 184,
      "habit": "closer",
      "severity": "low",
      "quote": "A server that never answers at all times out twice.",
      "why": "A short declarative sentence caps the paragraph by tidily stating what the fix implies, in the cadence of a wrap-up line rather than a continuation of the explanation."
    }
  ]
}
```

Antithesis and fragment are the habits that recur. Antithesis clusters in "What running it on real servers taught me about the probe," where three separate corrections (MotherDuck, the dbt-mcp timeout, the truncated error message) are each narrated as an apparent result overturned by the real one. Fragment shows up as a verbless lead-in used twice to introduce console output (lines 53 and 70) and once more to close the piece (line 234). Hedge, emphasis-word, and closer each appear once and are minor on their own; no triads, restatements, cliché-emphasis, reader-instruction, or generic-detail turned up anywhere in the draft.
