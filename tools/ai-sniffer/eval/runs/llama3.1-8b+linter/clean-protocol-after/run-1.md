I'll go through the draft and quote the habits I find.

**Word-level habits**

Using the linter report, I'll start by finding the word-level habits. According to the report, the following habits are present:

1. `emphasis-word`: "exactly" (line 26)
2. `emphasis-word`: "actually" (line 47)
3. `hedge`: "nearly any" (line 159)

**Structural habits**

Now, I'll move on to finding structural habits. I'll review the draft and quote the habits I find.

1. **Antithesis**: "You can't find out by connecting" (lines 24-30)
	* Setting up an idea and then knocking it down with another idea.
	* Quote: "Those last two have to stay apart, because a server that never answered hasn't told you anything about which protocol it speaks." (line 43)
2. **Fragment**: "The Python v2 SDK's own negotiation falls back on nearly any error" (line 159)
	* Verbless phrases standing in for sentences.
	* Quote: "nearly any error" (line 159)
3. **Triad**: "The servers that don't speak July turn it down in two different ways, and the split follows the SDK again" (lines 131-133)
	* Three items (ways) presented as a finished product.
	* Quote: "two different ways, and the split follows the SDK again" (line 132)
4. **Dramatic-beat**: "It doesn't know `server/discover` exists, and says so correctly" (line 69)
	* A short sentence or one-line paragraph used to create a pause or reveal.
	* Quote: "It doesn't know `server/discover` exists, and says so correctly" (line 69)
5. **Closer**: "Written against MCP protocol revision 2026-07-28" (line 234)
	* A section or paragraph ending built to land a point.
	* Quote: "Written against MCP protocol revision 2026-07-28" (line 234)
6. **Restatement**: "I'd just built a server of my own on the new revision, and wanted to know which protocol everyone else's servers speak" (line 21)
	* The same point made twice in adjacent sentences, with the second sentence adding nothing.
	* Quote: "I'd just built a server of my own on the new revision, and wanted to know which protocol everyone else's servers speak" (line 21)
7. **Cliche-emphasis**: "The key insight" is not present, but "the whole point" is (line 8)
	* Stock phrases used to announce importance instead of showing it.
	* Quote: "Those last two have to stay apart, because a server that never answered hasn't told you anything about which protocol it speaks" (line 43)
8. **Generic-detail**: "The Python servers' error code and message contradicted each other" (line 186)
	* Vague phrases where real details belong.
	* Quote: "The Python servers' error code and message contradicted each other" (line 186)
9. **Reader-instruction**: "Sit with that for a second" is not present, but "The trouble is that the Python SDK's client, left on its default, does exactly the negotiation you're trying to observe" (line 26)
	* Sentences that tell the reader how to think or react.
	* Quote: "The trouble is that the Python SDK's client, left on its default, does exactly the negotiation you're trying to observe" (line 26)
10. **Hedge**: "nearly any" (line 159)
	* Universal claims softened so they can't be checked.
	* Quote: "nearly any error" (line 159)

**Findings**

Here is the JSON output:

```json
{
  "findings": [
    {
      "line": 43,
      "habit": "antithesis",
      "severity": "high",
      "quote": "Those last two have to stay apart, because a server that never answered hasn't told you anything about which protocol it speaks."
    },
    {
      "line": 159,
      "habit": "fragment",
      "severity": "medium",
      "quote": "nearly any error"
    },
    {
      "line": 132,
      "habit": "triad",
      "severity": "low",
      "quote": "two different ways, and the split follows the SDK again"
    },
    {
      "line": 69,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It doesn't know `server/discover` exists, and says so correctly"
    },
    {
      "line": 234,
      "habit": "closer",
      "severity": "high",
      "quote": "Written against MCP protocol revision 2026-07-28"
    },
    {
      "line": 21,
      "habit": "restatement",
      "severity": "low",
      "quote": "I'd just built a server of my own on the new revision, and wanted to know which protocol everyone else's servers speak"
    },
    {
      "line": 8,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "Those last two have to stay apart, because a server that never answered hasn't told you anything about which protocol it speaks"
    },
    {
      "line": 186,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "The Python servers' error code and message contradicted each other"
    },
    {
      "line": 26,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "The trouble is that the Python SDK's client, left on its default, does exactly the negotiation you're trying to observe"
    },
    {
      "line": 159,
      "habit": "hedge",
      "severity": "medium",
      "quote": "nearly any error"
    }
  ]
}
```

**Summary**

The most recurring habits are antithesis, fragment, triad, and closer. These habits are present throughout the draft, and they can be clustered together in the following sections:

* Section 1: "You can't find out by connecting" (antithesis, fragment)
* Section 2: "Twelve servers" (triad, fragment)
* Section 3: "The upgrade that bumping won't get you" (closer)
* Section 4: "Two ways to say you don't know a method" (fragment, triad)
* Section 5: "What running it on real servers taught me about the probe" (closer)
* Section 6: "Run it yourself" (closer)
* Section 7: "Loose ends" (closer)

Note that these sections are not strictly linear, and the habits can be found in multiple sections.