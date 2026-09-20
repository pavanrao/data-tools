```json
{
  "findings": [
    {
      "line": 38,
      "habit": "antithesis",
      "severity": "low",
      "quote": "asking it for a handshake afterwards tells you about the lock and nothing about the server.",
      "why": "the clause sets up what the handshake tells you and knocks it down with \"nothing about\" the thing that actually matters, the same setup-and-knockdown shape as \"not X, but Y.\""
    },
    {
      "line": 164,
      "habit": "antithesis",
      "severity": "high",
      "quote": "meaning it had answered and refused both protocols, and the probe exited successfully. In fact it had died on startup before answering anything, because I'd left off a flag it needs",
      "why": "the first sentence states an apparent reading of the result, then \"In fact\" knocks it down for the real one, the two-sentence form of \"It wasn't X. It was Y.\""
    },
    {
      "line": 186,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "I also made a mistake outside the probe.",
      "why": "a short standalone sentence placed to announce a reveal before the explanation, the same move as the catalogued example \"This part I got wrong first.\""
    },
    {
      "line": 184,
      "habit": "closer",
      "severity": "medium",
      "quote": "A server that never answers at all times out twice.",
      "why": "a short sentence at the end of the paragraph that generalizes the just-described fix into a tidy rule, landing the point rather than continuing to report it."
    },
    {
      "line": 159,
      "habit": "hedge",
      "severity": "low",
      "quote": "nearly any",
      "why": "a quantity claim about which errors trigger the fallback, given without naming which ones, so it can't be checked against the SDK's actual behavior."
    },
    {
      "line": 47,
      "habit": "emphasis-word",
      "severity": "low",
      "quote": "actually",
      "why": "adds stress to \"people actually run\" without adding information about who runs them or how that differs from the alternative."
    }
  ]
}
```

Findings cluster in two places. The section on the MotherDuck run ("What running it on real servers taught me about the probe," lines 164-186) carries three of the six: an antithesis reveal, a short dramatic-beat sentence, and a closer, all within about twenty lines. The other antithesis instance sits earlier, in "You can't find out by connecting" (line 38), more subtle than the MotherDuck one. The two word-level habits kept from the linter's report — a hedge ("nearly any," line 159) and an emphasis-word ("actually," line 47) — are isolated, low-severity instances rather than a pattern; a third linter hit ("exactly," line 26) was dropped as a natural use, matching the same "exact" negotiation being described. No hedge-word instance of reader-instruction, restatement, cliche-emphasis, generic-detail, fragment, or triad stood out from the surrounding technical prose, which stays specific (dates, error codes, version numbers) even at its shortest sentences.
