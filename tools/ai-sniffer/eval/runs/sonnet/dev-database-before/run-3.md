```json
{
  "findings": [
    {
      "line": 276,
      "habit": "hedge",
      "severity": "high",
      "quote": "Almost every SQL-over-MCP server decides whether a query is safe by reading the query.",
      "why": "\"Almost every\" makes a universal claim about SQL-over-MCP servers without naming which ones, so it can't be checked."
    },
    {
      "line": 289,
      "habit": "fragment",
      "severity": "high",
      "quote": "Three tools, a row cap, done in an afternoon.",
      "why": "Three verbless phrases stacked in a row stand in for a sentence describing the build."
    },
    {
      "line": 294,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It was this question.",
      "why": "A short pause is inserted before the actual question that follows, when the question could simply be asked."
    },
    {
      "line": 308,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Consider what it must already handle correctly.",
      "why": "Opens on \"Consider,\" directing the reader's next mental step rather than stating the point."
    },
    {
      "line": 332,
      "habit": "antithesis",
      "severity": "high",
      "quote": "You can fix each of these. You cannot fix the category.",
      "why": "Sets up what can be fixed only to knock it down with what cannot, across two short parallel sentences."
    },
    {
      "line": 333,
      "habit": "antithesis",
      "severity": "low",
      "quote": "the list of shapes is owned by whoever maintains the SQL dialect, not by you",
      "why": "Contrasts who owns the list against \"not by you,\" the same setup-and-negate move used elsewhere."
    },
    {
      "line": 342,
      "habit": "fragment",
      "severity": "high",
      "quote": "Two mechanisms, both older than the problem.",
      "why": "Two verbless clauses joined by a comma stand in for a full sentence."
    },
    {
      "line": 347,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Not a flag your code checks. The file is opened in a mode where writing is not a thing that can happen.",
      "why": "Negates the expected mechanism (\"a flag\") before supplying the real one, split across two sentences."
    },
    {
      "line": 372,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "That is the whole guard.",
      "why": "A short, flat declaration placed before the explanation that immediately follows it."
    },
    {
      "line": 372,
      "habit": "triad",
      "severity": "low",
      "quote": "how the statement is spelled, whether it uses a CTE, or what SQL adds next year",
      "why": "Three parallel clauses reaching for a three-part cadence rather than a natural count of cases."
    },
    {
      "line": 399,
      "habit": "closer",
      "severity": "medium",
      "quote": "It is an allowlist in the engine, so it is wrong only in the safe direction.",
      "why": "A summarizing line telling the reader what the whole comparison just meant."
    },
    {
      "line": 408,
      "habit": "closer",
      "severity": "high",
      "quote": "The lesson survives the change of engine; the regex does not.",
      "why": "An aphorism built to land the point of the callout box rather than continue the explanation."
    },
    {
      "line": 408,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "The lesson survives the change of engine; the regex does not.",
      "why": "Contrasts what survives against what does not in the same setup-and-knock-down shape."
    },
    {
      "line": 412,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "which is the point",
      "why": "A stock phrase that announces significance in the heading instead of letting the anecdote show it."
    },
    {
      "line": 416,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It was refused.",
      "why": "An isolated two-word sentence placed as a reveal right after the setup."
    },
    {
      "line": 416,
      "habit": "restatement",
      "severity": "medium",
      "quote": "My own tool could not read its own schema.",
      "why": "Repeats the fact the previous sentence (\"It was refused\") already gave, without adding new information."
    },
    {
      "line": 430,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Sit with that for a second.",
      "why": "Tells the reader how to react to the fact just given rather than stating its significance directly."
    },
    {
      "line": 431,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "I would have shipped it.",
      "why": "A short admission dropped in as its own beat before the summarizing sentences that follow."
    },
    {
      "line": 432,
      "habit": "triad",
      "severity": "high",
      "quote": "Deny-by-default failed loudly, in development, on the safe side.",
      "why": "Three parallel prepositional phrases reaching for a finished-sounding cadence."
    },
    {
      "line": 433,
      "habit": "closer",
      "severity": "high",
      "quote": "That is the entire argument for it in one incident.",
      "why": "A line telling the reader what the whole incident proved, closing out the anecdote."
    },
    {
      "line": 445,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It is the wrong channel.",
      "why": "An isolated short verdict placed right after the setup question, before the reasoning is given."
    },
    {
      "line": 446,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "But nothing broke.",
      "why": "A short contradiction dropped in as its own beat before the explanation continues."
    },
    {
      "line": 448,
      "habit": "antithesis",
      "severity": "high",
      "quote": "What the model needs to know is not that it failed, but what to do differently.",
      "why": "Negates \"that it failed\" before supplying \"what to do differently\" as the real point, the classic not-X-but-Y shape."
    },
    {
      "line": 460,
      "habit": "fragment",
      "severity": "high",
      "quote": "Two fields, two audiences.",
      "why": "Two verbless noun phrases stand in for a sentence introducing the two fields."
    },
    {
      "line": 484,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "Fine.",
      "why": "A one-word sentence used as a pause before the \"But\" that turns the paragraph."
    },
    {
      "line": 496,
      "habit": "hedge",
      "severity": "medium",
      "quote": "the compute dwarfs the tokens by an amount that surprises people",
      "why": "\"People\" is never named, so the claim about who is surprised can't be checked."
    },
    {
      "line": 512,
      "habit": "triad",
      "severity": "medium",
      "quote": "A colleague who does not write SQL, an agent running unattended, a client with no shell.",
      "why": "Three parallel noun phrases describing the non-you consumer, reaching for a finished cadence."
    },
    {
      "line": 518,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Note that none of those three is about the protocol.",
      "why": "\"Note that\" directs the reader's attention rather than stating the point directly."
    },
    {
      "line": 528,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Build a server, not a client.",
      "why": "Negates \"a client\" to land \"a server\" as the real advice, the same setup-and-negate move used elsewhere."
    }
  ]
}
```

Antithesis and dramatic-beat recur most, with eight and nine instances respectively, and both cluster tightly in the two anecdote sections: the authorizer story (lines 332-433, including the exact "You can fix each of these. You cannot fix the category." and "Sit with that for a second." lines) and the refusal-channel section (lines 445-449). Reader-instruction and closer also concentrate in that same middle stretch (lines 399-433), often stacking two or three habits onto adjacent sentences. Fragment appears three times, always as a short comma-joined, verbless pair or triple ("Two mechanisms...", "Three tools...", "Two fields..."), and hedge and triad each show up twice, spread further apart in the piece.
