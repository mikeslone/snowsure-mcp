"""snowsure CLI — live ski & snow data from https://www.snowsure.ai.

Commands:
    snowsure report [--sort ...] [--limit N] [--region ...]
    snowsure resort <slug>
    snowsure ask "where is the best powder right now?"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from snowsure.client import DEFAULT_BASE_URL, SnowSureClient, SnowSureError


def _fmt_cm(value: Any) -> str:
    if value is None:
        return "-"
    return f"{value:g}cm" if isinstance(value, (int, float)) else str(value)


def _print_resort_rows(resorts: List[Dict[str, Any]]) -> None:
    header = f"{'RESORT':<34} {'COUNTRY':<16} {'SCORE':>5} {'24H':>7} {'7D':>7} {'DEPTH':>7}"
    print(header)
    print("-" * len(header))
    for r in resorts:
        cond = r.get("conditions") or {}
        score = (r.get("snowSure") or {}).get("score")
        print(
            f"{(r.get('name') or r.get('slug') or '?')[:33]:<34} "
            f"{(r.get('country') or '-')[:15]:<16} "
            f"{score if score is not None else '-':>5} "
            f"{_fmt_cm(cond.get('snowfall24hCm')):>7} "
            f"{_fmt_cm(cond.get('snowfall7dCm')):>7} "
            f"{_fmt_cm(cond.get('snowDepthCm')):>7}"
        )


def cmd_report(client: SnowSureClient, args: argparse.Namespace) -> int:
    data = client.get_snow_report(sort=args.sort, limit=args.limit, region=args.region)
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    resorts = data.get("resorts") or []
    if not resorts:
        print("No resorts returned.")
        return 1
    _print_resort_rows(resorts)
    return 0


def cmd_resort(client: SnowSureClient, args: argparse.Namespace) -> int:
    resort = client.get_resort(args.slug)
    if args.json:
        print(json.dumps(resort, indent=2))
        return 0
    snow = resort.get("snow") or {}
    snow_sure = resort.get("snowSure") or {}
    elevation = resort.get("elevation") or {}
    forecast = resort.get("forecast") or {}
    print(f"{resort.get('name', args.slug)} — {resort.get('country', '?')}")
    if snow_sure.get("score") is not None:
        rating = f" ({snow_sure['rating']})" if snow_sure.get("rating") else ""
        print(f"  SnowSure score: {snow_sure['score']}/100{rating}")
    print(f"  Depth: {_fmt_cm(snow.get('depthCm'))}  24h: {_fmt_cm(snow.get('last24hCm'))}  7d: {_fmt_cm(snow.get('last7dCm'))}  14d forecast: {_fmt_cm(forecast.get('total14dCm'))}")
    if elevation.get("summit") is not None:
        print(f"  Elevation: {elevation.get('base', '?')}–{elevation.get('summit', '?')}")
    print(f"  https://www.snowsure.ai/resorts/{resort.get('slug', args.slug)}")
    return 0


def cmd_ask(client: SnowSureClient, args: argparse.Namespace) -> int:
    data = client.ask(args.question, resort_slug=args.resort, locale=args.locale,
                      format="json" if args.json else "markdown")
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    print(data.get("answer", ""))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snowsure",
        description="Live ski & snow data from SnowSure (https://www.snowsure.ai).",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=argparse.SUPPRESS)
    parser.add_argument("--api-key", default=None, help="Optional partner API key (X-API-Key).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_report = sub.add_parser("report", help="Global snow rankings (SnowSure score, fresh snow, depth).")
    p_report.add_argument("--sort", choices=["snowsure", "forecast", "recent", "depth"], default=None)
    p_report.add_argument("--limit", type=int, default=None, help="Max results (max 100).")
    p_report.add_argument("--region", choices=["europe", "north-america", "asia", "oceania", "south-america"], default=None)
    p_report.add_argument("--json", action="store_true", help="Print raw JSON.")
    p_report.set_defaults(func=cmd_report)

    p_resort = sub.add_parser("resort", help="Live conditions and detail for one resort slug.")
    p_resort.add_argument("slug", help="Resort slug, e.g. matterhorn-ski-paradise")
    p_resort.add_argument("--json", action="store_true", help="Print raw JSON.")
    p_resort.set_defaults(func=cmd_resort)

    p_ask = sub.add_parser("ask", help="Ask the SnowSure Answer Engine a natural-language question.")
    p_ask.add_argument("question", help='e.g. "where is the best powder in the alps right now?"')
    p_ask.add_argument("--resort", default=None, help="Optional resort slug to scope the answer.")
    p_ask.add_argument("--locale", choices=["en", "es", "fr", "de", "it", "ja"], default=None)
    p_ask.add_argument("--json", action="store_true", help="Structured JSON answer payload.")
    p_ask.set_defaults(func=cmd_ask)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with SnowSureClient(base_url=args.base_url, api_key=args.api_key) as client:
            return args.func(client, args)
    except SnowSureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
