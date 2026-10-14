#!/usr/bin/env python3
"""Build the site from Markdown.

Reads   md/*.md     (front matter: title, date, description; body in Markdown)
Writes  posts/*.html  (one page per entry)
Updates index.html    (the post list between the posts:start/posts:end markers)

Python standard library only — no pip installs, ever.
Run from anywhere:  python3 tools/build.py
"""

import html
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_DIR = ROOT / "md"
POSTS_DIR = ROOT / "posts"
INDEX = ROOT / "index.html"

# ---------------------------------------------------------------- template

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{TITLE}} — Saul Neri</title>
  <meta name="description" content="{{DESCRIPTION}}">
  <script>
    try { var t = localStorage.getItem("theme");
      if (t === "dark" || t === "light") document.documentElement.dataset.theme = t;
    } catch (e) {}
  </script>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <button class="theme-toggle" type="button" aria-label="Toggle dark mode" aria-pressed="false">
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <defs>
        <pattern id="hatch" width="2.6" height="2.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="2.6" stroke="currentColor" stroke-width="0.95"/>
        </pattern>
      </defs>
      <filter id="f-tm" x="-20%" y="-20%" width="140%" height="140%">
        <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="11"/>
        <feDisplacementMap in="SourceGraphic" scale="1.4"/>
      </filter>
      <path class="tm-hatch tm-half-r" d="M12 4 a 8 8 0 0 1 0 16 Z" filter="url(#f-tm)"/>
      <path class="tm-hatch tm-half-l" d="M12 4 a 8 8 0 0 0 0 16 Z" filter="url(#f-tm)"/>
      <path class="tm-stroke" d="M16.5 5.5 A 8 8 0 1 0 19 10" filter="url(#f-tm)"/>
    </svg>
  </button>

  <nav aria-label="Site">
    <a href="../index.html">&larr; home</a>
  </nav>

  <main>
    <article>
      <header>
        <h1>{{TITLE}}</h1>
        <p class="date"><time datetime="{{DATE}}">{{DATE}}</time></p>
      </header>

{{BODY}}
    </article>
  </main>

  <script>
    (function () {
      var root = document.documentElement;
      var btn = document.querySelector(".theme-toggle");
      function dark() {
        return root.dataset.theme ? root.dataset.theme === "dark"
          : matchMedia("(prefers-color-scheme: dark)").matches;
      }
      function sync() { btn.setAttribute("aria-pressed", String(dark())); }
      btn.addEventListener("click", function () {
        root.dataset.theme = dark() ? "light" : "dark";
        try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
        sync();
      });
      sync();
    })();
  </script>
</body>
</html>
"""

# ---------------------------------------------------------------- markdown

def inline(s: str) -> str:
    """Inline Markdown -> HTML, escaped first so raw < > & are safe."""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


SPECIAL = re.compile(r"^(#{1,3} |```|> |[-*] |\d+\. |(---|\*\*\*)\s*$)")


def md_to_html(text: str) -> str:
    """A deliberately small Markdown subset: enough to write, nothing to fear."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):                                   # code fence
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
        elif re.match(r"^#{1,3} ", line):                            # headings
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>{inline(line[level + 1:])}</h{level}>")
            i += 1
        elif re.match(r"^(---|\*\*\*)\s*$", line):                   # rule
            out.append("<hr>")
            i += 1
        elif line.startswith(">"):                                   # blockquote
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i].lstrip("> ").strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(block)) + "</blockquote>")
        elif re.match(r"^[-*] ", line):                              # bullet list
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i]):
                items.append("<li>" + inline(lines[i][2:]) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
        elif re.match(r"^\d+\. ", line):                             # numbered list
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\d+\. ", "", lines[i])) + "</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
        else:                                                        # paragraph
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not SPECIAL.match(lines[i]):
                para.append(lines[i])
                i += 1
            out.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n".join(out)


# ---------------------------------------------------------------- pieces

def split_front_matter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        sys.exit(f"  front matter missing (start the file with ---):\n{text[:40]}")
    meta = {}
    for ln in m.group(1).splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, m.group(2)


def render_post(meta, body_html, slug) -> str:
    for key in ("title", "date", "description"):
        if key not in meta:
            sys.exit(f"  md/{slug}.md is missing `{key}:` in its front matter")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", meta["date"]):
        sys.exit(f"  md/{slug}.md: date must be YYYY-MM-DD, got `{meta['date']}`")
    body = textwrap.indent(body_html, "      ")
    return (PAGE
            .replace("{{TITLE}}", html.escape(meta["title"], quote=True))
            .replace("{{DESCRIPTION}}", html.escape(meta["description"], quote=True))
            .replace("{{DATE}}", meta["date"])
            .replace("{{BODY}}", body))


def update_index(entries):
    """entries: list of (slug, title, date), newest first."""
    items = []
    for slug, title, date in entries:
        items.append(
            "        <li>\n"
            f"          <a href=\"posts/{slug}.html\">{html.escape(title, quote=False)}</a>\n"
            f"          <time datetime=\"{date}\">{date}</time>\n"
            "        </li>"
        )
    listing = "<!-- posts:start -->\n    <ol class=\"post-list\" reversed>\n" \
        + "\n".join(items) + "\n    </ol>\n    <!-- posts:end -->"
    src = INDEX.read_text()
    new, n = re.subn(
        r"<!-- posts:start -->.*?<!-- posts:end -->",
        lambda _: listing, src, flags=re.S)
    if n != 1:
        sys.exit("  index.html must contain exactly one pair of "
                 "<!-- posts:start --> / <!-- posts:end --> markers")
    INDEX.write_text(new)


# ---------------------------------------------------------------- main

def main():
    md_files = sorted(MD_DIR.glob("*.md"))
    if not md_files:
        sys.exit("  nothing to build: md/ contains no .md files")
    POSTS_DIR.mkdir(exist_ok=True)
    entries = []
    for path in md_files:
        slug = path.stem
        text = path.read_text()
        if not text.strip():
            print(f"  skipped md/{slug}.md (empty)")
            continue
        meta, body = split_front_matter(text)
        if meta.get("draft", "").lower() in ("true", "yes"):
            print(f"  skipped md/{slug}.md (draft)")
            continue
        page = render_post(meta, md_to_html(body), slug)
        (POSTS_DIR / f"{slug}.html").write_text(page)
        entries.append((slug, meta["title"], meta["date"]))
        print(f"  built posts/{slug}.html")
    entries.sort(key=lambda e: e[2], reverse=True)
    update_index(entries)
    print(f"  index.html updated ({len(entries)} entries, newest first)")


if __name__ == "__main__":
    main()
