#!/usr/bin/env python3
"""Fail CI if a public post is missing editorial approval metadata."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"
ALLOWED_LANGS = {"ru", "en"}


def frontmatter(text: str):
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return None
    result = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def check_posts():
    errors = []
    urls = set()
    posts = sorted(POSTS.glob("**/*.md")) if POSTS.exists() else []
    for post in posts:
        rel = post.relative_to(ROOT)
        name_ok = re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md", post.name)
        if not name_ok:
            errors.append(f"{rel}: expected YYYY-MM-DD-latin-slug.md filename")
        fm = frontmatter(post.read_text(encoding="utf-8"))
        if fm is None:
            errors.append(f"{rel}: missing YAML front matter")
            continue
        lang = fm.get("lang")
        if lang not in ALLOWED_LANGS:
            errors.append(f"{rel}: lang must be ru or en")
        if fm.get("approved", "").lower() != "true":
            errors.append(f"{rel}: approved: true required before publishing")
        if not fm.get("title"):
            errors.append(f"{rel}: title required")
        slug = fm.get("permalink", "")
        if not slug.startswith(f"/{lang}/articles/") or not slug.endswith("/"):
            errors.append(f"{rel}: permalink must start /{lang}/articles/ and end with /")
        if slug in urls:
            errors.append(f"{rel}: duplicate permalink {slug}")
        urls.add(slug)
    return errors, len(posts)


if __name__ == "__main__":
    errors, count = check_posts()
    if errors:
        print("PUBLICATION GUARD FAILED")
        for error in errors:
            print(" -", error)
        sys.exit(1)
    print(f"OK: {count} approved public posts checked; unmerged drafts remain unpublished.")
