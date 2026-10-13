"""Validate generated site links, metadata and migration compatibility offline."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json
import re

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.cards, self.filters, self.resources = [], [], [], [], []
        self.slug = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag in ("script", "link"):
            resource = attrs.get("src", attrs.get("href", ""))
            self.links.append(resource)
            self.resources.append(resource)
        if "card" in attrs.get("class", "").split():
            self.cards.append(attrs)
        if "data-filter" in attrs:
            self.filters.append(attrs["data-filter"])
        if tag == "main":
            self.slug = attrs.get("data-slug")


pages = {p.resolve(): Page(p.read_text()) for p in [ROOT / "index.html", *ROOT.glob("posts/*.html")]}
errors = []
for file, page in pages.items():
    if len(page.ids) != len(set(page.ids)):
        errors.append(f"{file.name}: duplicate ID")
    for link in page.links:
        parsed = urlparse(link)
        if parsed.scheme or parsed.netloc:
            continue
        target = (file.parent / unquote(parsed.path)).resolve() if parsed.path else file
        if not target.exists():
            errors.append(f"{file.name}: missing {link}")
        if parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
            errors.append(f"{file.name}: missing fragment {link}")
    for resource in page.resources:
        if urlparse(resource).scheme or urlparse(resource).netloc:
            errors.append(f"{file.name}: non-local runtime resource {resource}")

home = pages[(ROOT / "index.html").resolve()]
metas = [json.loads(re.match(r"^---\n([\s\S]*?)\n---", p.read_text())[1]) for p in sorted(ROOT.glob("content/*.md"))]
expected = {meta["slug"]: meta for meta in metas}
if len(expected) != len(metas):
    errors.append("Duplicate source slug")
if set(card["data-slug"] for card in home.cards) != set(expected) or len(home.cards) != len(expected):
    errors.append("Homepage/source article mismatch")
if set(home.filters) != {"all", *(meta["topic"] for meta in metas)} or len(home.filters) != 6:
    errors.append("Expected all + five technical directions")
for card in home.cards:
    meta = expected[card["data-slug"]]
    if card["data-topic"] != meta["topic"] or card["href"] != f'posts/{meta["slug"]}.html':
        errors.append(f'{meta["slug"]}: mismatched card metadata')
for slug, meta in expected.items():
    page = pages.get((ROOT / f"posts/{slug}.html").resolve())
    if not page or page.slug != slug:
        errors.append(f"{slug}: missing page/progress key")
    if f'<title>{meta["title"]} · Agent Fieldnotes</title>' not in (ROOT / f"posts/{slug}.html").read_text():
        errors.append(f"{slug}: title metadata mismatch")
legacy_ids = json.loads((ROOT / "templates/heading-ids.json").read_text())
for slug, headings in legacy_ids.items():
    page = pages[(ROOT / f"posts/{slug}.html").resolve()]
    for anchor in headings.values():
        if anchor not in page.ids:
            errors.append(f"{slug}: missing legacy anchor #{anchor}")
script = (ROOT / "assets/search-index.js").read_text()
index = json.loads(script.removeprefix("window.FIELDNOTES_SEARCH = ").rstrip(";\n"))
if {entry["slug"] for entry in index} != set(expected) or len(index) != len(expected):
    errors.append("Search index/source mismatch")
for entry in index:
    if expected[entry["slug"]]["topic"] not in entry["text"]:
        errors.append(f'{entry["slug"]}: missing technical category in search')
if errors:
    raise SystemExit("\n".join(errors))
print(f"Validated {len(pages)} pages, {len(metas)} source/index entries, five directions, local resources and {sum(len(v) for v in legacy_ids.values())} legacy anchors.")
