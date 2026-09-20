```json
{
  "findings": [
    {
      "line": 17,
      "habit": "hedge",
      "severity": "high",
      "quote": "Plenty of older clients and servers are still around",
      "why": "A universal claim about how many old clients and servers persist, with no name for who or a count, so it can't be checked."
    },
    {
      "line": 23,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "which turned out to be harder to ask than I expected",
      "why": "A reaction with no content; the passage needs a real specific from the author about what made asking hard, not a description of the surprise itself."
    },
    {
      "line": 36,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "For a client that just needs a session, that's the right design. For working out what a server is, it throws the answer away.",
      "why": "The same contrast split across two parallel sentences, praising the design for one purpose only to knock it down for another."
    },
    {
      "line": 45,
      "habit": "triad",
      "severity": "medium",
      "quote": "It worked. The server answered and said no, in which case the error code is kept. Or nothing usable came back at all.",
      "why": "Three parallel short outcomes lined up for a sense of completeness rather than because the phrasing needed exactly three beats."
    },
    {
      "line": 46,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "The difference between those last two is the whole point",
      "why": "A stock phrase that announces importance without itself showing why it's the whole point."
    },
    {
      "line": 46,
      "habit": "closer",
      "severity": "low",
      "quote": "The difference between those last two is the whole point, because a server that never answered hasn't told you anything about which protocol it speaks.",
      "why": "Ends the section's argument by telling the reader what it all meant, right before the next heading."
    },
    {
      "line": 91,
      "habit": "fragment",
      "severity": "high",
      "quote": "Both npm packages, both reasonably recent, opposite answers.",
      "why": "Three verbless parallel phrases standing in for a full sentence."
    },
    {
      "line": 114,
      "habit": "restatement",
      "severity": "high",
      "quote": "Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them.",
      "why": "The second sentence restates the first in negative form without adding new information."
    },
    {
      "line": 123,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "This part I got wrong first.",
      "why": "A one-line paragraph placed right after a heading purely to create a pause before the explanation, when the content doesn't need one."
    },
    {
      "line": 126,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "The evidence looked solid.",
      "why": "A claim about evidence with no evidence; the passage needs a real specific from the author about what made it look solid."
    },
    {
      "line": 178,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It had bugs I'd never have found against test servers.",
      "why": "A standalone short sentence right after the heading, set up to create a pause before the bug list rather than to carry information on its own."
    },
    {
      "line": 181,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It hadn't answered anything.",
      "why": "A very short sentence dropped in to reveal a contradiction of what the previous clause implied, when the correction could simply be stated once."
    },
    {
      "line": 190,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "which is precisely where that one explanatory line went",
      "why": "\"Precisely\" adds stress without adding any information about where the line went."
    },
    {
      "line": 191,
      "habit": "triad",
      "severity": "low",
      "quote": "reads as unreachable, exits with a failure code, and shows the tail of its stderr",
      "why": "Three parallel verb phrases stacked for cadence; each is real content, but the three-part form reads as finished more than the claim requires."
    },
    {
      "line": 202,
      "habit": "fragment",
      "severity": "medium",
      "quote": "And one mistake that wasn't in the probe at all.",
      "why": "A subject phrase with no main-clause predicate, standing in for a full sentence to introduce the next anecdote."
    },
    {
      "line": 219,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "that's a fact about the server rather than a lie it told",
      "why": "\"Rather than\" sets up one characterization of the exit code only to knock it down for another."
    },
    {
      "line": 223,
      "habit": "hedge",
      "severity": "medium",
      "quote": "plenty of hosted servers only offer HTTP",
      "why": "A second, echoing use of the softened universal quantifier \"plenty of\" with no named count."
    },
    {
      "line": 225,
      "habit": "antithesis",
      "severity": "high",
      "quote": "That's a decision about sending requests to other people's endpoints, not a technical gap, and I'd rather make it deliberately.",
      "why": "An \"X, not Y\" construction that asserts one characterization by explicitly knocking down another."
    },
    {
      "line": 236,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "These numbers have a short shelf life.",
      "why": "A stock phrase announcing impermanence instead of showing it."
    },
    {
      "line": 236,
      "habit": "closer",
      "severity": "medium",
      "quote": "These numbers have a short shelf life. The day the reference servers move to v2 SDKs, the table flips.",
      "why": "An aphoristic pair of sentences landing the final point of the piece's last substantive section."
    }
  ]
}
```

Antithesis and dramatic-beat each show up three times, and generic-detail, cliche-emphasis, triad, hedge, fragment, and closer each show up twice — the draft leans on knock-down contrasts and short reveal sentences more than any single word-level tic. The habits cluster in three places: the "You can't find out by connecting" section (lines 36-48), which stacks an antithesis, a triad, and a cliche-emphasis/closer pair in one paragraph; the "real servers taught me about the probe" section (lines 178-202), which carries two dramatic-beats, the emphasis-word, a triad, and a fragment; and the closing stretch from "Two ways to say you don't know a method" through "Loose ends" (lines 219-238), which closes with two separate antithesis constructions and a final cliche-emphasis/closer pair. Outside the injected examples, the recurring shape is a short sentence used to reveal or reverse the sentence before it.
