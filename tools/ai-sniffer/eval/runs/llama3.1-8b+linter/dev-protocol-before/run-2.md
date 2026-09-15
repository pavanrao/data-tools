This is a detailed guide on how to review a draft for common writing habits that can make the text more skimmable. Here are the key points:

**Purpose:** The goal is to identify and quote instances of common writing habits in a draft, so the author can fix them.

**How to work:**

1. Read the entire draft, paying attention to every section equally.
2. Use a linter to identify word-level habits (such as hedging or using emphasis words). If the linter report is included, use it to find these habits.
3. Look for structural habits (such as antithesis or triads) that are not caught by the linter.
4. Ignore code, commands, tables of data, and quoted text from other sources.

**Habits to look for:**

1. **Antithesis**: Setting up an idea only to knock it down for another.
2. **Fragment**: Verbless phrases standing in for sentences.
3. **Triad**: Three items, clauses, or adjectives because three sounds finished, not because there were three things.
4. **Dramatic-beat**: A short sentence or one-line paragraph placed to create a pause or reveal, when the content doesn't need one.
5. **Closer**: A section or paragraph ending built to land a point, such as an aphorism or summary.
6. **Restatement**: Making the same point twice in adjacent sentences.
7. **Cliche-emphasis**: Stock phrases that announce importance instead of showing it.
8. **Generic-detail**: Vague phrases where a real detail belongs.
9. **Reader-instruction**: Telling the reader how to think or react.
10. **Hedge**: Universal claims softened so they can't be checked.
11. **Emphasis-word**: Intensifiers that add stress but no information.

**Rules for reporting:**

1. Quote the draft's words exactly as a reader sees them, without markup.
2. Give the line number where the quote starts.
3. Report one finding per instance.
4. A single natural use isn't a finding.
5. Severity: high, medium, or low (high if a reader would notice it on its own).
6. Never write replacement text, suggested wording, or an example of a better version.
7. For generic-detail, say that the passage needs a real specific from the author.

**Output:**

1. A fenced JSON block with findings.
2. A short plain summary of two to four sentences, including which habits recur most and where they cluster.

The guide provides examples of each habit and how to report them, as well as rules for reporting and output.