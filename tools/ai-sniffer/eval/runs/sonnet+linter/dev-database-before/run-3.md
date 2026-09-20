```json
{
  "findings": [
    {
      "line": 276,
      "habit": "hedge",
      "severity": "high",
      "quote": "Almost every SQL-over-MCP server decides whether a query is safe by reading the query.",
      "why": "A universal claim about how such servers work, with no named servers, opens the piece and can't be checked."
    },
    {
      "line": 289,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Three tools, a row cap, done in an afternoon.",
      "why": "A verbless list of three descriptors standing in for a sentence."
    },
    {
      "line": 289,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "The interesting part turned out not to be the protocol at all.",
      "why": "Sets up a negation that the next paragraph's opening sentence, \"It was this question,\" resolves — the setup/reveal split across sentences."
    },
    {
      "line": 302,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Most published examples do some version of this",
      "why": "A quantified claim about \"most\" examples with none named, so it can't be checked."
    },
    {
      "line": 309,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Consider what it must already handle correctly.",
      "why": "Opens on \"Consider,\" directly telling the reader how to approach what follows."
    },
    {
      "line": 332,
      "habit": "antithesis",
      "severity": "high",
      "quote": "You can fix each of these. You cannot fix the category.",
      "why": "Sets up one claim only to knock it down with its negation in the very next sentence."
    },
    {
      "line": 342,
      "habit": "fragment",
      "severity": "high",
      "quote": "Two mechanisms, both older than the problem.",
      "why": "A verbless phrase standing in for a full sentence, immediately after the sentence it elaborates."
    },
    {
      "line": 347,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Not a flag your code checks.",
      "why": "A verbless phrase inserted between two full sentences to stand in for one."
    },
    {
      "line": 408,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "The lesson survives the change of engine; the regex does not.",
      "why": "Two parallel clauses set against each other, one affirmed and one negated, to land the callout's point."
    },
    {
      "line": 412,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "which is the point",
      "why": "A stock phrase in the heading that announces significance rather than showing it."
    },
    {
      "line": 430,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Sit with that for a second.",
      "why": "Directly instructs the reader to pause and react, rather than letting the content do that work."
    },
    {
      "line": 432,
      "habit": "triad",
      "severity": "high",
      "quote": "Deny-by-default failed loudly, in development, on the safe side.",
      "why": "Three adverbial clauses stacked for rhythm rather than because three distinct facts were needed."
    },
    {
      "line": 433,
      "habit": "closer",
      "severity": "high",
      "quote": "That is the entire argument for it in one incident.",
      "why": "A summary line built to tell the reader what the anecdote meant, capping the section."
    },
    {
      "line": 446,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It is the wrong channel.",
      "why": "A very short sentence placed right after the setup to create a reveal."
    },
    {
      "line": 447,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "But nothing broke.",
      "why": "A second short sentence in the same paragraph placed for contrast and pause."
    },
    {
      "line": 448,
      "habit": "antithesis",
      "severity": "high",
      "quote": "What the model needs to know is not that it failed, but what to do differently.",
      "why": "Textbook \"not X, but Y\" construction knocking down one framing for another."
    },
    {
      "line": 461,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Two fields, two audiences.",
      "why": "A verbless, parallel \"two X, two Y\" phrase standing in for a sentence."
    },
    {
      "line": 463,
      "habit": "closer",
      "severity": "medium",
      "quote": "The result is not an error, so nothing downstream treats it as a transient failure to retry.",
      "why": "A tidy line that tells the reader what the guard/reason distinction just described means, landing the paragraph."
    },
    {
      "line": 497,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "an amount that surprises people",
      "why": "A claim about magnitude and reaction with no real specifics; the passage needs a real detail from the author about the amount and who was surprised."
    },
    {
      "line": 503,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Honest answer, for the case you are probably imagining: no.",
      "why": "A verbless lead-in standing in for a sentence before the actual answer."
    },
    {
      "line": 512,
      "habit": "fragment",
      "severity": "medium",
      "quote": "A colleague who does not write SQL, an agent running unattended, a client with no shell.",
      "why": "A verbless run of three noun phrases standing in for a sentence."
    },
    {
      "line": 518,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Note that none of those three is about the protocol.",
      "why": "Opens on \"Note that,\" telling the reader what to notice instead of letting it be evident."
    },
    {
      "line": 520,
      "habit": "restatement",
      "severity": "low",
      "quote": "That is the problem it exists to solve",
      "why": "Restates the point just made about writing the server once for every client, without adding to it."
    },
    {
      "line": 528,
      "habit": "antithesis",
      "severity": "low",
      "quote": "Build a server, not a client.",
      "why": "An \"X, not Y\" contrast used as a list lead-in, part of a repeated pattern across the piece."
    },
    {
      "line": 531,
      "habit": "antithesis",
      "severity": "low",
      "quote": "Test the round trip, not the registration.",
      "why": "Another \"X, not Y\" contrast used as a list lead-in, echoing the same shape used elsewhere."
    }
  ]
}
```

Antithesis and fragment are the two habits that recur most, each showing up roughly six times: antithesis clusters around "The answer that does not have to anticipate" and "The second thing I got wrong: refusals" sections, then resurfaces in the two closing tips lists ("Build a server, not a client," "Test the round trip, not the registration"); fragment clusters in the opening paragraph, the same two sections, and the "Was the server worth building" section. Dramatic-beat, closer, and triad each appear as single sharp, high-confidence instances concentrated in the "It failed on my own code first" and "refusals" sections. Hedge appears twice, both early, in the standfirst and the first numbered section. generic-detail appears once, late, in the cap section's unquantified claim about surprise.
