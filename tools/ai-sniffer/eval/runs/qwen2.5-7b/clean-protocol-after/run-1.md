```json
{
  "findings": [
    {
      "line": 89,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "| Server | Publisher | SDK underneath | Speaks July? |",
      "why": "The header row is vague and doesn't provide specific details about what the terms mean."
    },
    {
      "line": 100,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "| `sqlite-mcp` | me | Python v2 | Yes |",
      "why": "The detail 'me' is vague and doesn't specify the exact contribution or role."
    },
    {
      "line": 123,
      "habit": "generic-detail",
      "severity": "medium",
      "quote": "If you maintain a TypeScript server, Dependabot will keep bumping `@modelcontextprotocol/sdk` for you and you'll stay on the old protocol, because the version that speaks the new one has a different name.",
      "why": "The detail 'you' is vague and doesn't specify the exact action or responsibility."
    }
  ]
}
```

### Summary
The most recurring habits in the draft are `generic-detail`, with several instances found. These instances are mostly in header rows and explanations that lack specific details, making them vague and less helpful to the reader.