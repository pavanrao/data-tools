```json
{
  "findings": [
    {
      "line": 276,
      "habit": "hedge",
      "severity": "high",
      "quote": "Almost every SQL-over-MCP server decides whether a query is safe by reading the query.",
      "why": "A universal claim softened without naming the scope, making it impossible to check."
    },
    {
      "line": 309,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Consider what it must already handle correctly.",
      "why": "Sentence opens with an explicit instruction telling the reader to think about something."
    },
    {
      "line": 327,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "a keyword scan says no to a perfectly ordinary query",
      "why": "The word 'perfectly' is an intensifier adding stress but not information; 'ordinary query' stands alone."
    },
    {
      "line": 332,
      "habit": "antithesis",
      "severity": "high",
      "quote": "You can fix each of these. You cannot fix the category.",
      "why": "Sets up one idea and knocks it down with another across consecutive sentences."
    },
    {
      "line": 409,
      "habit": "closer",
      "severity": "medium",
      "quote": "The lesson survives the change of engine; the regex does not.",
      "why": "A memorable closing line of the callout section meant to land a point and stick with the reader."
    },
    {
      "line": 430,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Sit with that for a second.",
      "why": "An explicit instruction telling the reader to pause and sit with an idea."
    },
    {
      "line": 442,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "The protocol has a perfectly good error channel.",
      "why": "The word 'perfectly' is an intensifier; 'good error channel' conveys the same meaning."
    },
    {
      "line": 450,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "The server worked exactly as designed.",
      "why": "The word 'exactly' is an intensifier; 'as designed' is sufficient for the meaning."
    },
    {
      "line": 450,
      "habit": "antithesis",
      "severity": "high",
      "quote": "What the model needs to know is not that it failed, but what to do differently.",
      "why": "Classic 'not X, but Y' antithesis structure within a single sentence."
    },
    {
      "line": 433,
      "habit": "closer",
      "severity": "medium",
      "quote": "That is the entire argument for it in one incident.",
      "why": "A wrapping-up line that summarizes what was just said and tells the reader what the anecdote meant."
    },
    {
      "line": 518,
      "habit": "reader-instruction",
      "severity": "high",
      "quote": "Note that none of those three is about the protocol.",
      "why": "An explicit instruction telling the reader to keep something in mind."
    },
    {
      "line": 531,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "Listing your tools proves nothing about what a consumer actually reads.",
      "why": "The word 'actually' is an intensifier; 'what a consumer reads' is sufficient without it."
    }
  ]
}
```

Reader-instruction recurs most often (four instances), appearing as direct commands to the reader's attention. The piece also carries multiple emphasis-words and closers, mostly in medium-severity clusters within explained concepts. Two antitheses land clear contrasts. The hedge at the start softens the opening claim without scope.
