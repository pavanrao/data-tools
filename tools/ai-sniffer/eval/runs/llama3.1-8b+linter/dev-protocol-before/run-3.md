This is a detailed guide for reviewing a draft, specifically looking for common habits or patterns that may be detrimental to the reader's experience. Here's a summary of the guidelines and the specific habits to look for:

**How to work:**

1. Read the entire draft, paying attention to each section.
2. Use a linter to identify word-level habits, but also manually identify structural habits.
3. Ignore code, commands, tables of data, and quoted text from other sources.
4. Headings are considered prose and can carry habits.

**The catalogue:**

The guide lists several common habits to look for, including:

1. **Antithesis**: Setting up an idea only to knock it down for another, e.g., "not X, but Y".
2. **Fragment**: Verbless phrases standing in for sentences, often in a row.
3. **Triad**: Three items or clauses because three sounds finished, not because there were three things.
4. **Dramatic beat**: A very short sentence or one-line paragraph placed to create a pause or a reveal, when the content doesn't need one.
5. **Closer**: A section or paragraph ending built to land a point, often using an aphorism or summary.
6. **Restatement**: The same point made twice in adjacent sentences, with the second adding nothing.
7. **Cliche-emphasis**: Stock phrases that announce importance instead of showing it, e.g., "the key insight" or "a short shelf life".
8. **Generic-detail**: Vague phrases where a real detail belongs, often a reaction with no content or a claim about evidence with no evidence.
9. **Reader-instruction**: Telling the reader how to think or react, e.g., "keep in mind" or "sit with that".
10. **Hedge**: Universal claims softened so they can't be checked, e.g., "most people" or "plenty of".
11. **Emphasis-word**: Intensifiers that add stress but no information, e.g., "exactly", "precisely", "genuinely", or "actually".

**Rules:**

1. Quote the draft's words exactly as a reader sees them, without markup.
2. Provide the line number where the quote starts.
3. One finding per instance, even if a sentence carries multiple habits.
4. A single natural use isn't a finding.
5. Severity levels:
	* `high`: a reader would notice this sentence on its own.
	* `medium`: a habit, but one that stands out only alongside others.
	* `low`: defensible either way.
6. Never write replacement text, suggested wording, or an example of a better version.
7. For `generic-detail`, say that the passage needs a real specific from the author, without proposing one.

**Output:**

A fenced JSON block with findings, followed by a short plain summary of two to four sentences, including which habits recur most and where they cluster.

The guide also includes a sample draft and a linter report, which can be used to identify word-level habits. The reviewer's task is to identify these habits and quote them exactly as they appear in the draft, along with the line number where the quote starts.