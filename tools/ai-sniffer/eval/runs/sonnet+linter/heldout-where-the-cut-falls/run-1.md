```json
{
  "findings": [
    {
      "line": 269,
      "habit": "reader-instruction",
      "severity": "low",
      "quote": "Suppose you want a program to answer questions about your company's documents.",
      "why": "Opens the explainer by instructing the reader to imagine a hypothetical, the same move as the catalogue's \"Consider\"/\"Imagine\" openings."
    },
    {
      "line": 576,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Notice what overlap does — it is supposed to stop answers being severed, and it does, but every extra copy of the text is more padding you have to carry.",
      "why": "Tells the reader to notice something rather than letting the observation stand on its own."
    },
    {
      "line": 706,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Look at the last column.",
      "why": "Directly instructs the reader where to look, the first of three near-identical \"Look at\" instances."
    },
    {
      "line": 989,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Look at the table above: that single piece of knowledge moves a strategy between first and thirteenth.",
      "why": "Second occurrence of the same \"Look at\" instruction, showing it is a recurring habit rather than a one-off."
    },
    {
      "line": 1200,
      "habit": "reader-instruction",
      "severity": "medium",
      "quote": "Look at the last row.",
      "why": "Third occurrence of the same \"Look at\" instruction across the piece."
    },
    {
      "line": 274,
      "habit": "hedge",
      "severity": "low",
      "quote": "Most systems default to something arbitrary: every 800 characters, say.",
      "why": "\"Most systems\" is an unnamed universal group, softening a claim the piece never checks against a count."
    },
    {
      "line": 1334,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Raising it almost always raises recall and always lowers precision, so a score quoted without its k means nothing.",
      "why": "\"Almost always\" softens a universal claim without naming what the exceptions are."
    },
    {
      "line": 1428,
      "habit": "hedge",
      "severity": "medium",
      "quote": "Here: chunk size affects almost everything, so the useful question is what a signal tells you after you already know how big the chunks are.",
      "why": "\"Almost everything\" is a sweeping claim with no named scope, so it can't be checked."
    },
    {
      "line": 606,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "completely useless",
      "why": "\"Completely\" stresses \"useless\" without adding anything the sentence hasn't already said."
    },
    {
      "line": 706,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "and overlap is precisely the setting people reach for when answers keep getting severed",
      "why": "\"Precisely\" here means \"specifically,\" adding stress rather than the precision the word usually claims."
    },
    {
      "line": 708,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "looked entirely reasonable, and quietly recommended turning overlap up",
      "why": "\"Entirely\" intensifies \"reasonable\" without adding information."
    },
    {
      "line": 768,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "“good chunking” is only defined relative to the questions people actually ask",
      "why": "First of three near-identical uses of \"actually ask(ed)\" across the piece, where \"actually\" adds no information beyond \"ask.\""
    },
    {
      "line": 853,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "shrinking that is exactly what raises a precision ceiling",
      "why": "\"Exactly\" stresses the causal claim without sharpening it further."
    },
    {
      "line": 998,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "Then, once you have traffic, use what people actually asked.",
      "why": "Second occurrence of the recurring \"actually ask(ed)\" phrase."
    },
    {
      "line": 1040,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "The two questions that survived are exactly right.",
      "why": "\"Exactly right\" intensifies an already plain claim without adding precision."
    },
    {
      "line": 1201,
      "habit": "emphasis-word",
      "severity": "high",
      "quote": "That is a genuinely interesting claim — bigger models being worse at copying text exactly",
      "why": "\"Genuinely\" is inserted to pre-validate the claim's interest rather than demonstrate it, the exact word the catalogue names."
    },
    {
      "line": 1218,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "And a slightly reworded quote reads perfectly well.",
      "why": "\"Perfectly\" intensifies \"well\" for rhetorical contrast without adding information."
    },
    {
      "line": 1220,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "That is also exactly why it looked like a size effect.",
      "why": "\"Exactly\" adds stress to a causal claim that doesn't need it."
    },
    {
      "line": 1298,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "this one produced a clean, plausible, publishable result that was entirely wrong",
      "why": "\"Entirely\" intensifies \"wrong\" after a stack of three adjectives has already done the emphatic work."
    },
    {
      "line": 1421,
      "habit": "emphasis-word",
      "severity": "medium",
      "quote": "The distribution of things people actually ask — narrow lookups, comparisons across a document, open synthesis.",
      "why": "Third occurrence of the same \"actually ask\" tic, confirming a pattern rather than a single word choice."
    },
    {
      "line": 375,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "Which means it is something to measure, not something to have an opinion about.",
      "why": "Sets up \"opinion\" only to dismiss it in favor of \"measure,\" the not-X-but-Y move."
    },
    {
      "line": 606,
      "habit": "antithesis",
      "severity": "high",
      "quote": "Perfect recall, and completely useless: to answer “when does the Northeast file?” it hands over the entire speech.",
      "why": "Sets up a seemingly perfect score only to immediately knock it down as useless."
    },
    {
      "line": 683,
      "habit": "antithesis",
      "severity": "high",
      "quote": "We assumed it meant the smallest set of chunks that covers the answer. It actually means every chunk containing any part of the answer.",
      "why": "Textbook two-sentence \"we thought X. It actually means Y\" reversal, matching the catalogue's split-sentence form exactly."
    },
    {
      "line": 733,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "It is a real trade, not a safety setting to leave on.",
      "why": "Knocks down the implied framing (\"safety setting\") in favor of \"real trade.\""
    },
    {
      "line": 772,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "That was our claim before we tested it. Then we tested it, and it survived — but not for the reason we expected.",
      "why": "Sets up confirmation of a claim, then undercuts the reason for it with the same knock-down shape."
    },
    {
      "line": 806,
      "habit": "antithesis",
      "severity": "high",
      "quote": "A correlation near zero is not evidence of no relationship — it can be two relationships in opposite directions.",
      "why": "Explicit \"not X — it can be Y\" construction."
    },
    {
      "line": 852,
      "habit": "antithesis",
      "severity": "high",
      "quote": "The signal is fine. The score was the wrong thing to check it against.",
      "why": "Two-sentence reversal that moves blame from the signal to the score."
    },
    {
      "line": 1039,
      "habit": "antithesis",
      "severity": "medium",
      "quote": "It is a measurement of how much you lost, not a corruption you never noticed.",
      "why": "\"Not X\" knock-down appended after asserting the actual claim."
    },
    {
      "line": 1063,
      "habit": "antithesis",
      "severity": "high",
      "quote": "If it does not tell you which, it is not a simpler answer — it is the same answer with the assumption hidden.",
      "why": "The final sentence of the entire piece, built entirely on the not-X-it-is-Y shape."
    },
    {
      "line": 1146,
      "habit": "antithesis",
      "severity": "high",
      "quote": "The two are not big and small. They are frequent and rare.",
      "why": "Parallel two-sentence negation-then-assertion opening a figure caption."
    },
    {
      "line": 1161,
      "habit": "antithesis",
      "severity": "high",
      "quote": "It didn’t degrade. It collapsed.",
      "why": "Two clipped sentences, negate then assert, the sharpest instance of the pattern in the piece."
    },
    {
      "line": 527,
      "habit": "fragment",
      "severity": "high",
      "quote": "Same document, same answer, different denominator.",
      "why": "Three verbless parallel phrases standing in for a sentence."
    },
    {
      "line": 955,
      "habit": "fragment",
      "severity": "high",
      "quote": "One document, three right answers.",
      "why": "Verbless parallel phrase opening a figure caption, the same construction as the other fragment instance."
    },
    {
      "line": 980,
      "habit": "triad",
      "severity": "medium",
      "quote": "Text that landed in no chunk at all is lost whatever anyone asks. A chunk too large for the embedding model is silently truncated for everybody. A code example cut in half is broken universally.",
      "why": "Three parallel sentences share the same \"X is Y-ed for everyone\" shape, sounding finished rather than reflecting exactly three cases."
    },
    {
      "line": 1166,
      "habit": "triad",
      "severity": "medium",
      "quote": "It reads well, it fits the two worst cases, and it is not true",
      "why": "Three short clauses in a row building to the same reveal."
    },
    {
      "line": 1300,
      "habit": "triad",
      "severity": "medium",
      "quote": "this one produced a clean, plausible, publishable result that was entirely wrong",
      "why": "Three stacked adjectives where one or two would carry the point."
    },
    {
      "line": 407,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "It is not.",
      "why": "A two-word sentence inserted mid-paragraph purely for a pause before the actual correction."
    },
    {
      "line": 473,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It is a ceiling.",
      "why": "Short declarative sentence isolated between longer ones purely to land the definition dramatically."
    },
    {
      "line": 1073,
      "habit": "dramatic-beat",
      "severity": "medium",
      "quote": "Fair challenge.",
      "why": "Two-word sentence opening the section as a staged concession before the real content."
    },
    {
      "line": 1162,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It collapsed.",
      "why": "One-line paragraph-like beat placed for dramatic reveal right after the setup sentence."
    },
    {
      "line": 1205,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It was our fault.",
      "why": "Three-word standalone paragraph placed purely for a confessional pause, a near-exact match to the catalogue's own example."
    },
    {
      "line": 608,
      "habit": "closer",
      "severity": "medium",
      "quote": "You have to measure inside the chunk to see the problem at all.",
      "why": "Ends the section by telling the reader what the example meant, rather than letting it stand."
    },
    {
      "line": 713,
      "habit": "closer",
      "severity": "high",
      "quote": "The one check that could catch this, and it cost a 1.6 MB download.",
      "why": "Styled as a pull-quote aphorism landing the section's point in one line."
    },
    {
      "line": 743,
      "habit": "closer",
      "severity": "high",
      "quote": "Which is the entire argument for measuring rather than choosing: the ranking depends on your corpus, so it has to be computed on your corpus.",
      "why": "Explicitly frames itself as the whole argument in one closing sentence."
    },
    {
      "line": 1222,
      "habit": "closer",
      "severity": "high",
      "quote": "The apparent finding about model size was a finding about our configuration, wearing a costume.",
      "why": "Closes the section with a summary metaphor that tells the reader exactly what to take away."
    },
    {
      "line": 1063,
      "habit": "closer",
      "severity": "high",
      "quote": "If it does not tell you which, it is not a simpler answer — it is the same answer with the assumption hidden.",
      "why": "The final sentence of the entire piece, built as a closing aphorism that tells the reader what it all meant."
    },
    {
      "line": 1462,
      "habit": "closer",
      "severity": "medium",
      "quote": "None of that was available by reasoning about it.",
      "why": "Closes the final section with a one-line statement of what the measurements meant."
    },
    {
      "line": 303,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "the whole argument of this piece is about isolating one of them",
      "why": "Announces scope and importance through a stock self-reference rather than showing it."
    },
    {
      "line": 1075,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "this whole piece is advice about the wrong knob",
      "why": "Same self-referential \"whole piece\" framing recurring a second time."
    },
    {
      "line": 915,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "a ranking that hides its question mix is the thing this whole section is warning about",
      "why": "Third recurrence of the \"whole piece/section/argument\" framing, confirming it as a tic."
    },
    {
      "line": 721,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "Three things, none of which is what the marketing around this topic suggests.",
      "why": "\"The marketing around this topic\" gestures at a claim being refuted without naming a source or example; the passage needs a real specific from the author about what that marketing actually says."
    },
    {
      "line": 984,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "and it is worth doing before anything else — most first attempts have at least one",
      "why": "Asserts a frequency claim about \"most first attempts\" with no count or source, unlike the piece's usual sourced numbers; the passage needs a real specific from the author."
    },
    {
      "line": 1169,
      "habit": "generic-detail",
      "severity": "low",
      "quote": "Worth saying out loud, because that paragraph very nearly got written the other way.",
      "why": "A claim about how close the paragraph came to being written differently, with no detail on what that version would have said; needs a real specific from the author."
    },
    {
      "line": 1180,
      "habit": "generic-detail",
      "severity": "low",
      "quote": "One more, because it is the most useful mistake in this whole piece and it very nearly got published as a result.",
      "why": "A claim about how close the piece came to publishing a mistake, with no detail on what would have been published or how close it came; needs a real specific from the author."
    }
  ]
}
```

Antithesis and emphasis-word are the two habits that recur most (eleven and twelve instances), and together they dominate the back half of the piece: the correction-heavy sections from "The part where we got it wrong" through "The bug that looked like a discovery," plus the closing section, are built almost entirely out of "we assumed X, it actually means Y" reversals and intensifiers like "exactly," "genuinely," and "entirely" that add stress without information. Closer and dramatic-beat cluster in the same stretch, since each reveal is staged with a short standalone sentence ("It is a ceiling.", "It was our fault.", "It collapsed.") and then summed up in an aphoristic closing line. Reader-instruction shows up as the same "Look at ___" cue three separate times, and a self-referential "the whole piece/argument/section is about X" phrase recurs four times as a cliche-emphasis tic. Generic-detail is comparatively rare, but the two "very nearly got written/published" asides are vague process claims with no real specifics behind them.
