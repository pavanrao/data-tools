# 008 — Data-engineering coverage

The second coverage map. [`005`](005_concept-coverage.md) asks *which AI concepts
do I have a measured tool for*; this one asks a different question about the same
backlog:

> **Which enterprise data-engineering problems do I have a tool for, and which are
> bare?**

## Why two maps

Every idea in sections **H–J** of [`IDEAS.md`](../IDEAS.md) carries two lines, and
they point at different things:

```
### 93. vendor-spec-reader — file-spec PDF → parser config + DQ rules
- Learn:    RAG over long structured documents; schema-constrained JSON output;
            citation discipline.              <- an AI concept          -> 005
- Maps to:  legacy/COTS flat-file ingestion onboarding.
                                              <- a data problem         -> here
```

So `#93` is *simultaneously* a §2 RAG exercise and a legacy-onboarding tool. In
sections A–G the two axes collapse — for a concept lab the AI concept **is** the
point — which is why `005` alone was enough until now. Sections H–J separate them,
and one document cannot answer both questions without answering neither well.

**The bar for inclusion** is stated in each entry's *agentic core* line: what makes
a language model load-bearing here rather than decorative. A problem solvable by a
schema diff and a `GROUP BY` does not belong in H–J, and several ideas in sections
A–E are marked ⚠️ **Deterministic** precisely because their core job is not an AI
problem at all.

## How to read a row

**Covered** means an idea exists and is specific enough to build from — not that it
is built. Only ✅ means built. A problem with no idea against it is the useful
signal: it is either genuinely not an AI problem, or a gap.

---

## §A · Source onboarding & discovery

The hardest, least glamorous part of any platform: making sense of what arrives.

| Problem | Covered by |
| --- | --- |
| Onboarding a flat file with a prose spec | #93 `vendor-spec-reader` (200-page PDF → parser config + DQ rules, traced to the page) |
| Mainframe sources — copybooks, EBCDIC, packed decimal | #94 `copybook-decoder` · #144 `mainframe-assimilator` (end to end) |
| No spec exists at all | #96 `fixed-width-inferrer` (recover the layout from the data) |
| An undocumented legacy database | #118 `db-archaeologist` (infer keys and relationships, confidence-ranked) |
| Onboarding as a repeatable service, not a project | #152 `onboarding-concierge` · #150 `data-product-foundry` |
| Absorbing an acquired company's estate | #146 `ma-data-assimilator` |

## §B · Semantics & standardisation

What the columns *mean*, which no schema records.

| Problem | Covered by |
| --- | --- |
| Cryptic legacy column names | #95 `column-semantics-tagger` |
| Sentinel values — is `9999-12-31` a date or a null? | #97 `null-semantics-detective` |
| Mixed units, currencies and scales in one column | #98 `units-detective` |
| Reference data and code-set alignment | #99 `code-set-mapper` |
| Naming conventions across an estate | #107 `naming-harmonizer` |
| **Time zones, calendars and effective dating** | *bare* |
| **Encoding, collation and locale drift** | *partly* — #98 `units-detective` touches scale, not encoding |

## §C · Mapping, matching & integration

| Problem | Covered by |
| --- | --- |
| Source→target column mappings | #100 `mapping-suggester` |
| How two systems' tables join | #101 `join-key-suggester` |
| MDM match/merge in the gray zone | #123 `match-merge-adjudicator` (adjudicated, with evidence) |
| **Survivorship rules and golden-record policy** | *bare* — #123 adjudicates a pair, not a policy |

## §D · Transform understanding & modernisation

| Problem | Covered by |
| --- | --- |
| What does this legacy SQL actually do? | #102 `transform-explainer` (→ business-rule documentation) |
| What changed, in business terms? | #103 `sql-intent-differ` |
| Stored procedures → a modern engine | #119 `proc-modernizer` (tested SparkSQL) |
| Mainframe job flows → an orchestrator | #120 `jcl-flow-reconstructor` |
| SQL dialect migration | #116 `dialect-translator` (verified, not just translated) |
| Copy-paste transform sprawl | #135 `dedup-refactorer` |
| A whole ETL estate | #143 `etl-migration-factory` · #145 `platform-migration-copilot` |

## §E · Semantic layer, metrics & BI

| Problem | Covered by |
| --- | --- |
| Where do metric definitions actually live? | #104 `metric-definition-extractor` (mine the reports) |
| One KPI, four definitions | #124 `metric-consistency-auditor` |
| The model hiding in the report estate | #121 `report-reverse-engineer` · #122 `model-designer` |
| 4,000 reports that should be 400 | #147 `bi-rationalizer` |
| Building and *maintaining* a semantic layer | #149 `semantic-layer-factory` |
| "Why did this number move?" | #137 `number-change-detective` · #142 `lineage-narrator` |
| Trustworthy chat-with-data | #164 `analysis-copilot` (answers with proof) |

## §F · Catalog, glossary & documentation

| Problem | Covered by |
| --- | --- |
| Glossary terms → physical columns | #105 `glossary-linker` |
| Documentation that lies about reality | #108 `doc-drift-detector` |
| Catalog enrichment / auto-classification | #95 `column-semantics-tagger` |
| Documentation that cannot go stale | #167 `as-built-documentarian` |
| One queryable brain over catalog + lineage + stewardship | #148 `estate-knowledge-graph` |

## §G · Contracts, quality & stewardship

| Problem | Covered by |
| --- | --- |
| Contracts extracted from legacy artifacts | #106 `contract-from-docs` |
| Contracts that stay alive | #151 `contract-lifecycle-system` · #19 `data-contract-linter` |
| DQ rules that learn the business rhythm | #155 `quality-sentinel-network` · #35 `dq-rule-suggester` |
| The quarantine pile nobody triages | #130 `quarantine-adjudicator` |
| Telling a source system it broke, with evidence | #114 `failure-notifier` |
| The steward's queue, triaged | #163 `steward-command-center` |
| The ad-hoc request firehose | #165 `data-request-desk` |

## §H · Testing & change safety

| Problem | Covered by |
| --- | --- |
| Fixtures for SQL transforms | #109 `test-synthesizer` · #42 `sql-test-harness` |
| Business-rule-aware edge cases | #110 `edge-case-smith` |
| Reviewing generated orchestration code | #111 `dag-reviewer` |
| Blast radius of a change | #112 `change-risk-scorer` (as a PR comment) |
| Schema drift — the "what now?" after detection | #134 `drift-ripple-planner` · #158 `source-watchtower` (moved left of the failure) |
| Why did it get slow or wrong? | #131 `regression-bisector` |
| Why does dev ≠ test ≠ prod? | #132 `env-drift-explainer` |
| Retiring dead weight safely | #136 `deprecation-planner` |

## §I · Operations, incidents & reconciliation

| Problem | Covered by |
| --- | --- |
| Is it late, or is it just Tuesday? | #113 `freshness-inferrer` · #128 `sla-forecaster` |
| Root cause with an evidence chain | #126 `rca-investigator` · #154 `incident-war-room` |
| From incident window to an ordered backfill | #127 `backfill-planner` · #82 `backfill-drill` |
| Detect → diagnose → fix, governed | #153 `self-healing-pipelines` |
| Incidents → runbooks | #115 `runbook-writer` |
| When did the data go wrong? | #133 `snapshot-debugger` |
| Chasing a control-total mismatch | #125 `recon-investigator` · #28 `load-reconciler` |
| Audit evidence, assembled | #141 `audit-evidence-compiler` |

## §J · Cost & portfolio

| Problem | Covered by |
| --- | --- |
| Compute cost per feed or domain | #41 `finops-attributor` · #157 `autonomous-finops-governor` |
| Performance fixes as validated PRs | #129 `spark-tuner` · #79 `spark-clinic` |
| Storage hygiene across an estate | #136 `deprecation-planner` |
| The whole nightly batch, optimised | #156 `pipeline-portfolio-optimizer` |

## §K · Privacy, access & retention

| Problem | Covered by |
| --- | --- |
| Shareable samples with structure intact | #117 `sample-redactor` |
| Test environments without PII | #166 `synthetic-environment-fabricator` |
| Does the masking actually hold? | #139 `reident-tester` (attack your own control) |
| What can this role actually see? | #138 `access-explainer` · #162 `access-governance-suite` |
| Subject rights (DSAR) | #159 `dsar-orchestrator` |
| Privacy impact assessments | #140 `pia-drafter` |
| Retention and legal hold | #161 `retention-lifecycle-enforcer` |
| Regulation changes → policy changes | #160 `reg-change-compliance-system` |

---

## What is bare

Named honestly, because an empty row is the most useful thing a coverage map
produces:

- **Time zones, calendars and effective dating** (§B). Endemic in insurance and
  finance, and nothing here touches it.
- **Survivorship rules and golden-record policy** (§C). `#123` adjudicates one
  match; deciding *which* value wins across sources is a different problem.
- **Encoding, collation and locale drift** (§B). Partly implied, never targeted.
- **Streaming-specific operations.** Sections H–J are batch-shaped throughout;
  `#81 stream-lab` in section F is the only streaming coverage, and it is a concept
  lab rather than an enterprise tool.

## Relationship to 005

A tool can and usually does appear in both maps, against different cards.
`#93 vendor-spec-reader` is *§A Source onboarding* here and *§2 The RAG pipeline*
in `005`. That is not duplication — it is the two axes doing their separate jobs,
and it is why the maps are worth keeping apart.
