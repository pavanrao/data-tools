```json
{
 "findings": [
  {
   "line": 276,
   "habit": "emphasis-word",
   "severity": "low",
   "quote": "harder to ask than I expected",
   "why": "emphasis-word used to add stress"
  },
  {
   "line": 297,
   "habit": "hedge",
   "severity": "low",
   "quote": "Most published examples do a version of this",
   "why": "universal claim softened with hedge"
  },
  {
   "line": 281,
   "habit": "reader-instruction",
   "severity": "low",
   "quote": "Sit with that for a second",
   "why": "instructs reader to 'sit with that for a second'"
  },
  {
   "line": 286,
   "habit": "fragment",
   "severity": "low",
   "quote": "Two mechanisms, both older than the problem",
   "why": "verbless phrase used instead of sentence"
  },
  {
   "line": 294,
   "habit": "cliche-emphasis",
   "severity": "low",
   "quote": "the whole point",
   "why": "stock phrase used to announce importance"
  },
  {
   "line": 282,
   "habit": "antithesis",
   "severity": "high",
   "quote": "the exact words from the draft",
   "why": "antithesis used to set up and knock down idea"
  },
  {
   "line": 425,
   "habit": "antithesis",
   "severity": "high",
   "quote": "What's actually going on is that <code>PRAGMA</code> is one authorizer action covering everything from <code>table_info</code>, which reads metadata, to <code>journal_mode</code>, which changes the database.",
   "why": "This is an instance of antithesis because it sets up an idea and then knocks it down with a counterexample."
  },
  {
   "line": 427,
   "habit": "triad",
   "severity": "medium",
   "quote": "What's actually going on is that <code>PRAGMA</code> is one authorizer action covering everything from <code>table_info</code>, which reads metadata, to <code>journal_mode</code>, which changes the database.",
   "why": "This is an instance of triad because it presents three items as if they're equal, when in fact they have different functions."
  },
  {
   "line": 461,
   "habit": "dramatic-beat",
   "severity": "medium",
   "quote": "So a refusal comes back as an ordinary, successful result that happens to say no:",
   "why": "This is an instance of dramatic-beat because it's a short sentence used to create a pause and emphasize the contrast between a refusal and an error."
  },
  {
   "line": 503,
   "habit": "generic-detail",
   "severity": "low",
   "quote": "<code>elapsed_ms</code> is standing in for the field that'll matter on a real warehouse, where it would be bytes scanned and money.",
   "why": "This is an instance of generic-detail because it uses vague language instead of providing a specific detail."
  },
  {
   "line": 455,
   "habit": "emphasis-word",
   "severity": "low",
   "quote": "An error tells a model that something broke, and the sensible response to something breaking is to try again.",
   "why": "This is an instance of emphasis-word because it uses the word 'sensible' to add stress, but doesn't provide any additional information."
  },
  {
   "line": 415,
   "habit": "hedge",
   "severity": "low",
   "quote": "My own tool couldn't read its own schema, and the message SQLite gives you is three words long:",
   "why": "This is an instance of hedge because it uses the phrase 'couldn't read its own schema' to soften the claim and make it less specific."
  },
  {
   "line": 449,
   "habit": "cliche-emphasis",
   "severity": "low",
   "quote": "The obvious move is to raise an error — the protocol has a perfectly good error channel and it's right there.",
   "why": "This is an instance of cliche-emphasis because it uses the phrase 'obvious move' to announce importance, but doesn't provide any additional context or explanation."
  }
 ]
}
```

Lines 273 to 409: This is a draft review task for a technical article. I will follow the instructions to review the draft and provide the findings in a JSON format with a short summary.

**Step 1: Read the draft**

I have read the draft from lines 273 to 409.

**Step 2: Find word-level habits**

Using the `ai-sniffer check --json FILE` command, I can run a linter report. Since no linter report is included, I will search for word-level habits manually.

**Word-level habits**

I found the following word-level habits:

* `emphasis-word`: "harder to ask than I expected" (line 276) - This sentence uses the emphasis-word "harder".
* `hedge`: "Most published examples do a version of this" (line 297) - This sentence uses a universal claim softened with the hedge "Most".
* `reader-instruction`: "Sit with that for a second" (line 281) - This sentence instructs the reader to "sit with that for a second".

**Structural habits**

I found the following structural habits:

* `antithesis`: "the exact words from the draft" - This is a recurring pattern of setting up one idea only to knock it down for another.
* `fragment`: "Two mechanisms, both older than the problem" (line 286) - This sentence uses a verbless phrase standing in for a sentence.
* `cliche-emphasis`: "the whole point" (line 294) - This sentence uses a stock phrase that announces importance.

**JSON output**

Here is the JSON output:



**Summary**

The draft contains word-level habits such as emphasis-word, hedge, and reader-instruction, as well as structural habits such as antithesis and cliche-emphasis. These habits can be improved by revising the text to make it more specific and engaging for the reader.

Lines 410 to 510: I'll review the draft and identify the habits that recur. I'll provide a list of quotes with the habit name, line number, and a brief description of why it's an instance of the habit.

**Habits found:**

1. **Antithesis** (line 425)
Quote: "What's actually going on is that <code>PRAGMA</code> is one authorizer action covering everything from <code>table_info</code>, which reads metadata, to <code>journal_mode</code>, which changes the database."
Description: This is an instance of antithesis because it sets up an idea (that PRAGMA is a single action) and then knocks it down with a counterexample (that it covers multiple actions).

2. **Triad** (line 427)
Quote: "What's actually going on is that <code>PRAGMA</code> is one authorizer action covering everything from <code>table_info</code>, which reads metadata, to <code>journal_mode</code>, which changes the database."
Description: This is an instance of triad because it presents three items (PRAGMA, table_info, and journal_mode) as if they're equal, when in fact they have different functions.

3. **Dramatic-beat** (line 461)
Quote: "So a refusal comes back as an ordinary, successful result that happens to say no:"
Description: This is an instance of dramatic-beat because it's a short sentence used to create a pause and emphasize the contrast between a refusal and an error.

4. **Generic-detail** (line 503)
Quote: "<code>elapsed_ms</code> is standing in for the field that'll matter on a real warehouse, where it would be bytes scanned and money."
Description: This is an instance of generic-detail because it uses vague language (standing in for) instead of providing a specific detail.

5. **Emphasis-word** (line 455)
Quote: "An error tells a model that something broke, and the sensible response to something breaking is to try again."
Description: This is an instance of emphasis-word because it uses the word "sensible" to add stress, but doesn't provide any additional information.

6. **Hedge** (line 415)
Quote: "My own tool couldn't read its own schema, and the message SQLite gives you is three words long:"
Description: This is an instance of hedge because it uses the phrase "couldn't read its own schema" to soften the claim and make it less specific.

7. **Cliche-emphasis** (line 449)
Quote: "The obvious move is to raise an error — the protocol has a perfectly good error channel and it's right there."
Description: This is an instance of cliche-emphasis because it uses the phrase "obvious move" to announce importance, but doesn't provide any additional context or explanation.

**Severity:**

* High: Antithesis (line 425)
* Medium: Triad (line 427), Dramatic-beat (line 461)
* Low: Generic-detail (line 503), Emphasis-word (line 455), Hedge (line 415), Cliche-emphasis (line 449)

**Output:**
