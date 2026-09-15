```json
{
 "findings": [
  {
   "line": 276,
   "habit": "generic-detail",
   "severity": "medium",
   "quote": "That works fine, right up until a cut lands in the middle of the sentence that holds the answer.",
   "why": "This sentence is vague and could benefit from a specific example or detail."
  },
  {
   "line": 292,
   "habit": "generic-detail",
   "severity": "medium",
   "quote": "which is worse than useless, because it looks like an answer.",
   "why": "This sentence is vague and could be improved by providing more specific details."
  },
  {
   "line": 399,
   "habit": "triad",
   "severity": "medium",
   "quote": "the document's own markup — headings, tables, code fences",
   "why": "Three items listed in a row to describe the same concept."
  },
  {
   "line": 406,
   "habit": "closer",
   "severity": "high",
   "quote": "Only the bottom row separates the two units.",
   "why": "A sentence ending summarizing the point, which is the entire argument of the paragraph."
  },
  {
   "line": 476,
   "habit": "closer",
   "severity": "high",
   "quote": "That number has a name — Precision Ω, “precision omega”.",
   "why": "A sentence ending with a summary of the point, which is the entire argument of the paragraph."
  },
  {
   "line": 528,
   "habit": "closer",
   "severity": "high",
   "quote": "The top three change if you swap the retriever, tune the query, or ask for more chunks — so they measure the whole system.",
   "why": "A sentence ending with a summary of the point, which is the entire argument of the paragraph."
  },
  {
   "line": 685,
   "habit": "antithesis",
   "severity": "high",
   "quote": "Those are the same thing — right up until chunks overlap, at which point the second is larger and the score is lower.",
   "why": "The sentence sets up the idea of the two readings being the same and then immediately contradicts it, creating a false antithesis."
  },
  {
   "line": 711,
   "habit": "triad",
   "severity": "medium",
   "quote": "With no overlap it is almost exactly right. With overlap it is about 28% too high — and overlap is precisely the setting people reach for when answers keep getting severed.",
   "why": "Three separate clauses are used to describe the relationship between overlap and the score, which is unnecessary and creates a triad."
  },
  {
   "line": 740,
   "habit": "cliche-emphasis",
   "severity": "medium",
   "quote": "it wins <em>enormously</em> (81.9 against 69.5 on one benchmark).",
   "why": "The phrase 'enormously' is a cliché used to emphasize a large difference, but it's too vague to convey the actual magnitude."
  },
  {
   "line": 743,
   "habit": "closer",
   "severity": "high",
   "quote": "Which is the entire argument for measuring rather than choosing: the ranking depends on your corpus, so it has to be computed on your corpus.",
   "why": "The paragraph ends with a summary that states the argument explicitly, which can be seen as telling the reader what was just said."
  },
  {
   "line": 767,
   "habit": "triad",
   "severity": "low",
   "quote": "These can tell you a configuration is broken. They cannot tell you which of two reasonable configurations is better — “good chunking” is only defined relative to the questions people actually ask. Anything claiming a universal chunk-quality score without queries is overselling.",
   "why": "The sentence lists three items, which is a common habit."
  },
  {
   "line": 789,
   "habit": "restatement",
   "severity": "low",
   "quote": "Three of the four answers were not what we expected.",
   "why": "This sentence reiterates the same point as the previous sentence, which is not adding new information."
  },
  {
   "line": 870,
   "habit": "restatement",
   "severity": "low",
   "quote": "Two of them, duplication from overlap and whether cuts land cleanly, carry real information about quality as well. The rest are best read as faults to fix, not as a ranking.",
   "why": "The same point is made again in the adjacent sentence, with no new information added."
  },
  {
   "line": 880,
   "habit": "closer",
   "severity": "medium",
   "quote": "The objection is sharper than it looks, because the ranking really does depend on the questions.",
   "why": "This sentence summarily concludes the paragraph and restates the main point without adding new information."
  },
  {
   "line": 924,
   "habit": "closer",
   "severity": "medium",
   "quote": "“self-contained” is the one that moves.",
   "why": "ends a paragraph with a key point, suggesting the sentence is meant to land a conclusion."
  },
  {
   "line": 980,
   "habit": "restatement",
   "severity": "low",
   "quote": "Some faults are faults for every question. Some faults are faults for every question.",
   "why": "same point is made twice in adjacent sentences."
  },
  {
   "line": 999,
   "habit": "cliche-emphasis",
   "severity": "medium",
   "quote": "You can manufacture questions, at increasing fidelity.",
   "why": "uses 'at increasing fidelity' to announce importance."
  },
  {
   "line": 1015,
   "habit": "dramatic-beat",
   "severity": "low",
   "quote": "Ask for a quote and a mistake announces itself.",
   "why": "a very short sentence or one-line paragraph for a reveal."
  },
  {
   "line": 1039,
   "habit": "generic-detail",
   "severity": "high",
   "quote": "A 25% yield.",
   "why": "a vague phrase where a real detail belongs."
  },
  {
   "line": 1082,
   "habit": "fragment",
   "severity": "medium",
   "quote": "So we measured both. Change the chunking with the search engine held still; change the search engine with the chunking held still; see how far each one moves the score.",
   "why": "A verbless phrase standing in for a sentence, used in a row."
  },
  {
   "line": 1163,
   "habit": "fragment",
   "severity": "medium",
   "quote": "All four of the bad cases were the same failure. The keyword search engine, which matches on shared words, simply lost the answer — scoring 1.3 where a meaning-based engine scored 19.7 on the identical chunks. It didn’t degrade. It collapsed.",
   "why": "A verbless phrase standing in for a sentence, used in a row."
  },
  {
   "line": 1287,
   "habit": "triad",
   "severity": "low",
   "quote": "llama3.1 8B <td class=\"hit\">15</td><td>8</td>",
   "why": "Three numerical values in a row, likely for emphasis or finish."
  },
  {
   "line": 1312,
   "habit": "closer",
   "severity": "medium",
   "quote": "If you only read one entry, read the last one.",
   "why": "Summary statement ending the paragraph."
  }
 ]
}
```

Lines 255 to 383: ### Summary
The most recurring habits in this section are `generic-detail`. The sentences about the consequences of bad cuts could benefit from more specific examples or details.

Lines 384 to 616: ### Summary
The most recurring habit in this section is `closer`, where paragraphs end with a sentence that summarizes the main point. The `triad` habit is also present, where three items are listed to describe a single concept.

Lines 617 to 735: ### Summary
The draft from lines 617 to 735 features recurring habits of antithesis and triad. Antithesis is particularly noticeable in line 685, where the sentence sets up an idea only to contradict it. Triads are observed in line 711, where three separate clauses are used to describe the relationship between overlap and the score.

Lines 736 to 800: ### Summary
The most recurring habits in this section are `cliche-emphasis` and `closer`. The `triad` and `restatement` habits also appear but are less prominent. These habits cluster in the final paragraph and the summary section, where they can be more noticeable to the reader.

Lines 801 to 919: ### Summary
The most recurring habits in this section are `restatement` and `closer`. The `restatement` habit is seen in line 870, where the same point is made twice with no additional information. The `closer` habit is observed in line 880, where a sentence concludes the paragraph by restating the main point without adding new content.

Lines 920 to 1071: ### Summary
The draft exhibits a mix of habits, with `closer` and `generic-detail` being the most prevalent. The `closer` habit is noticeable in paragraph endings, while `generic-detail` is used to summarize results without providing specific numbers or details. These habits could benefit from more precise and specific content to enhance the clarity and impact of the text.

Lines 1072 to 1208: ### Summary
The draft exhibits the `fragment` habit most prominently, with two instances where verbless phrases are used in a row. These are found in lines 1082 and 1163.

Lines 1209 to 1556: ### Summary
The most recurring habits are `triad`, where three items are grouped together, and `closer`, where a paragraph ends with a summarizing statement. These habits are found in sections discussing model performance and the conclusion of the glossary section.
