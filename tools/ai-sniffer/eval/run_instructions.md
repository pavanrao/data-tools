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

---

## Do not name a habit in the instructions

Added 2026-09-17, after a review of the blog post that covers this work.

One verification run was given an extra line: *"Pay particular attention to `closer` and
to repeated sentence skeletons, since those are the habits this draft is most at risk
of."* On the same draft, three unprimed runs returned 17, 22 and 13 findings with 8, 6
and 4 closers. The primed run returned 27 findings with 17 closers — roughly four times
the closer count of the unprimed run that followed it, on text that had by then been
edited to have fewer.

It also over-fired in a readable way, calling a subordinate clause that explains a
design decision ("since a closer is not something a pattern can adjudicate") a closer,
and a method statement ("whatever a detector says about the untouched posts is
subtracted first") a closer.

So the count from a primed run cannot be compared with any other run, which is the same
independence failure as handing the reviewer the linter's report and calling the result
unaided. Instructions to a review run say what to read and where to write; the
catalogue of habits lives in the prompt and nowhere else.
