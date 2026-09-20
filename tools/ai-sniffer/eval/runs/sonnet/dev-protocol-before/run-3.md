```json
{
  "findings": [
    {
      "line": 17,
      "habit": "hedge",
      "severity": "high",
      "quote": "Plenty of older clients and servers are still around",
      "why": "A universal claim about how many old clients/servers persist, with no name for who, so it can't be checked."
    },
    {
      "line": 23,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "which turned out to be harder to ask than I expected",
      "why": "States a reaction to difficulty without saying what made asking hard; the passage needs a real specific from the author."
    },
    {
      "line": 36,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "For a client that just needs a session, that's the right design. For working out what a server is, it throws the answer away.",
      "why": "Two parallel sentences set up the same fact as good for one purpose and knock it down as bad for another."
    },
    {
      "line": 45,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It worked.",
      "why": "A two-word sentence dropped into a list of three outcomes, breaking rhythm for effect where the other two items are full clauses."
    },
    {
      "line": 46,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "The difference between those last two is the whole point",
      "why": "Announces importance with the stock phrase \"the whole point\" instead of letting the distinction show it."
    },
    {
      "line": 91,
      "habit": "fragment",
      "severity": "high",
      "quote": "Both npm packages, both reasonably recent, opposite answers.",
      "why": "Three verbless parallel phrases stand in for a sentence."
    },
    {
      "line": 110,
      "habit": "closer",
      "severity": "medium",
      "quote": "Which protocol a server speaks, on this sample, is a dependency decision nobody on the project necessarily made on purpose.",
      "why": "Closes the paragraph by telling the reader what the preceding data meant, rather than leaving the table to make the point."
    },
    {
      "line": 114,
      "habit": "restatement",
      "severity": "high",
      "quote": "Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them.",
      "why": "The second sentence just inverts the first, adding no new information."
    },
    {
      "line": 123,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "This part I got wrong first.",
      "why": "A one-line paragraph placed right after a heading purely to create a pause before the reveal."
    },
    {
      "line": 126,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "The evidence looked solid.",
      "why": "Asserts confidence in evidence without saying what the evidence was; the passage needs a real specific from the author."
    },
    {
      "line": 167,
      "habit": "antithesis",
      "severity": "low",
      "quote": "I'd call it the likely mechanism rather than a proven one.",
      "why": "A \"rather than\" construction that knocks down one framing for another, though here it's doing real epistemic work."
    },
    {
      "line": 178,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It had bugs I'd never have found against test servers.",
      "why": "A short standalone paragraph right after a heading, setting up a reveal the following examples would have carried on their own."
    },
    {
      "line": 190,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "which is precisely where that one explanatory line went",
      "why": "\"Precisely\" adds stress without adding information about where the line went."
    },
    {
      "line": 191,
      "habit": "triad",
      "severity": "medium",
      "quote": "A crashed server now reads as unreachable, exits with a failure code, and shows the tail of its stderr.",
      "why": "Three parallel verb phrases describing the fix, arranged for the shape of three rather than because a shorter or longer list wouldn't do."
    },
    {
      "line": 200,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "A server that genuinely never answers times out twice.",
      "why": "\"Genuinely\" intensifies the claim but the contrast with the earlier false-seeming case doesn't need the extra word."
    },
    {
      "line": 202,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "And one mistake that wasn't in the probe at all.",
      "why": "A short fragment-like sentence introducing the third bug as a reveal, echoing the same move used earlier in the piece."
    },
    {
      "line": 219,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "that's a fact about the server rather than a lie it told",
      "why": "Sets up \"a lie it told\" only to knock it down for \"a fact about the server,\" the same rather-than move used elsewhere in the piece."
    },
    {
      "line": 223,
      "habit": "hedge",
      "severity": "medium",
      "quote": "plenty of hosted servers only offer HTTP",
      "why": "An unquantified claim about how many hosted servers exist, with no name for which ones, echoing the same hedge used earlier."
    },
    {
      "line": 232,
      "habit": "closer",
      "severity": "medium",
      "quote": "So the SDK settled which protocols a server speaks, and what each server claims within them came down to how it was written.",
      "why": "Wraps up the paragraph's four examples with a tidy statement of what they meant."
    },
    {
      "line": 236,
      "habit": "cliche-emphasis",
      "severity": "high",
      "quote": "These numbers have a short shelf life.",
      "why": "A stock phrase announcing that the data will age rather than showing it."
    }
  ]
}
```

Dramatic-beat is the most frequent habit, appearing four times (lines 45, 123, 178, 202), each a short standalone sentence or fragment dropped in right after a heading or list item to create a pause. Antithesis is the second most common, showing up three times (lines 36, 167, 219) as a recurring "X rather than Y" or two-sentence contrast move. The two clearest catalogue-style instances — cliche-emphasis ("the whole point," "short shelf life") and hedge ("plenty of...") — each occur twice, bookending the piece near the start and again near the close. Closers cluster in the "Twelve servers" and "Loose ends" sections, where paragraphs about data end on a sentence stating what the data meant.
