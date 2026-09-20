```json
{
  "findings": [
    {
      "line": 288,
      "habit": "antithesis",
      "severity": "low",
      "quote": "I assumed the time would go on the protocol. It didn't.",
      "why": "Sets up an expectation only to immediately knock it down, the two-sentence contradiction shape."
    },
    {
      "line": 288,
      "habit": "hedge",
      "severity": "low",
      "quote": "Nearly all",
      "why": "Softens a claim about the author's own time allocation that the author could have quantified."
    },
    {
      "line": 342,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Not a flag your code consults later — the handle can't write, in the same way a file opened for reading can't be written to.",
      "why": "Classic 'not X — Y' construction, denying one framing before asserting the real one."
    },
    {
      "line": 404,
      "habit": "antithesis",
      "severity": "low",
      "quote": "On a warehouse that's a read-only role granted on a narrow set of views, not a string check in your server.",
      "why": "States the answer then negates the alternative ('Y, not X'), the same contrast move in reverse order."
    },
    {
      "line": 406,
      "habit": "fragment",
      "severity": "medium",
      "quote": "Same idea, different engine.",
      "why": "Verbless parallel phrase standing in for a sentence, closing the callout."
    },
    {
      "line": 414,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It got refused.",
      "why": "A very short sentence inserted for a beat before the reveal that the author's own tool broke."
    },
    {
      "line": 422,
      "habit": "fragment",
      "severity": "medium",
      "quote": "No mention of which action, which table, or which pragma.",
      "why": "Verbless phrase listing three things, standing alone as a sentence."
    },
    {
      "line": 422,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "I spent a while assuming I'd broken the connection string.",
      "why": "\"A while\" stands in for a real duration only the author has; the passage needs that specific."
    },
    {
      "line": 427,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "actually",
      "why": "Intensifier that adds stress to the sentence without adding information."
    },
    {
      "line": 439,
      "habit": "closer",
      "severity": "medium",
      "quote": "Instead the allowlist broke my own code in development, which is the cheapest place for it to break.",
      "why": "Ends the section with a summarizing line that tells the reader what the anecdote meant."
    },
    {
      "line": 449,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "perfectly",
      "why": "Intensifies \"good\" without adding checkable content."
    },
    {
      "line": 454,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "An error tells a model that something broke, and the sensible response to something breaking is to try again. But nothing broke.",
      "why": "Builds up the error-channel framing across a full sentence, then knocks it down with a short contradiction."
    },
    {
      "line": 456,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "But nothing broke.",
      "why": "A three-word sentence placed as a pause before the explanation that follows."
    },
    {
      "line": 456,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "exactly",
      "why": "Adds emphasis to \"what it was built to do\" without adding information."
    },
    {
      "line": 456,
      "habit": "antithesis",
      "severity": "high",
      "quote": "The model doesn't need to know that the call failed; it needs to know what to do differently.",
      "why": "A textbook 'not X; Y' split across one sentence, denying one need before asserting the other."
    },
    {
      "line": 472,
      "habit": "closer",
      "severity": "low",
      "quote": "Since the result isn't an error, nothing downstream treats it as a blip worth retrying.",
      "why": "Ends the paragraph by tying back to the earlier point in a tidy summarizing line."
    },
    {
      "line": 494,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "The cap isn't the interesting bit. What matters is that a truncated result which doesn't mention it was truncated is worse than no result at all.",
      "why": "Dismisses one thing as uninteresting before asserting what actually matters, the same knock-down shape."
    },
    {
      "line": 505,
      "habit": "closer",
      "severity": "medium",
      "quote": "On Snowflake it's the whole bill — the compute dwarfs the token spend by more than people expect, and the agent's loop is what drives it.",
      "why": "Closes the section on a vivid, punchy line that lands the point about cost."
    },
    {
      "line": 523,
      "habit": "fragment",
      "severity": "high",
      "quote": "A colleague who doesn't write SQL, an agent running unattended, a client with no shell.",
      "why": "Three verbless noun phrases in a row standing in for a sentence."
    },
    {
      "line": 529,
      "habit": "antithesis",
      "severity": "high",
      "quote": "None of those is really about MCP. They're about who's asking and how often.",
      "why": "Directly matches the 'It wasn't X. It was Y.' shape across two adjacent sentences."
    },
    {
      "line": 530,
      "habit": "closer",
      "severity": "high",
      "quote": "What the protocol contributes is narrower: write the server once and every client can use it, which is genuinely the problem it exists to solve, and why the spec keeps comparing itself to the language server protocol.",
      "why": "A definitive, summarizing line that closes the section by telling the reader what the protocol's contribution really is."
    },
    {
      "line": 531,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "genuinely",
      "why": "Intensifies the claim about the problem without adding checkable content."
    },
    {
      "line": 561,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "I haven't run it.",
      "why": "A short, separated sentence placed for effect after the preceding sentence already implied it."
    },
    {
      "line": 580,
      "habit": "closer",
      "severity": "high",
      "quote": "If a tutorial you're reading mentions either, it predates this.",
      "why": "The last line of the piece, built to land a final, clever-sounding point."
    }
  ]
}
```

Antithesis is the habit that recurs most: seven instances across the piece, from the opening paragraph ("I assumed... It didn't.") through a dense cluster in the "How do you say no?" section (lines 454–458, which stacks a setup-knockdown pair with a second, near-textbook "doesn't need X; needs Y" construction) to the "Was it worth building?" section (line 529). The closer habit is nearly as pervasive: almost every section, and the piece itself, ends on a deliberately landing line (lines 331, 439, 472, 505, 530, 580). Emphasis-words ("actually," "perfectly," "exactly," "genuinely") are spread evenly through the middle and back half rather than clustered. Fragments and the one generic-detail instance are comparatively rare, appearing mainly in the "victim was me" and "Was it worth building?" sections.
