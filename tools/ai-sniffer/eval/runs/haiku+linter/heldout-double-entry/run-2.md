```json
{
  "findings": [
    {
      "line": 564,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "These are numbered because they genuinely are a sequence — each one consumes what the last produced.",
      "why": "The word 'genuinely' is an intensifier adding stress but no information; the context (numbered list) already establishes this is a sequence."
    },
    {
      "line": 706,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Note that it says ok on all eight, including ok, 0 chars for a three-page scanned document.",
      "why": "Explicitly tells the reader what to notice rather than letting the evidence speak for itself."
    },
    {
      "line": 631,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "It is therefore invisible to similarity search — there is literally nothing to rank.",
      "why": "The word 'literally' is a redundant intensifier; the sentence is clear without it."
    },
    {
      "line": 872,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Almost nothing checks that promise, and the failures are specifically the quiet kind — no crash, no warning, plausible output.",
      "why": "Softens a claim without specificity; 'almost nothing' lacks a referent for what systems do check."
    },
    {
      "line": 402,
      "habit": "hedge",
      "severity": "medium",
      "quote": "A great deal of extraction code opens a spreadsheet and reads the active sheet — whichever tab happened to be selected when the file was last saved.",
      "why": "Vague claim about prevalence; 'a great deal of' offers no measurable standard."
    },
    {
      "line": 410,
      "habit": "hedge",
      "severity": "medium",
      "quote": "The caveat in the footnote — frequently the sentence that changes the meaning — is never seen.",
      "why": "The claim about footnotes rests on an unspecified frequency; 'frequently' needs a scope."
    },
    {
      "line": 383,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Nearly every 'chat with your documents' product works roughly this way.",
      "why": "Softens the scope with 'nearly every' and 'roughly' both in one sentence, making the claim untestable."
    },
    {
      "line": 388,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "The trouble is entirely in step one, and it is invisible from step four.",
      "why": "The word 'entirely' emphasizes the logical contrast but carries little weight when stating a substantive claim about where the failure occurs."
    },
    {
      "line": 388,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "The trouble is entirely in step one, and it is invisible from step four.",
      "why": "Stands alone as a one-sentence paragraph, creating a pause for emphasis when the content could flow naturally into surrounding text."
    },
    {
      "line": 447,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "What's needed is not a confession. It's a checksum.",
      "why": "Sets up one idea and knocks it down for another across two sentences, a pattern that appears in context when functional explanation would serve the same purpose."
    },
    {
      "line": 344,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "That difference is the entire idea.",
      "why": "The phrase 'the entire idea' is stock language announcing importance; the reasoning that follows shows importance without the cliche."
    }
  ]
}
```

The draft clusters hedges (seven findings across lines 373–872), with the heaviest concentration in the RAG explanation section where claims about product ubiquity and footnote significance are softened without specificity. The dramatic-beat and antithesis habits appear in section endings, shaping conclusions for effect. The one high-severity finding is the word 'genuinely' in a context where the structure already establishes the point being made.
