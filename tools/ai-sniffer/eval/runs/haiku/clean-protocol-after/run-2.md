```json
{
  "findings": [
    {
      "line": 164,
      "habit": "antithesis",
      "severity": "high",
      "quote": "the probe exited successfully. In fact it had died on startup before answering anything",
      "why": "Sets up one result then immediately knocks it down with a reversal, creating a dramatic surprise"
    },
    {
      "line": 186,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "I'd concluded that the Python servers' error code and message contradicted each other, because the message read \"Invalid request\". My own summary script had cut every message at 40 characters, and the full text was \"Invalid request parameters\", which matches the code.",
      "why": "Sets up one conclusion then knocks it down by revealing fuller facts that show the opposite"
    },
    {
      "line": 153,
      "habit": "antithesis",
      "severity": "low",
      "quote": "I'd call it the likely mechanism rather than a proven one",
      "why": "Uses the \"not X, but Y\" structure even though hedged with acknowledgment of uncertainty"
    },
    {
      "line": 209,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "I also haven't probed anything running on someone else's infrastructure, because that means sending requests to their endpoints and I haven't decided to do that yet.",
      "why": "The decision criteria is unspecified; what would need to change for the author to decide differently"
    }
  ]
}
```

The draft relies on antithetical structures across multiple sections, reaching for "not X, but Y" three times. A deferred decision about probing remote infrastructure is mentioned without explaining what the pending decision criteria actually is.
