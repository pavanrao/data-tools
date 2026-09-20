```json
{
  "findings": [
    {
      "line": 17,
      "habit": "hedge",
      "severity": "high",
      "quote": "Plenty of older clients and servers are still around",
      "why": "Universal claim about unnamed older clients and servers that can't be checked without naming who runs them."
    },
    {
      "line": 23,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "which turned out to be harder to ask than I expected",
      "why": "Vague claim about difficulty with no real specific about what made it hard; needs a concrete detail from the author, not a description of one."
    },
    {
      "line": 36,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "For a client that just needs a session, that's the right design. For working out what a server is, it throws the answer away.",
      "why": "Sets up one framing as correct only to invert the same framing into a failure across two matched sentences."
    },
    {
      "line": 46,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "The difference between those last two is the whole point",
      "why": "Stock phrase announcing that a distinction matters instead of showing why it matters."
    },
    {
      "line": 46,
      "habit": "closer",
      "severity": "medium",
      "quote": "The difference between those last two is the whole point, because a server that never answered hasn't told you anything about which protocol it speaks.",
      "why": "Ends the section by telling the reader what the distinction meant rather than stopping at the fact itself."
    },
    {
      "line": 91,
      "habit": "fragment",
      "severity": "high",
      "quote": "Both npm packages, both reasonably recent, opposite answers.",
      "why": "Three verbless phrases in a row standing in for a sentence."
    },
    {
      "line": 114,
      "habit": "restatement",
      "severity": "high",
      "quote": "Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them.",
      "why": "Second sentence inverts and repeats the first sentence's point without adding anything new."
    },
    {
      "line": 123,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "This part I got wrong first.",
      "why": "One-line paragraph placed to create a pause before the correction, though the correction doesn't need the pause."
    },
    {
      "line": 126,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "The evidence looked solid.",
      "why": "Vague assessment of the evidence with no specifics given for why it looked that way; needs a real detail from the author, not a description of one."
    },
    {
      "line": 173,
      "habit": "hedge",
      "severity": "low",
      "quote": "nearly any",
      "why": "Approximates which errors the SDK falls back on without naming the exceptions, so the claim can't be checked."
    },
    {
      "line": 178,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It had bugs I'd never have found against test servers.",
      "why": "One-line paragraph placed to create a pause before the bug list, though the list doesn't need the pause."
    },
    {
      "line": 180,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "MotherDuck's first result was `neither`, meaning it had answered and refused both protocols, and the probe exited successfully. It hadn't answered anything.",
      "why": "Sets up the initial reading of the result only to flatly negate it in the next sentence."
    },
    {
      "line": 190,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "which is precisely where that one explanatory line went",
      "why": "Intensifier adds stress to the location without adding information beyond 'where it went'."
    },
    {
      "line": 200,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "genuinely",
      "why": "Intensifies 'never answers' without adding checkable information."
    },
    {
      "line": 202,
      "habit": "fragment",
      "severity": "medium",
      "quote": "And one mistake that wasn't in the probe at all.",
      "why": "Elliptical clause missing a main predicate, standing in for a full sentence."
    },
    {
      "line": 218,
      "habit": "antithesis",
      "severity": "high",
      "quote": "A server that only speaks the old protocol exits `0`, since that's a fact about the server rather than a lie it told.",
      "why": "'Rather than' sets up one framing of the exit code only to knock it down for another."
    },
    {
      "line": 218,
      "habit": "closer",
      "severity": "medium",
      "quote": "A server that only speaks the old protocol exits `0`, since that's a fact about the server rather than a lie it told.",
      "why": "Ends the section with a line that tells the reader what the exit code means rather than stopping at the behavior itself."
    },
    {
      "line": 223,
      "habit": "hedge",
      "severity": "high",
      "quote": "plenty of hosted servers",
      "why": "Repeats the same unfalsifiable quantifier used earlier in the piece about unnamed servers."
    },
    {
      "line": 236,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "These numbers have a short shelf life.",
      "why": "Stock phrase announcing impermanence instead of showing it."
    },
    {
      "line": 53,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "actually",
      "why": "Intensifies 'run' without adding checkable information about who runs the tools."
    }
  ]
}
```

Antithesis and hedge are the two habits that recur enough to count as patterns rather than single choices: antithesis appears three times (lines 36, 180, 218), each setting up one reading only to knock it down in the next clause or sentence, and "plenty of" as a hedge appears twice (lines 17 and 223) about different unnamed groups of servers. The two generic-detail instances (lines 23 and 126) and the two cliche-emphasis instances (lines 46 and 236) are close matches to each other in phrasing and both land at section or paragraph boundaries. The heaviest clustering is in the piece's back half, from the MotherDuck bug story through the exit-code section (roughly lines 178-236), where dramatic-beat, fragment, antithesis, emphasis-word, hedge, and cliche-emphasis all appear within about sixty lines of each other.
