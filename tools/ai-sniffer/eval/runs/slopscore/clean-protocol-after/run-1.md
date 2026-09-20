```json
{
 "findings": [
  {
   "line": 1,
   "habit": null,
   "severity": "n/a",
   "quote": "Older clients and servers are still in use, so both SDKs kept the old path alongside the new one, and a given server might speak either, or both.\n\n",
   "rule": "GENERIC_SENTENCE",
   "why": ""
  },
  {
   "line": 1,
   "habit": null,
   "severity": "n/a",
   "quote": "The obvious move is to connect with the SDK and look at what you got. The trouble is that the Python SDK's client, left on its default, does exactly the negotiation you're trying to observe. It tries , falls back to  if that fails, and hands you a working session. Whether the server spoke the new protocol or the old one isn't recorded anywhere you can easily get at. ",
   "rule": "CADENCE_UNIFORM_RUN",
   "why": ""
  },
  {
   "line": 31,
   "habit": null,
   "severity": "n/a",
   "quote": "—",
   "rule": "FORMATTING_EM_DASH",
   "why": ""
  },
  {
   "line": 1,
   "habit": null,
   "severity": "n/a",
   "quote": "The connections have to be separate, because one that has answered  is locked into the new protocol, so asking it for a handshake afterwards tells you about the lock and nothing about the server.\n\n",
   "rule": "GENERIC_SENTENCE",
   "why": ""
  },
  {
   "line": 1,
   "habit": null,
   "severity": "n/a",
   "quote": "I also haven't probed anything running on someone else's infrastructure, because that means sending requests to their endpoints and I haven't decided to do that yet.\n\n",
   "rule": "GENERIC_SENTENCE",
   "why": ""
  }
 ]
}
```
