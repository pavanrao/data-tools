"""A server that dies before speaking MCP, the way a misconfigured one does."""

import sys

print("Error: In-memory databases require the --read-write flag.", file=sys.stderr)
sys.exit(2)
