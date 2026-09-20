```json
{
 "findings": [
  {
   "line": 37,
   "habit": "generic-detail",
   "severity": "high",
   "quote": "The connections have to be separate, because one that has answered discover is locked into the new protocol, so asking it for a handshake afterwards tells you about the lock and nothing about the server.",
   "why": "The quote suggests that the state of a connection can tell us something about the server, but it doesn't provide any specific evidence or detail to support this."
  },
  {
   "line": 94,
   "habit": "generic-detail",
   "severity": "high",
   "quote": "Every server on a version-one SDK spoke only the old handshake, and every server on version two spoke both.",
   "why": "The quote makes a general claim without providing specific examples or details to support it."
  },
  {
   "line": 106,
   "habit": "generic-detail",
   "severity": "high",
   "quote": "I didn't find one that had implemented discovery by hand, or one on a v2 SDK that had turned it off.",
   "why": "The quote makes a general claim without providing specific examples or details to support it."
  },
  {
   "line": 149,
   "habit": "hedge",
   "severity": "high",
   "quote": "-32602 is the JSON-RPC code for calling a method that exists with the wrong arguments.",
   "why": "The phrase 'is the' softens a universal claim, making it unverifiable."
  },
  {
   "line": 172,
   "habit": "closer",
   "severity": "high",
   "quote": "A crashed server now reads as unreachable, exits with a failure code, and shows the tail of its stderr.",
   "why": "The sentence is a summary that reiterates the main point of the section."
  },
  {
   "line": 183,
   "habit": "triad",
   "severity": "medium",
   "quote": "A server that never answers at all times out twice.",
   "why": "The sentence uses three items to conclude a point, even though two would suffice."
  },
  {
   "line": 208,
   "habit": "reader-instruction",
   "severity": "low",
   "quote": "I also haven't probed anything running on someone else's infrastructure, because that means sending requests to their endpoints and I haven't decided to do that yet.",
   "why": "The sentence tells the reader how to think about the decision not to probe."
  }
 ]
}
```

Lines 9 to 109: ### Summary

The most recurring habits in this section are `generic-detail`, where vague claims are made without specific supporting details. These habits cluster in lines 37, 94, and 106.

Lines 110 to 236: ### Summary
The most recurring habits in this section are `hedge` and `closer`. These habits cluster around summarizing or generalizing points that could be more specific or direct.
