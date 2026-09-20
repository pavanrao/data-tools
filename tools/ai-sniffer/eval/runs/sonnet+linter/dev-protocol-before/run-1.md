```json
{
  "findings": [
    {
      "line": 17,
      "habit": "hedge",
      "severity": "high",
      "quote": "Plenty of older clients and servers are still around",
      "why": "No name is given for which clients or servers, so the universal claim can't be checked."
    },
    {
      "line": 23,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "which turned out to be harder to ask than I expected",
      "why": "States a reaction to difficulty without saying what made it hard; needs a real specific from the author."
    },
    {
      "line": 36,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "For a client that just needs a session, that's the right design. For working out what a server is, it throws the answer away.",
      "why": "Grants the design is right for one purpose only to reverse the verdict for another, the antithesis move split across two sentences."
    },
    {
      "line": 45,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It worked.",
      "why": "A two-word sentence inserted for a pause before the three outcomes are actually laid out."
    },
    {
      "line": 46,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "The difference between those last two is the whole point",
      "why": "Announces importance with a stock phrase instead of showing why the difference matters."
    },
    {
      "line": 46,
      "habit": "closer",
      "severity": "medium",
      "quote": "The difference between those last two is the whole point, because a server that never answered hasn't told you anything about which protocol it speaks.",
      "why": "Ends the section with a line that tells the reader what the paragraph meant, rather than letting it just stop."
    },
    {
      "line": 91,
      "habit": "fragment",
      "severity": "high",
      "quote": "Both npm packages, both reasonably recent, opposite answers.",
      "why": "Three verbless parallel phrases standing in for a sentence."
    },
    {
      "line": 114,
      "habit": "restatement",
      "severity": "high",
      "quote": "Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them.",
      "why": "The second sentence makes the same point from the opposite direction without adding anything new."
    },
    {
      "line": 123,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "This part I got wrong first.",
      "why": "A one-line paragraph placed right after the heading purely to create a pause before the explanation."
    },
    {
      "line": 126,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "The evidence looked solid.",
      "why": "Asserts the evidence was convincing without saying what the evidence actually was."
    },
    {
      "line": 141,
      "habit": "closer",
      "severity": "low",
      "quote": "It just requires someone to take the major bump.",
      "why": "A short line built to land the section's point rather than the paragraph simply ending on its last fact."
    },
    {
      "line": 53,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "actually run",
      "why": "\"Actually\" adds stress to \"run\" without adding information the sentence doesn't already have."
    },
    {
      "line": 56,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "actually work",
      "why": "A second \"actually\" three lines later doing the same stress-only work as the one before it."
    },
    {
      "line": 173,
      "habit": "hedge",
      "severity": "medium",
      "quote": "nearly any error",
      "why": "A vague quantifier on a checkable technical claim, with no list of which errors trigger the fallback."
    },
    {
      "line": 178,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It had bugs I'd never have found against test servers.",
      "why": "A one-line paragraph opening the section to create a pause before the bugs are described."
    },
    {
      "line": 181,
      "habit": "antithesis",
      "severity": "high",
      "quote": "the probe exited successfully. It hadn't answered anything.",
      "why": "Sets up the successful exit only to reverse it flatly in the next sentence."
    },
    {
      "line": 190,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "which is precisely where that one explanatory line went",
      "why": "\"Precisely\" adds emphasis to the location without adding information."
    },
    {
      "line": 200,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "genuinely",
      "why": "Intensifies \"never answers\" without adding anything \"never\" doesn't already say."
    },
    {
      "line": 202,
      "habit": "fragment",
      "severity": "medium",
      "quote": "And one mistake that wasn't in the probe at all.",
      "why": "A verbless sentence opening the paragraph in place of a full one."
    },
    {
      "line": 218,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "that's a fact about the server rather than a lie it told",
      "why": "Casts the exit code as one thing rather than another, the not-X-but-Y shape in miniature."
    },
    {
      "line": 223,
      "habit": "hedge",
      "severity": "medium",
      "quote": "plenty of hosted servers",
      "why": "No name for which hosted servers, repeating the same vague quantifier used earlier in the piece."
    },
    {
      "line": 225,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "That's a decision about sending requests to other people's endpoints, not a technical gap, and I'd rather make it deliberately.",
      "why": "Explicit not-X-but-Y framing applied to the same limitation already stated plainly in the prior sentence."
    },
    {
      "line": 236,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "These numbers have a short shelf life.",
      "why": "A stock phrase announcing that the data will age instead of showing it aging."
    }
  ]
}
```

Antithesis and emphasis-word are the most frequent habits, each appearing four times, followed by dramatic-beat and hedge at three each. Antithesis clusters in the back half of the piece — the MotherDuck reveal, the exit-code framing, and the stdio caveat in "Loose ends" — with one earlier instance in the connection-probing section. Emphasis-word instances ("actually" twice, "precisely", "genuinely") cluster around the methodology paragraph and the "real servers" section, while the three dramatic-beat one-line paragraphs each open a section rather than appearing mid-argument. A number of the strongest findings are near-verbatim matches to habit patterns that recur across the piece's rhetorical high points: section-ending closers, a restatement, and two fragments.
