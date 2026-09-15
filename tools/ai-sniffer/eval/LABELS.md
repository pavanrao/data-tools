# ai-sniffer eval labels

Generated from `labels.json` by `render_labels.py`; edit `labels.jsonl`, not this file.

**How severity is scored.** `high` and `medium` count toward recall, so a reviewer that misses one loses a point. `low` is neutral: a defensible use either way, so flagging it neither earns nor costs anything.

**Reviewing.** Disagree with a label by its id: wrong habit, wrong severity, not a habit at all, or a habit that isn't labelled.

| Draft | Role | High | Medium | Low |
| --- | --- | --- | --- | --- |
| `heldout-double-entry.html` | held-out | 22 | 16 | 9 |
| `heldout-where-the-cut-falls.html` | held-out | 11 | 14 | 4 |
| `dev-database-before.html` | development | 17 | 14 | 3 |
| `dev-protocol-before.md` | development | 17 | 9 | 6 |
| `clean-database-after.html` | clean | 1 | 12 | 8 |
| `clean-protocol-after.md` | clean | 0 | 0 | 2 |
| **total** | | 68 | 65 | 32 |

## `heldout-double-entry.html`

**held-out** · data-tools b265882. Never quoted in the prompt. Labelled before any model saw it. This is the recall that counts.

| Id | Line | Severity | Habit | Quote |
| --- | --- | --- | --- | --- |
| `heldout-double-entry-01` | 316 | high | triad | Nothing crashes, nothing warns you, and the answers keep coming. |
| `heldout-double-entry-02` | 344 | high | cliche-emphasis | That difference is the entire idea. |
| `heldout-double-entry-03` | 344 | high | antithesis | One number can only ever be a system grading its own homework. Two numbers, counted independently, can disagree. |
| `heldout-double-entry-04` | 354 | medium | dramatic-beat | Your files go in. Some of them don't arrive. |
| `heldout-double-entry-05` | 357 | low | dramatic-beat | Start from nothing. |
| `heldout-double-entry-06` | 382 | low | dramatic-beat | This is a good design. |
| `heldout-double-entry-07` | 384 | medium | hedge | product works roughly this way. |
| `heldout-double-entry-08` | 388 | high | dramatic-beat | The trouble is entirely in step one, and it is invisible from step four. |
| `heldout-double-entry-09` | 397 | high | antithesis | Not an error - an empty string. |
| `heldout-double-entry-10` | 402 | medium | hedge | A great deal of extraction code opens a |
| `heldout-double-entry-11` | 410 | medium | generic-detail | The most popular way to read one walks the body and stops. |
| `heldout-double-entry-12` | 411 | low | hedge | frequently the sentence that changes the meaning |
| `heldout-double-entry-13` | 422 | low | emphasis-word | is simply not in the corpus |
| `heldout-double-entry-14` | 427 | high | antithesis | This is not hallucination. |
| `heldout-double-entry-15` | 430 | high | closer | It is the missing passages that lie. |
| `heldout-double-entry-16` | 437 | low | fragment | Because none of these raise an exception. |
| `heldout-double-entry-17` | 446 | high | antithesis | What's needed is not a confession. It's a checksum. |
| `heldout-double-entry-18` | 456 | low | triad | Count it twice, on purpose, by different routes |
| `heldout-double-entry-19` | 460 | medium | triad | records every transaction twice, in two places, by two routes that must agree |
| `heldout-double-entry-20` | 461 | high | antithesis | Not because the second entry is more accurate - because a single entry has nothing to be checked against. |
| `heldout-double-entry-21` | 462 | high | closer | An error in one column is invisible; the same error in one of two columns is a mismatch. |
| `heldout-double-entry-22` | 515 | low | cliche-emphasis | and more importantly it is |
| `heldout-double-entry-23` | 522 | high | cliche-emphasis | The independence is the whole mechanism. |
| `heldout-double-entry-24` | 550 | high | fragment | A detail that matters more than it looks. |
| `heldout-double-entry-25` | 564 | medium | emphasis-word | because they genuinely are a sequence |
| `heldout-double-entry-26` | 586 | high | antithesis | This is not for speed. It is so that a parse killed |
| `heldout-double-entry-27` | 630 | medium | dramatic-beat | Here is the trap that ordinary retrieval falls into. |
| `heldout-double-entry-28` | 632 | medium | emphasis-word | there is literally nothing to rank |
| `heldout-double-entry-29` | 632 | high | antithesis | The system doesn't ignore it; it never knew it existed. |
| `heldout-double-entry-30` | 636 | high | triad | You still have its name. You have the tab that came back empty, and that tab has a name. You have the error. |
| `heldout-double-entry-31` | 638 | medium | emphasis-word | startlingly often the exact vocabulary |
| `heldout-double-entry-32` | 685 | medium | closer | Pages and nodes are not interchangeable quantities. |
| `heldout-double-entry-33` | 706 | high | reader-instruction | Note that it says ok on all |
| `heldout-double-entry-34` | 708 | high | closer | That is the whole problem, rendered as a column. |
| `heldout-double-entry-35` | 729 | high | fragment | Same corpus, same index, two questions. |
| `heldout-double-entry-36` | 756 | medium | dramatic-beat | coverage 1.00. That is correct. |
| `heldout-double-entry-37` | 762 | low | emphasis-word | which is exactly the hole an index would inherit |
| `heldout-double-entry-38` | 762 | high | fragment | Two different questions, both worth asking. |
| `heldout-double-entry-39` | 776 | medium | closer | Stated plainly, because a tool about honest reporting that oversold itself would be a poor joke. |
| `heldout-double-entry-40` | 804 | medium | antithesis | This catches wholesale loss, not quality degradation. |
| `heldout-double-entry-41` | 822 | high | antithesis | an honest gap rather than a silent one - but a gap all the same |
| `heldout-double-entry-42` | 839 | low | closer | This is the most valuable next thing. |
| `heldout-double-entry-43` | 869 | medium | restatement | The point, restated |
| `heldout-double-entry-44` | 872 | medium | hedge | Almost nothing checks that promise |
| `heldout-double-entry-45` | 873 | medium | triad | no crash, no warning, plausible output |
| `heldout-double-entry-46` | 875 | high | closer | one number cannot be wrong, it can only be the number |
| `heldout-double-entry-47` | 885 | high | fragment | MIT-adjacent in spirit, deterministic in the core, model-free where it counts. |

## `heldout-where-the-cut-falls.html`

**held-out** · data-tools b265882. Never quoted in the prompt. Labelled before any model saw it. This is the recall that counts.

Only lines 268–301, 384–461, 617–677, 751–781, 1072–1177 are labelled and scored (sections 1, 4, 7, 10 and 13).

| Id | Line | Severity | Habit | Quote |
| --- | --- | --- | --- | --- |
| `heldout-where-the-cut-falls-01` | 274 | medium | hedge | Most systems default to something arbitrary |
| `heldout-where-the-cut-falls-02` | 275 | medium | closer | And that works fine, right up until a cut lands in the middle of the sentence that holds the answer. |
| `heldout-where-the-cut-falls-03` | 291 | high | cliche-emphasis | That third cut is the whole problem. |
| `heldout-where-the-cut-falls-04` | 293 | high | cliche-emphasis | which is worse than useless, because it looks like an answer |
| `heldout-where-the-cut-falls-05` | 387 | high | antithesis | Counting characters is free. Asking a language model to read the document and decide is not. |
| `heldout-where-the-cut-falls-06` | 406 | medium | hedge | That last row is the one most write-ups get wrong |
| `heldout-where-the-cut-falls-07` | 407 | high | dramatic-beat | as though it were another way to cut. It is not. |
| `heldout-where-the-cut-falls-08` | 453 | medium | fragment | Which means any honest score has to say which of the two it measured. |
| `heldout-where-the-cut-falls-09` | 620 | low | antithesis | treating as one problem and which is really two |
| `heldout-where-the-cut-falls-10` | 671 | medium | antithesis | treated as the fixture having drifted, not as an improvement |
| `heldout-where-the-cut-falls-11` | 752 | medium | triad | no questions, no marked answers and no model at all |
| `heldout-where-the-cut-falls-12` | 767 | high | fragment | The limit worth stating. |
| `heldout-where-the-cut-falls-13` | 767 | high | antithesis | These can tell you a configuration is broken. They cannot tell you which of two reasonable configurations is better |
| `heldout-where-the-cut-falls-14` | 770 | medium | closer | Anything claiming a universal chunk-quality score without queries is overselling. |
| `heldout-where-the-cut-falls-15` | 773 | high | dramatic-beat | but not for the reason we expected. Next section. |
| `heldout-where-the-cut-falls-16` | 1073 | high | fragment | Fair challenge. |
| `heldout-where-the-cut-falls-17` | 1075 | low | cliche-emphasis | this whole piece is advice about the wrong knob |
| `heldout-where-the-cut-falls-18` | 1077 | medium | dramatic-beat | So we measured both. |
| `heldout-where-the-cut-falls-19` | 1079 | medium | antithesis | Never both at once - that measures neither. |
| `heldout-where-the-cut-falls-20` | 1095 | high | antithesis | Read the middle column and the answer is "chunking, obviously." Read the last two together and it changes. |
| `heldout-where-the-cut-falls-21` | 1097 | medium | dramatic-beat | What differs is how often. |
| `heldout-where-the-cut-falls-22` | 1146 | high | antithesis | The two are not big and small. They are frequent and rare. |
| `heldout-where-the-cut-falls-23` | 1154 | low | fragment | Which is a more useful thing to know than "chunking matters more" |
| `heldout-where-the-cut-falls-24` | 1157 | medium | closer | when it goes wrong it doesn't go slightly wrong |
| `heldout-where-the-cut-falls-25` | 1160 | low | emphasis-word | simply lost the answer |
| `heldout-where-the-cut-falls-26` | 1161 | high | antithesis | It didn't degrade. It collapsed. |
| `heldout-where-the-cut-falls-27` | 1163 | medium | fragment | One tempting explanation that turned out to be wrong. |
| `heldout-where-the-cut-falls-28` | 1166 | medium | triad | It reads well, it fits the two worst cases, and it is not true |
| `heldout-where-the-cut-falls-29` | 1168 | medium | closer | Worth saying out loud, because that paragraph very nearly got written the other way. |

## `dev-database-before.html`

**development** · data-tools 372bb84. The catalogue's examples are quoted from here, so recall on this draft is optimistic.

| Id | Line | Severity | Habit | Quote |
| --- | --- | --- | --- | --- |
| `dev-database-before-01` | 276 | medium | hedge | Almost every SQL-over-MCP server decides whether a query is safe |
| `dev-database-before-02` | 279 | medium | closer | the database has been offering it for twenty years |
| `dev-database-before-03` | 289 | high | fragment | Three tools, a row cap, done in an afternoon. |
| `dev-database-before-04` | 289 | medium | closer | The interesting part turned out not to be the protocol at all. |
| `dev-database-before-05` | 294 | high | dramatic-beat | It was this question. |
| `dev-database-before-06` | 302 | medium | hedge | Most published examples do some version of this |
| `dev-database-before-07` | 309 | high | reader-instruction | Consider what it must already handle correctly. |
| `dev-database-before-08` | 332 | high | antithesis | You can fix each of these. You cannot fix the category. |
| `dev-database-before-09` | 333 | medium | antithesis | is owned by whoever maintains the SQL dialect, not by you |
| `dev-database-before-10` | 342 | high | fragment | Two mechanisms, both older than the problem. |
| `dev-database-before-11` | 347 | high | antithesis | Not a flag your code checks. The file is opened in a mode where writing is not a thing that can happen. |
| `dev-database-before-12` | 373 | high | dramatic-beat | That is the whole guard. |
| `dev-database-before-13` | 399 | high | fragment | Four for four, and not because I thought about any of them. |
| `dev-database-before-14` | 399 | high | closer | It is an allowlist in the engine, so it is wrong only in the safe direction. |
| `dev-database-before-15` | 408 | high | antithesis | The lesson survives the change of engine; the regex does not. |
| `dev-database-before-16` | 412 | medium | cliche-emphasis | It failed on my own code first, which is the point |
| `dev-database-before-17` | 416 | medium | dramatic-beat | table_info. It was refused. |
| `dev-database-before-18` | 421 | medium | dramatic-beat | This was the guard working. |
| `dev-database-before-19` | 430 | high | reader-instruction | Sit with that for a second. |
| `dev-database-before-20` | 432 | medium | triad | Deny-by-default failed loudly, in development, on the safe side. |
| `dev-database-before-21` | 433 | high | closer | That is the entire argument for it in one incident. |
| `dev-database-before-22` | 442 | low | emphasis-word | The protocol has a perfectly good error channel. |
| `dev-database-before-23` | 446 | high | dramatic-beat | It is the wrong channel. |
| `dev-database-before-24` | 448 | low | emphasis-word | The server worked exactly as designed. |
| `dev-database-before-25` | 448 | high | antithesis | What the model needs to know is not that it failed, but what to do differently. |
| `dev-database-before-26` | 461 | high | fragment | Two fields, two audiences. |
| `dev-database-before-27` | 485 | high | dramatic-beat | eats the entire context window. Fine. |
| `dev-database-before-28` | 503 | medium | cliche-emphasis | Honest answer, for the case you are probably imagining |
| `dev-database-before-29` | 504 | low | emphasis-word | A server there is pure overhead |
| `dev-database-before-30` | 509 | medium | triad | It changes when one of three things is true. |
| `dev-database-before-31` | 518 | high | reader-instruction | Note that none of those three is about the protocol. |
| `dev-database-before-32` | 519 | medium | antithesis | The protocol's contribution is narrower and still real |
| `dev-database-before-33` | 528 | medium | antithesis | Build a server, not a client. |
| `dev-database-before-34` | 530 | medium | dramatic-beat | They are the product. |

## `dev-protocol-before.md`

**development** · pavanrao.github.io cfa59de. The catalogue's examples are quoted from here, so recall on this draft is optimistic.

| Id | Line | Severity | Habit | Quote |
| --- | --- | --- | --- | --- |
| `dev-protocol-before-01` | 17 | medium | hedge | Plenty of older clients and servers are still around |
| `dev-protocol-before-02` | 23 | high | generic-detail | which turned out to be harder to ask than I expected |
| `dev-protocol-before-04` | 29 | low | emphasis-word | does exactly the negotiation you're trying to observe |
| `dev-protocol-before-03` | 36 | high | antithesis | For a client that just needs a session, that's the right design. For working out what a server is, it throws the answer away. |
| `dev-protocol-before-05` | 40 | medium | generic-detail | Separate connections matter more than they look |
| `dev-protocol-before-06` | 45 | high | fragment | Each path ends one of three ways. It worked. |
| `dev-protocol-before-07` | 46 | high | cliche-emphasis | The difference between those last two is the whole point |
| `dev-protocol-before-08` | 53 | low | emphasis-word | companies whose tools people actually run |
| `dev-protocol-before-09` | 53 | medium | fragment | All at their latest versions, all started locally with npx or uvx, no credentials |
| `dev-protocol-before-10` | 56 | low | emphasis-word | checks that the listings actually work |
| `dev-protocol-before-11` | 91 | high | fragment | Both npm packages, both reasonably recent, opposite answers. |
| `dev-protocol-before-12` | 110 | high | closer | Which protocol a server speaks, on this sample, is a dependency decision nobody on the project necessarily made on purpose. |
| `dev-protocol-before-13` | 114 | high | restatement | Every server that listed a capability could back it up. Nothing advertised tools and then failed to list them. |
| `dev-protocol-before-14` | 117 | high | dramatic-beat | The reference servers stand out. |
| `dev-protocol-before-15` | 123 | high | dramatic-beat | This part I got wrong first. |
| `dev-protocol-before-16` | 126 | medium | generic-detail | The evidence looked solid. |
| `dev-protocol-before-17` | 133 | high | antithesis | wasn't released as a new major of the package everyone already had. It went out on 27 July as separate packages |
| `dev-protocol-before-18` | 137 | medium | dramatic-beat | That's a trap for anyone maintaining a TypeScript server. |
| `dev-protocol-before-19` | 137 | low | emphasis-word | Dependabot will happily keep bumping |
| `dev-protocol-before-20` | 141 | high | closer | It just requires someone to take the major bump. |
| `dev-protocol-before-21` | 174 | medium | closer | which looks a lot more reasonable with this table in front of you. |
| `dev-protocol-before-22` | 178 | high | dramatic-beat | It had bugs I'd never have found against test servers. |
| `dev-protocol-before-23` | 181 | high | dramatic-beat | It hadn't answered anything. |
| `dev-protocol-before-24` | 190 | medium | emphasis-word | which is precisely where that one explanatory line went |
| `dev-protocol-before-25` | 200 | low | emphasis-word | A server that genuinely never answers times out twice. |
| `dev-protocol-before-26` | 202 | medium | fragment | And one mistake that wasn't in the probe at all. |
| `dev-protocol-before-27` | 205 | low | emphasis-word | which matches the code exactly |
| `dev-protocol-before-28` | 219 | high | antithesis | since that's a fact about the server rather than a lie it told |
| `dev-protocol-before-29` | 223 | medium | hedge | plenty of hosted servers only offer HTTP |
| `dev-protocol-before-30` | 225 | high | antithesis | That's a decision about sending requests to other people's endpoints, not a technical gap |
| `dev-protocol-before-31` | 232 | high | closer | So the SDK settled which protocols a server speaks, and what each server claims within them came down to how it was written. |
| `dev-protocol-before-32` | 236 | high | cliche-emphasis | These numbers have a short shelf life. |

## `clean-database-after.html`

**clean** · data-tools 138a26c. Habits the rewrite left behind or introduced. Flags on anything *not* labelled here are false alarms.

| Id | Line | Severity | Habit | Quote |
| --- | --- | --- | --- | --- |
| `clean-database-after-01` | 288 | medium | dramatic-beat | I assumed the time would go on the protocol. It didn't. |
| `clean-database-after-02` | 289 | medium | generic-detail | one question that turned out to be harder than it looks |
| `clean-database-after-03` | 327 | low | cliche-emphasis | and that's sort of the problem |
| `clean-database-after-04` | 343 | medium | antithesis | Not a flag your code consults later |
| `clean-database-after-05` | 396 | low | fragment | All four, and I didn't reason about any of them. |
| `clean-database-after-06` | 397 | medium | closer | it can be wrong, but only by refusing something it should have allowed |
| `clean-database-after-07` | 406 | high | fragment | Same idea, different engine. |
| `clean-database-after-08` | 440 | medium | closer | which is the cheapest place for it to break |
| `clean-database-after-09` | 449 | low | emphasis-word | the protocol has a perfectly good error channel |
| `clean-database-after-10` | 455 | medium | dramatic-beat | to try again. But nothing broke. |
| `clean-database-after-11` | 456 | low | emphasis-word | The server did exactly what it was built to do. |
| `clean-database-after-12` | 456 | medium | antithesis | The model doesn't need to know that the call failed; it needs to know what to do differently. |
| `clean-database-after-13` | 494 | medium | antithesis | The cap isn't the interesting bit. What matters is |
| `clean-database-after-14` | 505 | low | antithesis | On SQLite that's a rounding error and the field is nearly pointless. On Snowflake it's the whole bill |
| `clean-database-after-15` | 507 | medium | generic-detail | by more than people expect |
| `clean-database-after-16` | 529 | medium | antithesis | None of those is really about MCP. They're about who's asking and how often. |
| `clean-database-after-17` | 531 | medium | emphasis-word | which is genuinely the problem it exists to solve |
| `clean-database-after-18` | 538 | low | fragment | Two things I'd tell someone doing this next. |
| `clean-database-after-19` | 540 | low | antithesis | a database qualifies, a folder of text files doesn't |
| `clean-database-after-20` | 549 | low | fragment | Nothing errors, nothing warns |
| `clean-database-after-21` | 559 | medium | closer | There's a lab in the backlog to measure it. I haven't run it. |

## `clean-protocol-after.md`

**clean** · pavanrao.github.io 2e91d3d. Habits the rewrite left behind or introduced. Flags on anything *not* labelled here are false alarms.

| Id | Line | Severity | Habit | Quote |
| --- | --- | --- | --- | --- |
| `clean-protocol-after-01` | 27 | low | emphasis-word | does exactly the negotiation you're trying to observe |
| `clean-protocol-after-02` | 48 | low | emphasis-word | companies whose tools people actually run |
