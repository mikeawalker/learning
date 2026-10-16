"""Generate a table-of-contents landing page for the JupyterLite site.

Scans the contents directory for notebooks and writes an index.html into the
built site that links each one to the single-notebook view.

Usage: python scripts/build_toc.py <contents-dir> <output-dir>
"""

import html
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

SITE_TITLE = "Notebooks"


def filename_title(path):
    return path.stem.replace("_", " ").replace("-", " ").strip().capitalize()


def notebook_title(path):
    """metadata.title, else the first markdown heading, else None."""
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if nb.get("metadata", {}).get("title"):
        return nb["metadata"]["title"]
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        for line in source.splitlines():
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip().replace("`", "")
    return None


def collect(contents):
    notebooks = [
        nb for nb in sorted(contents.rglob("*.ipynb"))
        if not any(part.startswith(".") for part in nb.relative_to(contents).parts)
    ]
    titles = {nb: notebook_title(nb) for nb in notebooks}
    # A heading shared by several notebooks (e.g. "Controls") isn't a useful title.
    counts = Counter(titles.values())
    sections = {}
    for nb in notebooks:
        title = titles[nb]
        if not title or counts[title] > 1:
            title = filename_title(nb)
        rel = nb.relative_to(contents)
        section = str(rel.parent) if rel.parent != Path(".") else ""
        sections.setdefault(section, []).append((title, rel.as_posix()))
    return sections


def render(sections):
    parts = []
    for section in sorted(sections, key=lambda s: (s != "", s)):
        heading = section.replace("/", " / ") if section else "General"
        items = []
        for title, rel in sections[section]:
            path = quote(rel)
            items.append(
                f'<li><a class="nb" href="notebooks/index.html?path={path}">{html.escape(title)}</a>'
                f'<span class="file">{html.escape(rel)}</span>'
                f'<a class="lab" href="lab/index.html?path={path}" title="Open in JupyterLab">Lab</a></li>'
            )
        parts.append(f"<section><h2>{html.escape(heading)}</h2><ul>{''.join(items)}</ul></section>")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_TITLE}</title>
<style>
  :root {{ --bg: #fafafa; --fg: #1f2328; --muted: #656d76; --card: #fff; --border: #d0d7de; --accent: #0969da; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #0d1117; --fg: #e6edf3; --muted: #8d96a0; --card: #161b22; --border: #30363d; --accent: #4493f8; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--fg);
         font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 40px 16px; }}
  h1 {{ margin: 0 0 4px; font-size: 1.8rem; }}
  .sub {{ color: var(--muted); margin: 0 0 32px; }}
  .sub a {{ color: var(--accent); }}
  h2 {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin: 28px 0 8px; }}
  ul {{ list-style: none; margin: 0; padding: 0; background: var(--card);
        border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  li {{ display: flex; align-items: baseline; gap: 12px; padding: 10px 14px; flex-wrap: wrap; }}
  li + li {{ border-top: 1px solid var(--border); }}
  .nb {{ color: var(--accent); text-decoration: none; font-weight: 500; }}
  .nb:hover {{ text-decoration: underline; }}
  .file {{ color: var(--muted); font-size: 0.8rem; font-family: ui-monospace, monospace; flex: 1; }}
  .lab {{ color: var(--muted); font-size: 0.8rem; text-decoration: none; }}
  .lab:hover {{ color: var(--accent); }}
</style>
</head>
<body>
<main>
  <h1>{SITE_TITLE}</h1>
  <p class="sub">Each notebook runs in your browser. Prefer the full IDE? <a href="lab/index.html">Open JupyterLab</a>.</p>
  {''.join(parts)}
</main>
</body>
</html>
"""


def main():
    contents, output = Path(sys.argv[1]), Path(sys.argv[2])
    (output / "index.html").write_text(render(collect(contents)), encoding="utf-8")


if __name__ == "__main__":
    main()
