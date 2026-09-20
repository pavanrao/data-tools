```json
{
  "findings": [
    {
      "line": 276,
      "habit": "hedge",
      "severity": "high",
      "quote": "Almost every SQL-over-MCP server decides whether a query is safe by reading the query.",
      "why": "A universal claim about an unnamed set of servers, opening the standfirst, that no reader can check."
    },
    {
      "line": 302,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Most published examples do some version of this",
      "why": "Softens a claim about examples without naming which ones, so it can't be checked."
    },
    {
      "line": 289,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Three tools, a row cap, done in an afternoon.",
      "why": "Three verbless phrases standing in for a sentence, in a row."
    },
    {
      "line": 294,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It was this question.",
      "why": "A very short sentence inserted purely to create a pause before the real question."
    },
    {
      "line": 309,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Consider what it must already handle correctly.",
      "why": "Opens on \"Consider\", directly instructing the reader how to engage with what follows."
    },
    {
      "line": 332,
      "habit": "antithesis",
      "severity": "high",
      "quote": "You can fix each of these. You cannot fix the category.",
      "why": "Sets up one claim only to knock it down for the opposite, split across two sentences."
    },
    {
      "line": 333,
      "habit": "antithesis",
      "severity": "low",
      "quote": "the list of shapes is owned by whoever maintains the SQL dialect, not by you",
      "why": "A second X-not-Y contrast in the same paragraph as the sentence above."
    },
    {
      "line": 342,
      "habit": "fragment",
      "severity": "high",
      "quote": "Two mechanisms, both older than the problem.",
      "why": "Verbless phrase standing in for a sentence, announcing a list before any items are given."
    },
    {
      "line": 406,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "this is a read-only role granted on a narrow set of views, not a string check in your server",
      "why": "Knocks down one option (a string check) in favor of another (a role) via a not-Y tail."
    },
    {
      "line": 408,
      "habit": "antithesis",
      "severity": "high",
      "quote": "The lesson survives the change of engine; the regex does not.",
      "why": "The same X-does/Y-does-not contrast split across a semicolon, landing the callout."
    },
    {
      "line": 430,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Sit with that for a second.",
      "why": "Tells the reader how to react to the point just made rather than letting it stand."
    },
    {
      "line": 432,
      "habit": "triad",
      "severity": "high",
      "quote": "Deny-by-default failed loudly, in development, on the safe side.",
      "why": "Three parallel clauses shaped to sound conclusive rather than because there were three distinct things to report."
    },
    {
      "line": 433,
      "habit": "closer",
      "severity": "high",
      "quote": "That is the entire argument for it in one incident.",
      "why": "A line that tells the reader what the preceding anecdote meant, closing the section on an aphorism."
    },
    {
      "line": 446,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It is the wrong channel.",
      "why": "A short flat sentence placed at the top of the paragraph purely to create a reveal before the explanation."
    },
    {
      "line": 447,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "But nothing broke.",
      "why": "Knocks down the setup (something broke) with its negation in a following short sentence."
    },
    {
      "line": 448,
      "habit": "antithesis",
      "severity": "high",
      "quote": "What the model needs to know is not that it failed, but what to do differently.",
      "why": "Classic not-X-but-Y construction contrasting two framings of the same fact."
    },
    {
      "line": 461,
      "habit": "fragment",
      "severity": "high",
      "quote": "Two fields, two audiences.",
      "why": "Verbless parallel phrase standing in for a sentence, echoing the same shape used earlier for the two mechanisms."
    },
    {
      "line": 485,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "Fine.",
      "why": "A one-word sentence inserted as a beat before the pivot, where the content doesn't need the pause."
    },
    {
      "line": 496,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "the compute dwarfs the tokens by an amount that surprises people",
      "why": "Claims a magnitude and a reaction without giving the real number or naming who is surprised; the passage needs a real specific from the author."
    },
    {
      "line": 412,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "which is the point",
      "why": "A stock phrase asserting significance in the heading itself rather than showing it."
    },
    {
      "line": 518,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Note that none of those three is about the protocol.",
      "why": "Opens on \"Note that\", directing how the reader should take the list just given."
    },
    {
      "line": 528,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Build a server, not a client.",
      "why": "X-not-Y construction used as the punchy opening of a list item."
    },
    {
      "line": 529,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "A database qualifies. A folder of text files does not.",
      "why": "Sets up one case as qualifying only to knock down the other across two adjacent sentences."
    },
    {
      "line": 530,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "They are the product.",
      "why": "A stock claim of importance standing in place of showing why the guards matter more than the query code."
    },
    {
      "line": 531,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Test the round trip, not the registration.",
      "why": "Another X-not-Y construction in the same list as the two above it."
    },
    {
      "line": 512,
      "habit": "fragment",
      "severity": "high",
      "quote": "A colleague who does not write SQL, an agent running unattended, a client with no shell.",
      "why": "Three parallel verbless phrases in a row standing in for a sentence."
    },
    {
      "line": 538,
      "habit": "triad",
      "severity": "medium",
      "quote": "Nothing errors, nothing warns, and the tool looks identical in a listing.",
      "why": "Three parallel clauses shaped for a sense of completeness rather than because a third clause was needed."
    }
  ]
}
```

Antithesis is the habit that recurs most, with nine instances running through nearly every section: the anticipation argument, the read-only callout, the refusal-channel explanation, and all three items of the closing "what I would tell someone starting" list. Reader-instruction ("Consider...", "Sit with that...", "Note that...") and dramatic-beat each surface three times, clustering around the two "got this wrong" sections in the middle of the piece. Fragment appears four times at points the draft treats as pivots — the opening summary, the mechanism introduction, the refusal-fields explanation, and the consumer list — and triad and cliche-emphasis each show up twice, also concentrated in the second half.
