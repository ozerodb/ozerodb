"""Rewrite the PROJECTS block of README.md with the owner's most-starred public repos."""
import json
import os
import re
import urllib.request

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "ozerodb")
COUNT = 2
EXCLUDE = {OWNER, f"{OWNER}.github.io"}  # profile repo and landing page
README = "README.md"

CARD = (
    '  <a href="https://github.com/{owner}/{repo}"><img width="49%" '
    'src="https://github-readme-stats.vercel.app/api/pin/?username={owner}&repo={repo}'
    '&hide_border=true&theme=transparent&title_color=5EB1BF&icon_color=5EB1BF'
    '&text_color=8b949e" alt="{repo}" /></a>'
)


def fetch_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "readme-updater"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def pick(repos):
    eligible = [
        r for r in repos
        if not r["private"] and not r["fork"] and r["name"] not in EXCLUDE
    ]
    # Most stars first; ties broken by most recent push.
    eligible.sort(key=lambda r: (r["stargazers_count"], r["pushed_at"]), reverse=True)
    return [r["name"] for r in eligible[:COUNT]]


def render(names):
    cards = "\n".join(CARD.format(owner=OWNER, repo=n) for n in names)
    return f"<!-- PROJECTS:START -->\n<p>\n{cards}\n</p>\n<!-- PROJECTS:END -->"


def update(text, names):
    pattern = re.compile(r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->", re.S)
    if not pattern.search(text):
        raise SystemExit("PROJECTS markers not found in README.md")
    return pattern.sub(lambda _: render(names), text)


if __name__ == "__main__":
    with open(README, encoding="utf-8") as f:
        old = f.read()
    new = update(old, pick(fetch_repos()))
    if new != old:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README updated")
    else:
        print("No changes")
