```json
{
 "findings": [
  {
   "line": 270,
   "habit": "generic-detail",
   "severity": "medium",
   "quote": "there is far too much text",
   "why": "the phrase 'far too' is vague and does not provide a specific detail about the extent of the text."
  },
  {
   "line": 292,
   "habit": "generic-detail",
   "severity": "medium",
   "quote": "which is worse than useless, because it looks like an answer",
   "why": "the phrase 'worse than useless' is vague and does not provide a specific detail about the impact of the cut."
  },
  {
   "line": 407,
   "habit": "cliche-emphasis",
   "severity": "high",
   "quote": "That last row is the one most write-ups get wrong, by listing it alongside the others as though it were another way to cut. It is not.",
   "why": "The phrase 'most write-ups get wrong' is a cliché used to emphasize the importance of the statement, which can distract from the actual content."
  },
  {
   "line": 488,
   "habit": "fragment",
   "severity": "medium",
   "quote": "RECALL · PRECISION · IoU",
   "why": "The phrase 'RECALL · PRECISION · IoU' is a fragment standing in for a sentence or set of related sentences."
  },
  {
   "line": 683,
   "habit": "antithesis",
   "severity": "high",
   "quote": "We assumed it meant <em>the smallest set of chunks that covers the answer</em>. It actually means <em>every chunk containing any part of the answer</em>.",
   "why": "The draft sets up a single idea (the smallest set of chunks) and immediately knocks it down for a different one (every chunk containing any part of the answer), creating an antithesis."
  },
  {
   "line": 708,
   "habit": "dramatic-beat",
   "severity": "low",
   "quote": "The wrong version would have passed every test we thought to write, looked entirely reasonable, and quietly recommended turning overlap up.",
   "why": "A very short sentence placed to create a pause or reveal, which isn't necessary for the content."
  },
  {
   "line": 710,
   "habit": "dramatic-beat",
   "severity": "low",
   "quote": "The wrong version would have passed every test we thought to write, looked entirely reasonable, and quietly recommended turning overlap up.",
   "why": "A very short sentence placed to create a pause or reveal, which isn't necessary for the content."
  },
  {
   "line": 757,
   "habit": "fragment",
   "severity": "low",
   "quote": "A chunker that drops a trailing paragraph produces a run that succeeds and scores that look fine.",
   "why": "The sentence starts with a fragment that lacks a verb and a subject."
  },
  {
   "line": 783,
   "habit": "fragment",
   "severity": "low",
   "quote": "It is an obvious question and a surprisingly rare one to ask.",
   "why": "The sentence starts with a fragment that lacks a verb and a subject."
  },
  {
   "line": 795,
   "habit": "fragment",
   "severity": "low",
   "quote": "Reporting that as evidence that cheap screening works would be reporting arithmetic.",
   "why": "The sentence starts with a fragment that lacks a verb and a subject."
  },
  {
   "line": 864,
   "habit": "emphasis-word",
   "severity": "high",
   "quote": "a result like this is about a pairing, never about the signal on its own.",
   "why": "The use of 'never' emphasizes the point without adding new information."
  },
  {
   "line": 879,
   "habit": "fragment",
   "severity": "medium",
   "quote": "Everything above ranks chunking strategies against questions with marked answers.",
   "why": "This sentence begins with a fragment, lacking a subject."
  },
  {
   "line": 888,
   "habit": "triad",
   "severity": "low",
   "quote": "sorted three times, by what the question happened to be asking for.",
   "why": "The sentence uses three adjectives to describe the sorting, which is likely a habit."
  },
  {
   "line": 922,
   "habit": "cliche-emphasis",
   "severity": "high",
   "quote": "‘self-contained’ is the one that moves",
   "why": "Using 'the one that' to emphasize the importance of a word is a cliché."
  },
  {
   "line": 964,
   "habit": "reader-instruction",
   "severity": "low",
   "quote": "‘There is no search engine yet’",
   "why": "Opening a sentence with 'This one' suggests to the reader how to think about the problem."
  },
  {
   "line": 964,
   "habit": "reader-instruction",
   "severity": "low",
   "quote": "‘Nobody has asked anything yet’",
   "why": "Opening a sentence with 'This one' suggests to the reader how to think about the problem."
  },
  {
   "line": 969,
   "habit": "restatement",
   "severity": "medium",
   "quote": "This one turns out not to be a problem, and it is the reason Precision Ω is the number this whole piece is built around. It is computed from the cuts and the marked answers alone — no retriever is involved at any point. You can compute it the moment you can chunk a document. The same goes for every cheap check: none of them has ever needed a search engine.",
   "why": "The second sentence repeats the same point as the first, adding no new information."
  },
  {
   "line": 981,
   "habit": "restatement",
   "severity": "medium",
   "quote": "Some faults are faults for every question. Text that landed in no chunk at all is lost whatever anyone asks. A chunk too large for the embedding model is silently truncated for everybody. A code example cut in half is broken universally. You can rule those out on day one, for free, and it is worth doing before anything else — most first attempts have at least one.",
   "why": "The second sentence repeats the same point as the first, adding no new information."
  },
  {
   "line": 984,
   "habit": "restatement",
   "severity": "medium",
   "quote": "You can rule those out on day one, for free, and it is worth doing before anything else — most first attempts have at least one.",
   "why": "The second sentence repeats the same point as the first, adding no new information."
  },
  {
   "line": 987,
   "habit": "restatement",
   "severity": "medium",
   "quote": "You know more about the questions than you think. You know whether you are building a support bot that answers narrow factual lookups, or a research assistant that has to pull threads across sections. Look at the table above: that single piece of knowledge moves a strategy between first and thirteenth. It is worth more than any amount of parameter tuning, and it is available before you write a line.",
   "why": "The second sentence repeats the same point as the first, adding no new information."
  },
  {
   "line": 994,
   "habit": "restatement",
   "severity": "medium",
   "quote": "You can manufacture questions, at increasing fidelity. Write a few documents where you plant the answers yourself, so their positions are known exactly — free and immediate. Then have a model read your real documents and write questions about them — one bill, once, after which the question set is a file you keep forever. Then, once you have traffic, use what people actually asked. Each step is closer to the truth and none of them blocks shipping.",
   "why": "The second sentence repeats the same point as the first, adding no new information."
  },
  {
   "line": 1013,
   "habit": "cliche-emphasis",
   "severity": "high",
   "quote": "Ask the model to quote the answer word for word, then go and find that quote in the document yourself.",
   "why": "Using 'word for word' to emphasize the importance of exact quoting is a cliché."
  },
  {
   "line": 1031,
   "habit": "fragment",
   "severity": "medium",
   "quote": "kept quote found in the document, position verified",
   "why": "A verbless phrase standing in for a sentence."
  },
  {
   "line": 1037,
   "habit": "fragment",
   "severity": "medium",
   "quote": "A 25% yield",
   "why": "A verbless phrase standing in for a sentence."
  },
  {
   "line": 1040,
   "habit": "cliche-emphasis",
   "severity": "high",
   "quote": "The two questions that survived are exactly right.",
   "why": "Using 'exactly' to emphasize the absolute nature of the result is a cliché."
  },
  {
   "line": 1078,
   "habit": "fragment",
   "severity": "medium",
   "quote": "Change the chunking with the search engine held still; change the search engine with the chunking held still; see how far each one moves the score.",
   "why": "The sentence consists of a series of verbless phrases that parallel each other."
  },
  {
   "line": 1156,
   "habit": "generic-detail",
   "severity": "high",
   "quote": "Fix the chunking first, because it always pays. But don’t assume the search engine is settled — when it goes wrong it doesn’t go slightly wrong.",
   "why": "The phrase 'it always pays' is vague and lacks specific details that would make the point more concrete."
  },
  {
   "line": 1169,
   "habit": "cliche-emphasis",
   "severity": "medium",
   "quote": "worth saying out loud, because that paragraph very nearly got written the other way.",
   "why": "The phrase 'worth saying out loud' is a stock expression used to emphasize a point."
  },
  {
   "line": 1278,
   "habit": "cliche-emphasis",
   "severity": "high",
   "quote": "And the headline number hides the more useful difference.",
   "why": "Uses 'the more useful difference' to emphasize importance without providing specific detail."
  },
  {
   "line": 1302,
   "habit": "reader-instruction",
   "severity": "medium",
   "quote": "The question that unstuck it wasn’t a better experiment. It was someone asking “is the problem how we’re asking?”",
   "why": "Uses 'asking' to instruct the reader on how to think about the issue."
  }
 ]
}
```

Lines 255 to 383: ### Summary
The most recurring habits in this section are `generic-detail`, where vague phrases are used instead of specific details. These can be found in the lines where the extent of the text and the impact of the cuts are described.

Lines 384 to 616: ### Summary
The most recurring habits in this section are `cliche-emphasis` and `fragment`. The phrase "most write-ups get wrong" is used to emphasize the importance of a statement, which can be distracting. Additionally, the phrase "RECALL · PRECISION · IoU" is a fragment used to introduce the concepts, which could be expanded into a full sentence.

Lines 617 to 735: ### Summary
The draft exhibits the habit of **antithesis** twice and the **dramatic-beat** once, with the latter being less noticeable. The antithesis habit is more prominent and noticeable.

Lines 736 to 800: ### Summary
The most recurring habit in this section is `fragment`, with several instances where verbless phrases are used to start sentences. These can be found in lines 757, 783, and 795.

Lines 801 to 919: ### Summary
The most recurring habits in this section are `emphasis-word` and `fragment`. The `triad` habit also appears but is less prominent. The habits cluster around key sentences that emphasize points and those beginning with fragments, which may disrupt the flow of the text.

Lines 920 to 1071: ### Summary
The draft in this section frequently uses habits such as `cliche-emphasis`, `reader-instruction`, and `restatement`. The most recurring habits are `cliche-emphasis`, followed closely by `restatement`. These habits are most noticeable in the `restatement` habit, where sentences repeat the same point, adding no new information. The `cliche-emphasis` habit is used to highlight the importance of certain phrases, which are often overused and lose their impact.

Lines 1072 to 1208: ### Summary
The draft exhibits recurring habits of fragment-like sentences, vague generic details, and cliché emphasis. These habits cluster in sections explaining the results of the experiments and the implications of the findings.

Lines 1209 to 1556: ### Summary
The most recurring habits are `cliche-emphasis` and `reader-instruction`. These habits cluster in sections discussing the significance of findings and guiding the reader's perspective.
