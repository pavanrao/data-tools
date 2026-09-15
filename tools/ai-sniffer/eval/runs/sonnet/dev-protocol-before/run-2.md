```json
{
  "findings": [
    {
      "line": 17,
      "habit": "hedge",
      "severity": "high",
      "quote": "Plenty of older clients and servers are still around",
      "why": "\"Plenty of\" softens a claim about how many old clients and servers exist without naming any, so it can't be checked."
    },
    {
      "line": 24,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "which turned out to be harder to ask than I expected",
      "why": "Says finding out was harder than expected but never says what made it hard; the specific obstacle is missing."
    },
    {
      "line": 24,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "actually speak",
      "why": "\"Actually\" stresses the word \"speak\" without adding information beyond it."
    },
    {
      "line": 46,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "The difference between those last two is the whole point",
      "why": "Announces that a distinction matters with a stock phrase instead of showing why it matters."
    },
    {
      "line": 53,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "companies whose tools people actually run",
      "why": "A second, nearby use of \"actually\" as an intensifier that adds stress but no new information."
    },
    {
      "line": 91,
      "habit": "fragment",
      "severity": "high",
      "quote": "Both npm packages, both reasonably recent, opposite answers.",
      "why": "Three verbless clauses in a row stand in for a full sentence comparing the two packages."
    },
    {
      "line": 114,
      "habit": "restatement",
      "severity": "high",
      "quote": "Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them.",
      "why": "The second sentence restates the first as a negative without adding anything new."
    },
    {
      "line": 123,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "This part I got wrong first.",
      "why": "A one-line paragraph placed right after a heading to create a pause before any detail is given."
    },
    {
      "line": 126,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "The evidence looked solid.",
      "why": "Says the evidence looked solid but never says what the evidence was or what made it look that way."
    },
    {
      "line": 133,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "The TypeScript SDK's second version wasn't released as a new major of the package everyone already had. It went out on 27 July as separate packages, and the old one simply stops at 1.x.",
      "why": "Sets up what the release wasn't only to knock it down with what it actually was, the two-sentence 'It wasn't X. It was Y' shape."
    },
    {
      "line": 173,
      "habit": "hedge",
      "severity": "low",
      "quote": "falls back on nearly any error",
      "why": "\"Nearly any\" describes checkable SDK behavior with a vague quantifier instead of naming which errors."
    },
    {
      "line": 178,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It had bugs I'd never have found against test servers.",
      "why": "A short, stark sentence opens the section as a pause, though the heading already told the reader bugs are coming."
    },
    {
      "line": 180,
      "habit": "antithesis",
      "severity": "high",
      "quote": "meaning it had answered and refused both protocols, and the probe exited successfully. It hadn't answered anything.",
      "why": "Sets up that the server had answered and refused both protocols only to reverse it completely in the next sentence."
    },
    {
      "line": 190,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "which is precisely where that one explanatory line went",
      "why": "\"Precisely\" adds stress to the coincidence without adding information about it."
    },
    {
      "line": 200,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "A server that genuinely never answers times out twice.",
      "why": "\"Genuinely\" intensifies \"never answers\" without adding checkable content."
    },
    {
      "line": 202,
      "habit": "fragment",
      "severity": "medium",
      "quote": "And one mistake that wasn't in the probe at all.",
      "why": "A verbless opening clause stands in for a full introductory sentence."
    },
    {
      "line": 218,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "A server that only speaks the old protocol exits `0`, since that's a fact about the server rather than a lie it told.",
      "why": "Frames the exit code as one thing rather than another, a not-X-but-Y contrast."
    },
    {
      "line": 223,
      "habit": "hedge",
      "severity": "high",
      "quote": "plenty of hosted servers only offer HTTP",
      "why": "\"Plenty of\" softens a claim about how many hosted servers exist without naming any, echoing the same hedge from the opening paragraph."
    },
    {
      "line": 225,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "That's a decision about sending requests to other people's endpoints, not a technical gap",
      "why": "Sets up one framing of the limitation only to knock down an alternative framing with \"not a technical gap.\""
    },
    {
      "line": 236,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "These numbers have a short shelf life.",
      "why": "A stock phrase announces that the data will go stale instead of showing what would make it go stale."
    }
  ]
}
```

Antithesis and emphasis-word intensifiers are the most frequent habits here, each appearing four times, with hedges built on "plenty of" close behind at three. The antithesis setups cluster in the back half of the piece, from the TypeScript-versioning section through the MotherDuck bug story and into the closing "Run it yourself" and "Loose ends" sections, each time framing a correction or a limitation as "not X but Y." The two "plenty of" hedges bookend the draft, one in the opening paragraph and one in "Loose ends," and "actually" appears twice in the first two sections. The single clearest habits — the two cliche-emphasis lines, the restatement, and the two generic-detail gaps — sit mostly in the first half, where the draft's stock phrasing is most visible before the more technical middle sections ease off.
