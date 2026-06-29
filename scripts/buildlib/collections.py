import re
import unicodedata

from .markdown import render_markdown
from .paths import ROOT


def slugify(value):
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower())
    return normalized.strip("-")


def collection_slug(item):
    item_id = item.get("id")
    if item_id is not None and str(item_id).strip():
        return str(item_id).strip()

    title = item.get("title", "item")
    return slugify(title)


def markdown_collection_index(items, folder):
    blocks = []

    for item in items:
        if isinstance(item, str):
            blocks.append(f"### {item}")
            continue

        title = item.get("title", "TODO: add title")
        link = f"{folder}/{collection_slug(item)}.html"
        block = [f"### [{title}]({link})"]

        details = []
        if item.get("event"):
            details.append(item["event"])
        if item.get("date"):
            details.append(str(item["date"]))
        if details:
            block.append(", ".join(details))

        blocks.append("\n".join(block).rstrip())

    return "\n\n".join(blocks)


def resolve_collection_text(value, context):
    if not value:
        return ""

    candidate = ROOT / str(value)
    if candidate.exists() and candidate.is_file():
        return render_markdown(candidate.read_text(encoding="utf-8"), context).strip()

    return str(value).strip()


def collection_summary_text(item, context, folder):
    explicit = item.get("summary_md") or item.get("content_md")
    if explicit:
        return resolve_collection_text(explicit, context)

    item_id = item.get("id")
    if item_id is not None and str(item_id).strip():
        candidate = ROOT / "content" / folder / f"{item_id}.md"
        if candidate.exists() and candidate.is_file():
            return render_markdown(candidate.read_text(encoding="utf-8"), context).strip()

    return ""


def markdown_organizing_list(items, folder="organizing"):
    blocks = []
    for item in items:
        if isinstance(item, str):
            blocks.append(f"- {item}")
            continue

        title = item.get("title", "TODO: add title")
        blocks.append(f"- [{title}]({folder}/{collection_slug(item)}.html)")

    return "\n".join(blocks)
