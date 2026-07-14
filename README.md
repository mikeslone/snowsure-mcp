# SnowSure MCP Server

[![Glama MCP server](https://glama.ai/mcp/servers/@mikeslone/snowsure-mcp/badge)](https://glama.ai/mcp/servers/@mikeslone/snowsure-mcp)
[![ora agent readiness score](https://ora.ai/api/badge/snowsure.ai)](https://ora.ai/scan/snowsure.ai)

**Hosted, remote [Model Context Protocol](https://modelcontextprotocol.io) server for live ski & snow data — no install, keyless read access.**

SnowSure gives AI assistants and agents grounded, verified snow intelligence: live conditions, 14‑day multi‑model forecasts, powder rankings, resort guides, webcams, ski‑pass intelligence, avalanche/road safety, and a natural‑language Answer Engine across **480+ ski resorts worldwide**. Every answer is grounded in SnowSure's data (seven weather models + verified resort‑reported ground truth) — never open web search.

- **Endpoint:** `https://www.snowsure.ai/mcp`
- **Transport:** Streamable HTTP (MCP spec `2025-03-26`)
- **Auth:** none (public, read‑only). A handful of write/personalization tools use an optional signed‑in SnowSure account.
- **Tools:** 39
- **Website:** https://www.snowsure.ai

## Connect

### Claude / ChatGPT / any remote‑MCP client
Add a custom connector with the URL — no token, no config:

```
https://www.snowsure.ai/mcp
```

### Cursor / config file
```json
{
  "mcpServers": {
    "snowsure": { "url": "https://www.snowsure.ai/mcp" }
  }
}
```

### Via Smithery
Install from the [Smithery](https://smithery.ai) directory — the server needs **no connection parameters**.

## What you can ask

> where is the best powder in the alps right now
> compare the 7‑day snow forecast for Niseko and Hakuba
> plan a 5‑day ski trip to Colorado in late January
> which resorts got fresh snow in the last 24 hours
> what is the SnowSure score and base depth at Zermatt today

## Tools

**Ask & discover**
- `ask_snowdata` — grounded natural‑language Q&A (the primary tool for chat)
- `search_resorts` — resolve a name to canonical resort slugs
- `get_resort` — full resort detail: live conditions, 7‑model forecast, history, webcams
- `get_resort_info` — resort guide card: elevation, lifts/runs, season dates, ski passes
- `get_resort_photos` — resort photo gallery
- `get_destination` — multi‑mountain hubs (Niseko, Chamonix, Hakuba, …)
- `find_resorts_by_criteria` — filter by depth, elevation, runs, score, country, region
- `get_regional_summary` — regional/country statistics and top resorts by score
- `get_southern_hemisphere_report` — in‑season AU/NZ/AR/CL report (NH off‑season)
- `get_season_openings` — resorts opening on a given day

**Snow & forecasts**
- `get_snow_report` — global rankings by SnowSure score, fresh snow, depth, or 14‑day forecast
- `find_best_powder` — resorts with the freshest 24‑hour snowfall
- `get_weather_forecast` — day‑by‑day weather up to 14 days
- `compare_forecasts` — 14‑day forecast across all 7 models with a confidence rating
- `get_snow_history` — season‑to‑date totals plus 5‑yr and 30‑yr averages
- `get_ml_trends` — SnowSure ML datasets: powder/bluebird leaderboards, model accuracy, forecast trust
- `get_insights` / `list_insight_categories` — season norms, forecast‑trust and other intelligence cards

**Passes & planning**
- `get_pass` / `find_pass_resorts` / `compare_passes` — Epic, Ikon, Mountain Collective, Indy, …
- `compare_resorts` — compare 2–4 resorts side by side
- `plan_ski_trip` — trip recommendations for a region, ability, and dates
- `plan_ski_road_trip` — multi‑stop drivable route with day allocation and conditions
- `find_powder_trips` — bookable powder trips ranked by 14‑day forecast, paired with lodging

**Safety & roads**
- `get_avalanche` — official avalanche bulletin (US/Canada/Switzerland), relayed with issuer + link
- `get_operating_risk` — 48h wind‑hold / visibility / cold / heavy‑snow lift‑operation risk
- `get_road_access` / `get_road_cameras` / `get_road_weather` — chain control, DOT cameras, roadside weather (Caltrans/WSDOT/CDOT/UDOT)
- `get_webcam_status` — live webcams

**Account & personalized** (optional signed‑in SnowSure account)
- `save_resort` / `remove_saved_resort` / `list_saved_resorts`
- `subscribe_alerts` / `list_alerts` / `unsubscribe_alerts`
- `get_my_snow_report` — personalized report for your saved resorts
- `book_lodging` — lodging near a resort with a booking link (never auto‑books)

## Python SDK & CLI

```bash
pip install snowsure
```

```python
from snowsure import SnowSureClient

client = SnowSureClient()
client.get_snow_report(region="europe")["resorts"]   # global rankings
client.get_resort("matterhorn-ski-paradise")          # one resort in full
client.ask("where is the best powder right now?")     # grounded Q&A
```

The package also installs a `snowsure` CLI:

```bash
snowsure report --sort recent --region europe
snowsure resort matterhorn-ski-paradise
snowsure ask "how much snow fell at Niseko this week?"
```

Source: [`python-sdk/`](python-sdk/). Thin typed wrappers over the public REST API (`GET /api/v1/resorts`, `GET /api/v1/resorts/{slug}`, `GET /api/v1/snow-report`, `POST /api/v1/ask`) — no API key required.

## Agent configs & skills

This repo ships ready-made agent configuration so coding agents and assistants know how to use SnowSure:

- **Agent skill (Claude Code, Cursor, Codex, and other skills-compatible agents):** [`.claude/skills/snowsure/SKILL.md`](.claude/skills/snowsure/SKILL.md) — an [agent skill](https://skills.sh) covering the MCP server, REST API, resort-slug conventions, and answer guidelines. Install with:

  ```bash
  npx skills add mikeslone/snowsure-mcp
  ```

- **Cursor rules:** [`.cursor/rules/snowsure.mdc`](.cursor/rules/snowsure.mdc) — copy into your project's `.cursor/rules/`.
- **Repo agent guidance:** [`CLAUDE.md`](CLAUDE.md).

## Discovery documents

- Server card: https://www.snowsure.ai/.well-known/mcp/server-card.json
- MCP manifest: https://www.snowsure.ai/.well-known/mcp.json
- AI catalog: https://www.snowsure.ai/.well-known/ai-catalog.json
- OpenAPI: https://www.snowsure.ai/openapi.json
- LLM guide: https://www.snowsure.ai/llms.txt

## About

SnowSure is the consumer + agent surface of Snowdata's snow‑intelligence stack. The **SnowSure Score** (0–100) summarizes skiability from seven weather models, decades of archive, and verified resort ground truth. Forecasts are model‑based, not certainty; avalanche/safety data is relayed from official issuers with attribution.

## License

MIT — see [LICENSE](LICENSE). This repository contains public metadata and documentation for the hosted SnowSure MCP service.
