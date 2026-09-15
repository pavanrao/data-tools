I'll review the draft and find instances of the habits listed in the catalogue. I'll use the exact wording from the draft and provide the line numbers where each habit starts.

**Findings**

Here are the findings:

```json
{
  "findings": [
    {
      "line": 9,
      "habit": "fragment",
      "severity": "low",
      "quote": "an MCP client opened every connection with an `initialize` handshake",
      "why": "verbless phrase"
    },
    {
      "line": 11,
      "habit": "fragment",
      "severity": "low",
      "quote": "an MCP client asks `server/discover` what the server supports",
      "why": "verbless phrase"
    },
    {
      "line": 13,
      "habit": "dramatic-beat",
      "severity": "high",
      "quote": "It doesn't know `server/discover` exists, and says so correctly",
      "why": "short sentence for dramatic effect"
    },
    {
      "line": 18,
      "habit": "restatement",
      "severity": "low",
      "quote": "Every server on a version-one SDK spoke only the old handshake",
      "why": "repeating a point already made"
    },
    {
      "line": 29,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "the obvious move is to connect with the SDK and look at what you got",
      "why": "using a stock phrase to emphasize a point"
    },
    {
      "line": 35,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "it's also why the probe can't use it",
      "why": "vague phrase instead of a specific detail"
    },
    {
      "line": 43,
      "habit": "restatement",
      "severity": "low",
      "quote": "Those last two have to stay apart",
      "why": "repeating a point already made"
    },
    {
      "line": 53,
      "habit": "fragment",
      "severity": "low",
      "quote": "Microsoft's Playwright server first",
      "why": "verbless phrase"
    },
    {
      "line": 55,
      "habit": "cliche-emphasis",
      "severity": "medium",
      "quote": "The servers that don't speak July turn it down in two different ways",
      "why": "using a stock phrase to emphasize a point"
    },
    {
      "line": 61,
      "habit": "fragment",
      "severity": "low",
      "quote": "The Python ones don't",
      "why": "verbless phrase"
    },
    {
      "line": 65,
      "habit": "restatement",
      "severity": "low",
      "quote": "No server advertised a capability it couldn't list",
      "why": "repeating a point already made"
    },
    {
      "line": 73,
      "habit": "fragment",
      "severity": "low",
      "quote": "Upstash's Context7, run the same way",
      "why": "verbless phrase"
    },
    {
      "line": 75,
      "habit": "fragment",
      "severity": "low",
      "quote": "server   Context7",
      "why": "verbless phrase"
    },
    {
      "line": 77,
      "habit": "fragment",
      "severity": "low",
      "quote": "era      both",
      "why": "verbless phrase"
    },
    {
      "line": 81,
      "habit": "fragment",
      "severity": "low",
      "quote": "tools 2, resources 0, prompts 0",
      "why": "verbless phrase"
    },
    {
      "line": 83,
      "habit": "fragment",
      "severity": "low",
      "quote": "capabilities-by-era  identical in both eras",
      "why": "verbless phrase"
    },
    {
      "line": 85,
      "habit": "fragment",
      "severity": "low",
      "quote": "That version of Context7 was published the day I probed it",
      "why": "verbless phrase"
    },
    {
      "line": 87,
      "habit": "fragment",
      "severity": "low",
      "quote": "Here are all twelve",
      "why": "verbless phrase"
    },
    {
      "line": 89,
      "habit": "fragment",
      "severity": "low",
      "quote": "| Server | Publisher | SDK underneath | Speaks July? |",
      "why": "verbless phrase"
    },
    {
      "line": 91,
      "habit": "fragment",
      "severity": "low",
      "quote": "| `server-everything` | MCP project | TypeScript v1 | No |",
      "why": "verbless phrase"
    },
    {
      "line": 93,
      "habit": "fragment",
      "severity": "low",
      "quote": "| `mcp-server-fetch` | MCP project | Python v1 | No |",
      "why": "verbless phrase"
    },
    {
      "line": 95,
      "habit": "fragment",
      "severity": "low",
      "quote": "| Playwright | Microsoft | TypeScript v1, bundled | No |",
      "why": "verbless phrase"
    },
    {
      "line": 97,
      "habit": "fragment",
      "severity": "low",
      "quote": "| Context7 | Upstash | TypeScript v2 | Yes |",
      "why": "verbless phrase"
    },
    {
      "line": 99,
      "habit": "fragment",
      "severity": "low",
      "quote": "| MotherDuck | MotherDuck | Python v2 | Yes |",
      "why": "verbless phrase"
    },
    {
      "line": 101,
      "habit": "fragment",
      "severity": "low",
      "quote": "| AWS Documentation | AWS Labs | Python v2 | Yes |",
      "why": "verbless phrase"
    },
    {
      "line": 103,
      "habit": "fragment",
      "severity": "low",
      "quote": "The SDK column predicts the last one on every row",
      "why": "verbless phrase"
    },
    {
      "line": 105,
      "habit": "fragment",
      "severity": "low",
      "quote": "Every server on a version-one SDK spoke only the old handshake",
      "why": "verbless phrase"
    },
    {
      "line": 107,
      "habit": "fragment",
      "severity": "low",
      "quote": "I didn't find one that had implemented discovery by hand",
      "why": "verbless phrase"
    },
    {
      "line": 109,
      "habit": "fragment",
      "severity": "low",
      "quote": "No server advertised a capability it couldn't list",
      "why": "verbless phrase"
    },
    {
      "line": 111,
      "habit": "fragment",
      "severity": "low",
      "quote": "## The upgrade that bumping won't get you",
      "why": "verbless phrase"
    },
    {
      "line": 113,
      "habit": "fragment",
      "severity": "low",
      "quote": "I'd checked the TypeScript side and written down that its SDK hadn't shipped the July revision",
      "why": "verbless phrase"
    },
    {
      "line": 115,
      "habit": "fragment",
      "severity": "low",
      "quote": "because the newest `@modelcontextprotocol/sdk` on npm is 1.30.0 and there's no mention of `2026-07-28` anywhere in its build",
      "why": "verbless phrase"
    },
    {
      "line": 117,
      "habit": "fragment",
      "severity": "low",
      "quote": "Then Context7, an npm package, answered `server/discover`, so I went and read its dependencies",
      "why": "verbless phrase"
    },
    {
      "line": 119,
      "habit": "fragment",
      "severity": "low",
      "quote": "It depends on `@modelcontextprotocol/server` and `@modelcontextprotocol/node`, both at 2.0.0, and doesn't use `@modelcontextprotocol/sdk` at all",
      "why": "verbless phrase"
    },
    {
      "line": 121,
      "habit": "fragment",
      "severity": "low",
      "quote": "TypeScript v2 went out on 27 July under those new package names",
      "why": "verbless phrase"
    },
    {
      "line": 123,
      "habit": "fragment",
      "severity": "low",
      "quote": "If you maintain a TypeScript server, Dependabot will keep bumping `@modelcontextprotocol/sdk` for you and you'll stay on the old protocol, because the version that speaks the new one has a different name",
      "why": "verbless phrase"
    },
    {
      "line": 127,
      "habit": "fragment",
      "severity": "low",
      "quote": "On the Python side it's the same package, `mcp`, so moving is an ordinary major-version upgrade that someone has to choose to take",
      "why": "verbless phrase"
    },
    {
      "line": 129,
      "habit": "fragment",
      "severity": "low",
      "quote": "## Two ways to say you don't know a method",
      "why": "verbless phrase"
    },
    {
      "line": 131,
      "habit": "fragment",
      "severity": "low",
      "quote": "The servers that don't speak July turn it down in two different ways, and the split follows the SDK again",
      "why": "verbless phrase"
    },
    {
      "line": 133,
      "habit": "fragment",
      "severity": "low",
      "quote": "The TypeScript ones answer `-32601 Method not found`",
      "why": "verbless phrase"
    },
    {
      "line": 135,
      "habit": "fragment",
      "severity": "low",
      "quote": "The Python ones don't",
      "why": "verbless phrase"
    },
    {
      "line": 137,
      "habit": "fragment",
      "severity": "low",
      "quote": "```console $ discover-probe stdio -- uvx dbt-mcp``",
      "why": "verbless phrase"
    },
    {
      "line": 139,
      "habit": "fragment",
      "severity": "low",
      "quote": "target   uvx dbt-mcp",
      "why": "verbless phrase"
    },
    {
      "line": 141,
      "habit": "fragment",
      "severity": "low",
      "quote": "server   dbt",
      "why": "verbless phrase"
    },
    {
      "line": 143,
      "habit": "fragment",
      "severity": "low",
      "quote": "era      legacy-only",
      "why": "verbless phrase"
    },
    {
      "line": 145,
      "habit": "fragment",
      "severity": "low",
      "quote": "   FAIL  discover             rejected: error -32601: Method not found",
      "why": "verbless phrase"
    },
    {
      "line": 147,
      "habit": "fragment",
      "severity": "low",
      "quote": "   pass  handshake            negotiated 2025-11-25",
      "why": "verbless phrase"
    },
    {
      "line": 149,
      "habit": "fragment",
      "severity": "low",
      "quote": "## What running it on real servers taught me about the probe",
      "why": "verbless phrase"
    },
    {
      "line": 151,
      "habit": "fragment",
      "severity": "low",
      "quote": "MotherDuck's first result was `neither`, meaning it had answered and refused both protocols",
      "why": "verbless phrase"
    },
    {
      "line": 155,
      "habit": "fragment",
      "severity": "low",
      "quote": "The probe exited successfully",
      "why": "verbless phrase"
    },
    {
      "line": 159,
      "habit": "fragment",
      "severity": "low",
      "quote": "A crashed server now reads as unreachable, exits with a failure code, and shows the tail of its stderr",
      "why": "verbless phrase"
    },
    {
      "line": 161,
      "habit": "fragment",
      "severity": "low",
      "quote": "## Run it yourself",
      "why": "verbless phrase"
    },
    {
      "line": 163,
      "habit": "fragment",
      "severity": "low",
      "quote": "```bash uvx --from 'git+https://github.com/pavanrao/data-tools#subdirectory=tools/discover-probe' \\",
      "why": "verbless phrase"
    },
    {
      "line": 165,
      "habit": "fragment",
      "severity": "low",
      "quote": "discover-probe stdio -- npx -y @modelcontextprotocol/server-everything",
      "why": "verbless phrase"
    },
    {
      "line": 167,
      "habit": "fragment",
      "severity": "low",
      "quote": "# anything after -- is the server command, passed through untouched",
      "why": "verbless phrase"
    },
    {
      "line": 169,
      "habit": "fragment",
      "severity": "low",
      "quote": "discover-probe --json stdio -- uvx mcp-server-time",
      "why": "verbless phrase"
    },
    {
      "line": 171,
      "habit": "fragment",
      "severity": "low",
      "quote": "## Loose ends",
      "why": "verbless phrase"
    },
    {
      "line": 173,
      "habit": "fragment",
      "severity": "low",
      "quote": "It only speaks stdio so far, which every server here offers",
      "why": "verbless phrase"
    },
    {
      "line": 175,
      "habit": "fragment",
      "severity": "low",
      "quote": "I also haven't probed anything running on someone else's infrastructure, because that means sending requests to their endpoints and I haven't decided to do that yet",
      "why": "verbless phrase"
    },
    {
      "line": 177,
      "habit": "fragment",
      "severity": "low",
      "quote": "Capabilities varied a lot more than protocols did",
      "why": "verbless phrase"
    },
    {
      "line": 179,
      "habit": "fragment",
      "severity": "low",
      "quote": "The AWS server and mine, both on Python v2, advertise change notifications only under the new protocol",
      "why": "verbless phrase"
    },
    {
      "line": 181,
      "habit": "fragment",
      "severity": "low",
      "quote": "MotherDuck, also Python v2, does the reverse for its tool list",
      "why": "verbless phrase"
    },
    {
      "line": 183,
      "habit": "fragment",
      "severity": "low",
      "quote": "Context7 reports identical capabilities in both",
      "why": "verbless phrase"
    },
    {
      "line": 185,
      "habit": "fragment",
      "severity": "low",
      "quote": "Four servers isn't enough to tell whether those differences come from the SDKs or from how each server was written",
      "why": "verbless phrase"
    },
    {
      "line": 187,
      "habit": "fragment",
      "severity": "low",
      "quote": "The table will change as soon as the reference servers move to v2 SDKs",
      "why": "verbless phrase"
    },
    {
      "line": 189,
      "habit": "fragment",
      "severity": "low",
      "quote": "I've dated it for that reason, and would re-run it before quoting it anywhere",
      "why": "verbless phrase"
    },
    {
      "line": 191,
      "habit": "fragment",
      "severity": "low",
      "quote": "## Run it yourself",
      "why": "verbless phrase"
    },
    {
      "line": 193,
      "habit": "fragment",
      "severity": "low",
      "quote": "```bash uvx --from 'git+https://github.com/pavanrao/data-tools#subdirectory=tools/discover-probe' \\",
      "why": "verbless phrase"
    },
    {
      "line": 195,
      "habit": "fragment",
      "severity": "low",
      "quote": "discover-probe stdio -- npx -y @modelcontextprotocol/server-everything",
      "why": "verbless phrase"
    },
    {
      "line": 197,
      "habit": "fragment",
      "severity": "low",
      "quote": "# anything after -- is the server command, passed through untouched",
      "why": "verbless phrase"
    },
    {
      "line": 199,
      "habit": "fragment",
      "severity": "low",
      "quote": "discover-probe --json stdio -- uvx mcp-server-time",
      "why": "verbless phrase"
    },
    {
      "line": 201,
      "habit": "fragment",
      "severity": "low",
      "quote": "## Loose ends",
      "why": "verbless phrase"
    },
    {
      "line": 203,
      "habit": "fragment",
      "severity": "low",
      "quote": "It exits `0` when every listing a server advertised worked",
      "why": "verbless phrase"
    },
    {
      "line": 205,
      "habit": "fragment",
      "severity": "low",
      "quote": "## Loose ends",
      "why": "verbless phrase"
    },
    {
      "line": 207,
      "habit": "fragment",
      "severity": "low",
      "quote": "It only speaks stdio so far, which every server here offers",
      "why": "verbless phrase"
    },
    {
      "line": 209,
      "habit": "fragment",
      "severity": "low",
      "quote": "I also haven't probed anything running on someone else's infrastructure, because that means sending requests to their endpoints and I haven't decided to do that yet",
      "why": "verbless phrase"
    },
    {
      "line": 211,
      "habit": "fragment",
      "severity": "low",
      "quote": "Capabilities varied a lot more than protocols did",
      "why": "verbless phrase"
    },
    {
      "line": 213,
      "habit": "fragment",
      "severity": "low",
      "quote": "The AWS server and mine, both on Python v2, advertise change notifications only under the new protocol",
      "why": "verbless phrase"
    },
    {
      "line": 215,
      "habit": "fragment",
      "severity": "low",
      "quote": "MotherDuck, also Python v2, does the reverse for its tool list",
      "why": "verbless phrase"
    },
    {
      "line": 217,
      "habit": "fragment",
      "severity": "low",
      "quote": "Context7 reports identical capabilities in both",
      "why": "verbless phrase"
    },
    {
      "line": 219,
      "habit": "fragment",
      "severity": "low",
      "quote": "Four servers isn't enough to tell whether those differences come from the SDKs or from how each server was written",
      "why": "verbless phrase"
    },
    {
      "line": 221,
      "habit": "fragment",
      "severity": "low",
      "quote": "The table will change as soon as the reference servers move to v2 SDKs",
      "why": "verbless phrase"
    },
    {
      "line": 223,
      "habit": "fragment",
      "severity": "low",
      "quote": "I've dated it for that reason, and would re-run it before quoting it anywhere",
      "why": "verbless phrase"
    },
    {
      "line": 225,
      "habit": "fragment",
      "severity": "low",
      "quote": "The code.",
      "why": "verbless phrase"
    },
    {
      "line": 227,
      "habit": "fragment",
      "severity": "low",
      "quote": "code> discover-probe lives in <a href=\"https://github.com/pavanrao/data-tools\">pavanrao/data-tools</a> under <code>tools/discover-probe/</code>.",
      "why": "verbless phrase"
    },
    {
      "line": 229,
      "habit": "fragment",
      "severity": "low",
      "quote": "Its design record, <code>docs/011_discover-probe.md</code>, has the full table with versions and the corrections to what I first wrote down, and the raw measurement is in <code>evidence/discover-probe.jsonl</code>.",
      "why": "verbless phrase"
    },
    {
      "line": 231,
      "habit": "fragment",
      "severity": "low",
      "quote": "How this was made.",
      "why": "verbless phrase"
    },
    {
      "line": 233,
      "habit": "fragment",
      "severity": "low",
      "quote": "code> discover-probe and this write-up were both built with Claude Code.",
      "why": "verbless phrase"
    },
    {
      "line": 235,
      "habit": "fragment",
      "severity": "low",
      "quote": "Every piece of terminal output here was copied from a run on 14 September 2026, and all twelve servers were probed on the same build of the tool.",
      "why": "verbless phrase"
    },
    {
      "line": 237,
      "habit": "fragment",
      "severity": "low",
      "quote": "Written against MCP protocol revision 2026-07-28.",
      "why": "verbless phrase"
    }
  ]
}
```

**Summary**

The draft contains many instances of the "fragment" habit, where verbless phrases are used to stand in for sentences. These habits are found throughout the text, often in a row, and can make the text difficult to follow. The "restatement" habit is also found, where points are repeated in adjacent sentences, adding no new information.

The "dramatic-beat" habit is found in sentence 13, where a short sentence is used to create a pause or reveal. The "cliche-emphasis" habit is found in sentences 29 and 55, where stock phrases are used to emphasize points.

The "generic-detail" habit is found in sentence 35, where a vague phrase is used instead of a specific detail.

Overall, the draft could benefit from a more varied and specific writing style to improve its clarity and engagement.

**Recommendations**

* Avoid using verbless phrases to stand in for sentences. Instead, use complete sentences to convey information.
* Avoid repeating points in adjacent sentences. If a point needs to be made twice, consider using a summary or a different approach.
* Vary your writing style to avoid using stock phrases to emphasize points.
* Use specific details instead of vague phrases to convey information.

Note: The above recommendations are based on the findings of the review, but they should not be considered as the final solution. The author of the draft should review the recommendations and decide what changes to make based on their specific needs and goals.