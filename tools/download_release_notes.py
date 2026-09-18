from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://api.github.com/repos/gruntwork-io/terragrunt/releases"


def fetch_releases(per_page: int = 100) -> list[dict[str, object]]:
    releases: list[dict[str, object]] = []
    page = 1
    while True:
        request = Request(
            f"{API_URL}?page={page}&per_page={per_page}",
            headers={"Accept": "application/vnd.github+json"},
        )
        with urlopen(request) as response:
            batch = json.load(response)
        releases.extend(batch)
        if len(batch) < per_page:
            return releases
        page += 1


def write_release_notes(output_dir: Path, releases: list[dict[str, object]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for release in releases:
        if release["draft"] or release["prerelease"]:
            continue
        tag = str(release["tag_name"])
        (output_dir / f"{tag}.md").write_text(
            f"# {tag}\n\n"
            f"- Tag: `{tag}`\n"
            f"- Published: {release['published_at']}\n"
            f"- URL: {release['html_url']}\n\n"
            f"## Release Notes\n{release['body'] or ''}\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Terragrunt release notes.")
    parser.add_argument("--output-dir", type=Path, default=Path("reference/terragrunt-releases"))
    args = parser.parse_args()
    write_release_notes(args.output_dir, fetch_releases())


if __name__ == "__main__":
    main()
