# Publishing checklist (maintainer)

Steps to publish the developer artifacts in this repo. Nothing here happens automatically — each step below is a manual action.

## 1. Push to GitHub

From `/Users/mikeslone/snowsure-mcp`:

```bash
git checkout -b developer-artifacts   # or commit straight to main
git add .claude .cursor python-sdk CLAUDE.md README.md PUBLISHING.md
git commit -m "Add agent configs, snowsure Python SDK/CLI, and skill"
git push origin developer-artifacts   # open a PR, or: git push origin main
```

Once merged to `main`, the Ora "agent platform configs" check is satisfied by `.claude/` and `.cursor/` being in this public repo. Make sure the homepage (snowsure.ai) or llms.txt links to https://github.com/mikeslone/snowsure-mcp so the checker can find it.

## 2. Publish `snowsure` to PyPI (SDK + CLI checks)

One-time setup: create a PyPI account, then an API token at https://pypi.org/manage/account/token/ (scope it to the project after first upload).

```bash
cd python-sdk
python3 -m pip install --upgrade build twine

# optional but recommended: run the tests first
python3 -m pip install -e ".[dev]" && python3 -m pytest

python3 -m build            # produces dist/snowsure-0.1.0.tar.gz + .whl
python3 -m twine check dist/*
python3 -m twine upload dist/*   # username: __token__, password: pypi-...
```

Verify with `pip install snowsure && snowsure report --limit 5`.

Optional cleanup before/after publishing: the SDK's `ask()` defaults to `partnerId: "chatgpt"` because that is the only keyless tier in `checkAnswerEngineAccess` (snowsure-web `lib/answer-engine-api-auth.ts`). For cleaner attribution, whitelist a dedicated keyless partner id (e.g. `python-sdk`) in `isChatGptPartner` (or a new allowlist) and change `DEFAULT_PARTNER_ID` in `python-sdk/src/snowsure/client.py`, then bump to 0.1.1.

## 3. Self-publish the skill on skills.sh

How skills.sh actually works (checked July 2026, https://www.skills.sh/docs): there is **no submission form or `publish` command**. The directory is populated by anonymous telemetry from the open-source skills CLI (github.com/vercel-labs/skills) — a repo/skill appears on the leaderboard after someone installs it with `npx skills add`.

So, after step 1 is merged to `main`:

```bash
# 1. Confirm the CLI discovers the skill in this repo
npx skills add mikeslone/snowsure-mcp --list

# 2. Install it once yourself — this seeds the telemetry that lists it
npx skills add mikeslone/snowsure-mcp --skill snowsure -y
```

The page then appears at https://skills.sh/mikeslone/snowsure-mcp (cached; may take a while). Two optional follow-ups:

- Add the install badge to README.md:
  `[![skills.sh](https://skills.sh/b/mikeslone/snowsure-mcp)](https://skills.sh/mikeslone/snowsure-mcp)`
- If more skills are added later, a root `skills.sh.json` can group them on the repo page (see https://www.skills.sh/docs — "Customize repo pages").

If `--list` does not find the skill under `.claude/skills/`, move/copy it to `skills/snowsure/SKILL.md` at the repo root (the layout used by anthropics/skills and vercel-labs/agent-skills) and keep `.claude/skills/snowsure/SKILL.md` as the Claude Code copy.

## 4. Optional: Homebrew tap for the CLI

Cheapest credible path — a personal tap that installs the PyPI package:

```bash
# one-time: create the public repo github.com/mikeslone/homebrew-snowsure
brew tap-new mikeslone/snowsure
cd "$(brew --repository mikeslone/snowsure)"
```

Create `Formula/snowsure.rb` (after the PyPI release exists, take the sdist URL + sha256 from https://pypi.org/project/snowsure/#files):

```ruby
class Snowsure < Formula
  include Language::Python::Virtualenv

  desc "Live ski & snow data CLI (SnowSure)"
  homepage "https://www.snowsure.ai"
  url "https://files.pythonhosted.org/packages/.../snowsure-0.1.0.tar.gz"
  sha256 "<sha256 of the sdist>"
  license "MIT"

  depends_on "python@3.12"

  # brew update-python-resources snowsure  # fills in httpx deps
  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "snowsure", shell_output("#{bin}/snowsure --help")
  end
end
```

Run `brew update-python-resources snowsure` to generate the `resource` blocks for httpx and its dependencies, then push the tap repo. Users install with `brew install mikeslone/snowsure/snowsure`. (Homebrew/core is possible later but requires notability review.)

## 5. Future work (intentionally not scaffolded)

- **Go SDK** (`github.com/mikeslone/snowsure-go`): a small module wrapping the same four endpoints would satisfy the third SDK-ecosystem slot. Go modules are "published" just by tagging a public repo (`v0.1.0`) — no registry upload.
- **RubyGems** (`gem snowsure`): equivalent thin client + `gem build && gem push`.
- Link the GitHub repo prominently from snowsure.ai (footer or /developers) and from llms.txt so ecosystem checkers can discover it.
