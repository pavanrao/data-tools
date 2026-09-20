```json
{
  "findings": [
    {
      "line": 436,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "Because none of these raise an exception. Extraction "succeeds" and returns something.",
      "why": "The phrase 'something' is vague and does not specify what the extraction actually returns, potentially misleading readers."
    },
    {
      "line": 530,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "It differs per format, deliberately:",
      "why": "The phrase 'deliberately' is vague and does not provide specific reasons for the differences, which may leave readers uncertain."
    },
    {
      "line": 600,
      "habit": "generic-detail",
      "severity": "high",
      "quote": "This second index is what makes the last stage possible.",
      "why": "The phrase 'last stage' is vague and does not clarify which specific stage is being referred to, potentially confusing readers."
    }
  ]
}
```

Summary: The draft frequently uses vague phrases that do not provide specific details, which could lead to reader confusion. These habits are most prevalent in sections explaining the mechanisms and outputs of the tool.