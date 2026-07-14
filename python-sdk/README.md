# snowsure

Python SDK and CLI for [SnowSure](https://www.snowsure.ai) — live ski & snow data: current conditions, 14-day multi-model forecasts, powder rankings, and a grounded natural-language snow Answer Engine across 500+ resorts worldwide. No API key required.

```bash
pip install snowsure
```

## SDK

```python
from snowsure import SnowSureClient

client = SnowSureClient()

# Global snow rankings (SnowSure score, fresh snow, depth, 14-day forecast)
report = client.get_snow_report(sort="recent", region="europe", limit=10)
for resort in report["resorts"]:
    print(resort["name"], resort["snowSure"]["score"], resort["conditions"]["snowfall24hCm"])

# List / filter resorts
resorts = client.get_resorts(country="Switzerland", sort="score", limit=20)

# One resort in full detail (slugs are lowercase-hyphenated)
zermatt = client.get_resort("matterhorn-ski-paradise")

# Grounded natural-language Q&A
answer = client.ask("where is the best powder in the alps right now?")
print(answer["answer"])
```

All SnowSure API responses use a `{"meta": ..., "data": ...}` envelope; client methods return the unwrapped `data` payload. The most recent `meta` block (source, timestamp) is available on `client.last_meta`. Errors raise `snowsure.SnowSureError`.

`ask()` uses the public keyless tier (`partnerId: "chatgpt"`). Partners with a SnowSure API key can pass `SnowSureClient(api_key="...", partner_id="your-partner-id")`.

## CLI

The package installs a `snowsure` command:

```bash
snowsure report                         # global snow rankings
snowsure report --sort recent --region europe --limit 10
snowsure resort matterhorn-ski-paradise # live conditions for one resort
snowsure ask "how much snow fell at Niseko this week?"
```

Add `--json` to any command for the raw JSON payload.

## Related

- MCP server (39 tools, streamable HTTP, no auth): `https://www.snowsure.ai/mcp`
- OpenAPI spec: https://www.snowsure.ai/openapi.json
- LLM guide: https://www.snowsure.ai/llms.txt
- Repo: https://github.com/mikeslone/snowsure-mcp

## License

MIT
