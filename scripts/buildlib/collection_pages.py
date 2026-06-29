from .collections import collection_slug, collection_summary_text
from .commands import run
from .paths import BUILD_DIR, COMMUNITY_PATH, ORGANIZING_DIR, ROOT, TALKS_DIR
from .site import site_nav
from .yaml_subset import read_yaml_subset


def build_talk_pages(context):
    community = read_yaml_subset(COMMUNITY_PATH)
    talks = community.get("talks", [])
    for path in TALKS_DIR.glob("*.html"):
        path.unlink(missing_ok=True)

    for talk in talks:
        if not isinstance(talk, dict):
            continue

        talk_key = collection_slug(talk)
        source = BUILD_DIR / "talks" / f"{talk_key}.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        output = TALKS_DIR / f"{talk_key}.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        body = [
            "---",
            f'title: "{talk.get("title", "Talk")}"',
            f'description: "{talk.get("title", "Talk")} at {talk.get("event", "Talk")}"',
            'favicon: "../favicon.ico"',
            "stylesheet: ../assets/css/site.css",
            "body_class: page",
            "---",
            "",
            site_nav("../"),
            "",
            f"# {talk.get('title', 'Talk')}",
            "",
        ]

        if talk.get("event"):
            body.append(f"**Event:** {talk['event']}")
        if talk.get("date"):
            body.append(f"**Date:** {talk['date']}")
        if talk.get("event_url") and talk["event_url"] != "TODO":
            body.extend(["", f"[Event page]({talk['event_url']})"])
        summary = collection_summary_text(talk, context, "talks")
        if summary:
            body.extend(["", "## Summary", "", summary])
        if talk.get("video_url"):
            body.extend(["", f"[Video]({talk['video_url']})"])
        if talk.get("slides_url"):
            body.extend(["", f"[Slides]({talk['slides_url']})"])

        source.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
        run(
            [
                "pandoc",
                str(source.relative_to(ROOT)),
                "--standalone",
                "--template",
                "templates/page.html",
                "--wrap=none",
                "--output",
                str(output.relative_to(ROOT)),
            ]
        )


def build_organizing_pages(context):
    community = read_yaml_subset(COMMUNITY_PATH)
    organizing = community.get("organizing", [])
    for path in ORGANIZING_DIR.glob("*.html"):
        path.unlink(missing_ok=True)

    for item in organizing:
        if not isinstance(item, dict):
            continue

        item_key = collection_slug(item)
        source = BUILD_DIR / "organizing" / f"{item_key}.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        output = ORGANIZING_DIR / f"{item_key}.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        body = [
            "---",
            f'title: "{item.get("title", "Organizing")}"',
            f'description: "{item.get("title", "Organizing")}"',
            'favicon: "../favicon.ico"',
            "stylesheet: ../assets/css/site.css",
            "body_class: page",
            "---",
            "",
            site_nav("../"),
            "",
            f"# {item.get('title', 'Organizing')}",
            "",
        ]

        if item.get("event"):
            body.append(f"**Event:** {item['event']}")
        if item.get("date"):
            body.append(f"**Date:** {item['date']}")
        if item.get("event_url") and item["event_url"] != "TODO":
            body.extend(["", f"[Event page]({item['event_url']})"])
        summary = collection_summary_text(item, context, "organizing")
        if summary:
            body.extend(["", "## Summary", "", summary])

        source.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
        run(
            [
                "pandoc",
                str(source.relative_to(ROOT)),
                "--standalone",
                "--template",
                "templates/page.html",
                "--wrap=none",
                "--output",
                str(output.relative_to(ROOT)),
            ]
        )
