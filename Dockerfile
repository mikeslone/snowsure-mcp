# SnowSure is a HOSTED, remote streamable-HTTP MCP server (https://www.snowsure.ai/mcp).
# This image is a thin stdio<->remote bridge (via mcp-remote) so introspection-based
# directory checks (e.g. Glama) can start a local process that connects to the hosted
# endpoint and answers tools/list. It is NOT a second implementation of the server —
# it forwards to the same public endpoint every other client uses.
FROM node:22-slim
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["npx", "-y", "mcp-remote", "https://www.snowsure.ai/mcp"]
