```json
{
  "findings": [
    {
      "line": 288,
      "habit": "antithesis",
      "severity": "high",
      "quote": "I assumed the time would go on the protocol. It didn't. Nearly all of it went on one question that turned out to be harder than it looks",
      "why": "sets up one expectation (time spent on the protocol) only to knock it down for another (time spent on one question), split across short sentences"
    },
    {
      "line": 343,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Not a flag your code consults later",
      "why": "verbless phrase standing in for a sentence, used for contrastive emphasis before the dash"
    },
    {
      "line": 414,
      "habit": "restatement",
      "severity": "low",
      "quote": "My own tool couldn't read its own schema",
      "why": "restates the fact just given in \"It got refused\" with ironic framing rather than new information"
    },
    {
      "line": 414,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It got refused.",
      "why": "a very short sentence dropped in right after the setup to create a reveal"
    },
    {
      "line": 422,
      "habit": "fragment",
      "severity": "medium",
      "quote": "No mention of which action, which table, or which pragma.",
      "why": "verbless parallel phrase standing in for a sentence"
    },
    {
      "line": 427,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "What's actually going on",
      "why": "\"actually\" adds stress without adding information about the pragma behavior"
    },
    {
      "line": 438,
      "habit": "antithesis",
      "severity": "high",
      "quote": "I'd have shipped it and never known. Instead the allowlist broke my own code in development, which is the cheapest place for it to break.",
      "why": "sets up the silent-failure outcome only to knock it down with the actual, louder outcome, pivoting on \"Instead\""
    },
    {
      "line": 440,
      "habit": "closer",
      "severity": "high",
      "quote": "which is the cheapest place for it to break.",
      "why": "a tidy clause that lands the point of the paragraph rather than just ending it"
    },
    {
      "line": 406,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Same idea, different engine.",
      "why": "two-part verbless phrase closing the callout, parallel in structure"
    },
    {
      "line": 331,
      "habit": "closer",
      "severity": "medium",
      "quote": "The server keeps returning results and you keep believing it's read-only.",
      "why": "a summary line telling the reader what the preceding point meant, capping the paragraph"
    },
    {
      "line": 396,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "All four, and I didn't reason about any of them.",
      "why": "a short beat placed right after the list of four cases to land before the explanation"
    },
    {
      "line": 276,
      "habit": "hedge",
      "severity": "high",
      "quote": "Most SQL-over-MCP servers decide whether a query is safe by reading the query.",
      "why": "a universal claim about \"most\" servers with none named, so it can't be checked"
    },
    {
      "line": 298,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Most published examples do a version of this",
      "why": "\"most published examples\" names no examples, leaving the claim unverifiable"
    },
    {
      "line": 493,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Every server like this caps how many rows it returns",
      "why": "a universal claim about \"every\" such server with none named"
    },
    {
      "line": 494,
      "habit": "dramatic-beat",
      "severity": "low",
      "quote": "The cap isn't the interesting bit.",
      "why": "a short flat sentence used to pivot toward the real point"
    },
    {
      "line": 494,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "What matters is that a truncated result which doesn't mention it was truncated is worse than no result at all",
      "why": "\"what matters is\" announces importance rather than showing it"
    },
    {
      "line": 507,
      "habit": "hedge",
      "severity": "medium",
      "quote": "the compute dwarfs the token spend by more than people expect",
      "why": "\"people\" names no one, so the comparison can't be checked"
    },
    {
      "line": 514,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "For the case you're probably picturing, no.",
      "why": "a blunt one-word verdict dropped at the start of the paragraph for effect"
    },
    {
      "line": 531,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "which is genuinely the problem it exists to solve",
      "why": "\"genuinely\" adds stress without adding information to the claim"
    },
    {
      "line": 456,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "The server did exactly what it was built to do.",
      "why": "\"exactly\" is stressed emphasis rather than describing a checkable exact match"
    },
    {
      "line": 456,
      "habit": "antithesis",
      "severity": "high",
      "quote": "But nothing broke.",
      "why": "knocks down the expectation just raised (that something broke) with a short direct negation"
    },
    {
      "line": 538,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Two things I'd tell someone doing this next.",
      "why": "a noun-phrase-led fragment setting up a list, parallel to the catalogue's \"Two mechanisms\" shape"
    },
    {
      "line": 550,
      "habit": "triad",
      "severity": "medium",
      "quote": "Nothing errors, nothing warns, and the tool looks identical when you list it.",
      "why": "three parallel clauses stacked for rhythm rather than because three distinct symptoms were needed"
    },
    {
      "line": 561,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "I haven't run it.",
      "why": "a short admission placed as the final line of the paragraph to land on its own"
    }
  ]
}
```

Antithesis, dramatic-beat, fragment, and hedge are the habits that recur most, each appearing four or more times across the draft. They cluster in two places: the SQLite-authorizer narrative (lines 331-456), where short knockdown sentences and verbless fragments appear almost every paragraph, and the closing third of the piece (lines 493-561), where short verdict sentences ("no.", "I haven't run it.") and hedged universals ("every server like this," "more than people expect") repeat the same short-declarative-beat shape. The hedges are notable for spanning the piece end to end, from the standfirst's "Most SQL-over-MCP servers" to the closing section's "people expect." Emphasis-words ("actually," "genuinely," "exactly") appear only once or twice each and are individually milder, but their repetition across the draft is itself part of the pattern.
