```json
{
  "findings": [
    {
      "line": 288,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It didn't.",
      "why": "A two-word sentence dropped in mid-paragraph to land a reveal about where the time actually went, when the next sentence could have carried the information on its own."
    },
    {
      "line": 331,
      "habit": "closer",
      "severity": "medium",
      "quote": "The server keeps returning results and you keep believing it's read-only.",
      "why": "Ends the section's paragraph with a tidy line that tells the reader what the preceding examples mean, rather than just adding the last fact."
    },
    {
      "line": 343,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Not a flag your code consults later — the handle can't write, in the same way a file opened for reading can't be written to.",
      "why": "Sets up a rejected framing (\"not a flag\") only to knock it down with the real one, the not-X-but-Y move."
    },
    {
      "line": 404,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "On a warehouse that's a read-only role granted on a narrow set of views, not a string check in your server.",
      "why": "States the right approach, then dismisses the alternative with \"not,\" the same knock-down shape run in reverse order."
    },
    {
      "line": 406,
      "habit": "fragment",
      "severity": "high",
      "quote": "Same idea, different engine.",
      "why": "A verbless two-part phrase standing in for a sentence, placed for rhythm rather than because it needed to be terse."
    },
    {
      "line": 406,
      "habit": "closer",
      "severity": "high",
      "quote": "Same idea, different engine.",
      "why": "Closes the callout box with a pithy, aphoristic line that summarizes the point instead of adding to it."
    },
    {
      "line": 414,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It got refused.",
      "why": "A short, isolated sentence used as a beat before the explanation, when the next sentence already supplies the specifics."
    },
    {
      "line": 422,
      "habit": "fragment",
      "severity": "medium",
      "quote": "No mention of which action, which table, or which pragma.",
      "why": "A verbless phrase standing in for a full sentence, echoing the parallel list shape used earlier in the piece."
    },
    {
      "line": 427,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "actually",
      "why": "Adds stress to the explanation without adding information about what is going on."
    },
    {
      "line": 439,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "I'd have shipped it and never known.",
      "why": "A short, isolated admission placed for effect right before the section's summarizing line."
    },
    {
      "line": 440,
      "habit": "closer",
      "severity": "medium",
      "quote": "Instead the allowlist broke my own code in development, which is the cheapest place for it to break.",
      "why": "Ends the section by explicitly stating what the anecdote meant, rather than letting the anecdote stand."
    },
    {
      "line": 448,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "perfectly",
      "why": "Intensifies \"good\" without adding any information about the error channel."
    },
    {
      "line": 456,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "But nothing broke.",
      "why": "A blunt three-word sentence dropped in right after describing what a reader would expect, used purely to create a turn."
    },
    {
      "line": 456,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "exactly",
      "why": "Stresses correctness without adding information, stacked right after the short dramatic beat in the same paragraph."
    },
    {
      "line": 457,
      "habit": "antithesis",
      "severity": "high",
      "quote": "The model doesn't need to know that the call failed; it needs to know what to do differently.",
      "why": "A clean not-X-but-Y construction split across a semicolon, rejecting one framing of the model's need for another."
    },
    {
      "line": 472,
      "habit": "closer",
      "severity": "medium",
      "quote": "Since the result isn't an error, nothing downstream treats it as a blip worth retrying.",
      "why": "Wraps up the explanation with a line that states the implication for the reader rather than a new fact."
    },
    {
      "line": 494,
      "habit": "antithesis",
      "severity": "high",
      "quote": "The cap isn't the interesting bit. What matters is that a truncated result which doesn't mention it was truncated is worse than no result at all, because the first page of an answer looks exactly like the entire answer.",
      "why": "Dismisses one idea (the cap) explicitly in order to install the real point (what matters), the not-X-but-Y move split across two sentences."
    },
    {
      "line": 516,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "I'd reached the same conclusion about a different tool in this project a few weeks ago and it applies here too.",
      "why": "Offered as supporting evidence but names neither the tool nor the conclusion; the passage needs a real specific from the author."
    },
    {
      "line": 529,
      "habit": "antithesis",
      "severity": "high",
      "quote": "None of those is really about MCP. They're about who's asking and how often.",
      "why": "The it-wasn't-X-it-was-Y shape split across two adjacent sentences."
    },
    {
      "line": 530,
      "habit": "closer",
      "severity": "medium",
      "quote": "What the protocol contributes is narrower: write the server once and every client can use it, which is genuinely the problem it exists to solve, and why the spec keeps comparing itself to the language server protocol.",
      "why": "Ends the section by declaring what the whole discussion boils down to."
    },
    {
      "line": 530,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "genuinely",
      "why": "Intensifies the claim about what the protocol solves without adding information."
    },
    {
      "line": 549,
      "habit": "triad",
      "severity": "medium",
      "quote": "Nothing errors, nothing warns, and the tool looks identical when you list it.",
      "why": "Three short parallel clauses in a row, giving the sentence a finished rhythm independent of whether three was the natural count."
    }
  ]
}
```

Antithesis and closer are the habits that recur most, five instances each, with dramatic-beat close behind at four; they cluster most heavily in "The guard's first victim was me" and the run from "How do you say no?" through "Was it worth building?" (lines 404-530), where several instances land in the same paragraph or even the same sentence as an emphasis-word flag. The word-level habits from the linter thinned out on review: both hedge candidates ("Nearly all," "arguably") read as the author's own honest, checkable estimates rather than unfalsifiable universal claims, and "Look at the statement" reads as narrating the naive algorithm rather than instructing the reader, so all three were dropped; one "exactly" (line 494) was also dropped because it describes a genuinely exact resemblance. Generic-detail appears once, in the unnamed "different tool" reference, which is the one habit here that only the author can fix.
