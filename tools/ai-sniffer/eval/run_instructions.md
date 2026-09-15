# Instructions given to each model run

Every model run in `runs/` received exactly this message, with the placeholders filled
in. `{LINTER_LINE}` and `{LINTER_CLAUSE}` take the first form for the `+linter` setups
and the second otherwise. Inputs were neutral copies outside the repo (`draft-1.html`
to `draft-6.html`, mapped in `runs/manifest.json`), so a run saw neither the labels nor
a filename that named the draft's role.

---

You're doing one review for an evaluation. Read these files and no others:

- PROMPT: `{PROMPT}`
- DRAFT: `{DRAFT}`
{LINTER_LINE}
  - with the linter: `- LINTER: {LINTER}`
  - without: *(line omitted)*

Don't run commands, don't search the filesystem, and don't open any file not listed
above.

Review DRAFT exactly as PROMPT describes, using the line numbers you see when you read
DRAFT. {LINTER_CLAUSE}

- with the linter: The linter has already run, and LINTER is its report. Use it for the
  word-level habits as PROMPT says.
- without: No linter report is included. Find the word-level habits yourself.

Write your complete reply, meaning the fenced JSON block and the short summary that
PROMPT's Output section asks for, to `{OUTPUT}` with the Write tool. Then reply with
only the number of findings.
