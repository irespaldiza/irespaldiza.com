#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
PUBLIC_DIR = ROOT / "site"

PROFILE_PATH = ROOT / "content/data/profile.yml"
PRIVATE_PROFILE_PATH = ROOT / "private/profile.yml"
SKILLS_PATH = ROOT / "content/data/skills.yml"
EXPERIENCE_PATH = ROOT / "content/data/experience.yml"
COMMUNITY_PATH = ROOT / "content/data/community.yml"
PUBLICATIONS_PATH = ROOT / "content/data/publications.yml"
TRAINING_PATH = ROOT / "content/data/training.yml"
INDEX_SOURCE = ROOT / "content/pages/index.md"
RESUME_SOURCE = ROOT / "content/pages/resume.md"
COMMUNITY_SOURCE = ROOT / "content/pages/community.md"

RENDERED_INDEX = BUILD_DIR / "index.md"
RENDERED_RESUME = BUILD_DIR / "resume.md"
RENDERED_COMMUNITY = BUILD_DIR / "community.md"
PUBLIC_RESUME = BUILD_DIR / "resume.public.md"
PRIVATE_RESUME = BUILD_DIR / "resume.private.md"
PRIVATE_RESUME_HTML = BUILD_DIR / "resume.private.html"

INDEX_HTML = PUBLIC_DIR / "index.html"
COMMUNITY_HTML = PUBLIC_DIR / "community.html"
RESUME_HTML = PUBLIC_DIR / "resume.html"
RESUME_PDF = PUBLIC_DIR / "outputs/pdf/resume.pdf"
TALKS_DIR = PUBLIC_DIR / "talks"
ORGANIZING_DIR = PUBLIC_DIR / "organizing"
ASSETS_DIR = PUBLIC_DIR / "assets"
PUBLIC_FAVICON = PUBLIC_DIR / "favicon.ico"
PUBLIC_CNAME = PUBLIC_DIR / "CNAME"
PUBLIC_NOJEKYLL = PUBLIC_DIR / ".nojekyll"


def read_simple_yaml(path):
    data = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def parse_scalar(value):
    value = value.strip()
    if value in ("[]", ""):
        return [] if value == "[]" else ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def is_quoted(value):
    value = value.strip()
    return (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    )


def read_yaml_subset(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    data = {}
    current_key = None
    current_map_key = None
    current_item = None
    dict_list_keys = {"roles", "talks", "organizing"}
    string_list_keys = {"items", "focus"}

    for raw_line in lines:
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0 and line.endswith(":"):
            current_key = line[:-1]
            data[current_key] = (
                []
                if current_key in dict_list_keys | string_list_keys
                else {}
            )
            current_map_key = None
            current_item = None
            continue

        if indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            data[key] = parse_scalar(value)
            current_key = key
            current_map_key = None
            current_item = None
            continue

        if current_key is None:
            continue

        container = data[current_key]

        if isinstance(container, dict):
            if indent == 2 and line.endswith(":"):
                current_map_key = line[:-1]
                container[current_map_key] = []
                continue
            if indent == 2 and ":" in line:
                key, value = line.split(":", 1)
                container[key] = parse_scalar(value)
                current_map_key = key
                continue
            if indent == 4 and line.startswith("- ") and current_map_key:
                container[current_map_key].append(parse_scalar(line[2:]))
                continue

        if isinstance(container, list):
            if indent == 2 and line.startswith("- "):
                body = line[2:]
                if (
                    current_key in dict_list_keys
                    and ":" in body
                    and not is_quoted(body)
                ):
                    key, value = body.split(":", 1)
                    current_item = {key: parse_scalar(value)}
                    container.append(current_item)
                else:
                    current_item = None
                    container.append(parse_scalar(body))
                continue
            if indent == 4 and current_item is not None and line.endswith(":"):
                key = line[:-1]
                current_item[key] = []
                current_map_key = key
                continue
            if indent == 4 and current_item is not None and ":" in line:
                key, value = line.split(":", 1)
                current_item[key] = parse_scalar(value)
                current_map_key = key if isinstance(current_item[key], list) else None
                continue
            if (
                indent == 6
                and current_item is not None
                and line.startswith("- ")
                and current_map_key
            ):
                current_item[current_map_key].append(parse_scalar(line[2:]))
                continue

    return data


def markdown_key_values(mapping):
    return "\n\n".join(f"**{key}:** {value}" for key, value in mapping.items())


def markdown_grouped_lists(mapping):
    return "\n\n".join(
        f"**{key}:** {', '.join(values)}." for key, values in mapping.items()
    )


def markdown_list(items):
    return "\n".join(f"- {item}" for item in items)


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


def site_nav(prefix=""):
    return (
        "::: {.site-nav}\n"
        f"[Home]({prefix}index.html) "
        f"[Resume]({prefix}resume.html) "
        f"[PDF]({prefix}outputs/pdf/resume.pdf) "
        f"[Community]({prefix}community.html)\n"
        ":::"
    )


def prepare_public_site():
    shutil.rmtree(PUBLIC_DIR, ignore_errors=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", ASSETS_DIR, dirs_exist_ok=True)
    shutil.copy2(ROOT / "favicon.ico", PUBLIC_FAVICON)
    if (ROOT / "CNAME").exists():
        shutil.copy2(ROOT / "CNAME", PUBLIC_CNAME)
    PUBLIC_NOJEKYLL.write_text("", encoding="utf-8")


def markdown_experience(roles):
    blocks = []
    for role in roles:
        block = [
            f"### {role['organization']}",
            "",
            f"**{role['title']}**  ",
        ]

        location = role.get("location", "")
        dates = role.get("dates", "")
        if location and location != "TODO":
            block.append(f"{dates} | {location}")
        elif dates:
            block.append(dates)

        block.extend(["", role.get("description", "")])

        if role.get("extra_description"):
            block.extend(["", role["extra_description"]])

        responsibilities = role.get("responsibilities") or []
        if responsibilities:
            block.extend(["", "**Key responsibilities**", ""])
            block.extend(f"- {item}" for item in responsibilities)

        achievements = role.get("achievements") or []
        if achievements:
            block.extend(["", "**Selected achievements**", ""])
            block.extend(f"- {item}" for item in achievements)

        blocks.append("\n".join(block).rstrip())

    return "\n\n".join(blocks)


def contact_link(label, value):
    value = str(value).strip()
    display_labels = {
        "email": "Email",
        "github": "GitHub",
        "linkedin": "LinkedIn",
        "website": "Website",
    }
    display_label = display_labels.get(label, label.title())
    if label == "email":
        return f"[{display_label}](mailto:{value})"

    href = value if re.match(r"^https?://", value) else f"https://{value}"
    return f"[{display_label}]({href})"


def build_context(include_private=False):
    profile = read_yaml_subset(PROFILE_PATH)
    skills = read_yaml_subset(SKILLS_PATH)
    experience = read_yaml_subset(EXPERIENCE_PATH)
    community = read_yaml_subset(COMMUNITY_PATH)
    publications = read_yaml_subset(PUBLICATIONS_PATH)
    training = read_yaml_subset(TRAINING_PATH)

    contact_parts = []
    public_contact = profile.get("public_contact", {})
    for label, value in public_contact.items():
        if value and value != "TODO":
            contact_parts.append(contact_link(label, value))

    if include_private and PRIVATE_PROFILE_PATH.exists():
        private_profile = read_yaml_subset(PRIVATE_PROFILE_PATH)
        email = private_profile.get("email")
        if email and email != "TODO":
            contact_parts.append(contact_link("email", email))

    profile["contact_line"] = " | ".join(contact_parts)

    return {
        "profile": profile,
        "site": {
            "nav": site_nav(),
        },
        "skills": {
            "competencies": markdown_key_values(skills["competencies"]),
            "technologies": markdown_grouped_lists(skills["technologies"]),
            "focus": markdown_list(skills["focus"]),
            "focus_line": " | ".join(skills["focus"]),
            "languages": "\n\n".join(
                f"{language}: {level}."
                for language, level in skills["languages"].items()
            ),
        },
        "community": {
            "summary": (
                render_markdown(
                    Path(community["summary_md"]).read_text(encoding="utf-8"),
                    {"profile": profile, "skills": {}},
                ).strip()
                if community.get("summary_md")
                else ""
            ),
            "talks": markdown_collection_index(community.get("talks", []), "talks"),
            "organizing": markdown_collection_index(
                community.get("organizing", []),
                "organizing",
            ),
            "page": "\n\n".join(
                part
                for part in [
                    (
                        render_markdown(
                            Path(community["summary_md"]).read_text(encoding="utf-8"),
                            {"profile": profile, "skills": {}},
                        ).strip()
                        if community.get("summary_md")
                        else ""
                    ),
                    (
                        "### Organizing\n\n"
                        + markdown_organizing_list(community.get("organizing", []))
                        if community.get("organizing")
                        else ""
                    ),
                    (
                        "### Talks\n\n"
                        + markdown_collection_index(community.get("talks", []), "talks")
                        if community.get("talks")
                        else ""
                    ),
                ]
                if part
            ),
        },
        "resume": {
            "experience": markdown_experience(experience["roles"]),
            "community": "\n\n".join(
                part
                for part in [
                    (
                        render_markdown(
                            Path(community["summary_md"]).read_text(encoding="utf-8"),
                            {"profile": profile, "skills": {}},
                        ).strip()
                        if community.get("summary_md")
                        else ""
                    ),
                    (
                        "### Organizing\n\n"
                        + markdown_organizing_list(community.get("organizing", []))
                        if community.get("organizing")
                        else ""
                    ),
                ]
                if part
            ),
            "publications": markdown_list(publications["items"]),
            "training": markdown_list(training["items"]),
            "tagline": " | ".join(skills["focus"]),
        },
    }


def resolve_context(context, namespace, key, fallback):
    value = context.get(namespace, {}).get(key)
    return value if value is not None else fallback


def render_markdown(text, context):
    include_pattern = re.compile(r"^\{\{>\s*([^}]+?)\s*\}\}\s*$", re.MULTILINE)
    variable_pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\s*\}\}")

    def include(match):
        include_path = ROOT / match.group(1).strip()
        return render_markdown(
            include_path.read_text(encoding="utf-8"), context
        ).rstrip()

    def variable(match):
        namespace = match.group(1)
        key = match.group(2)
        return resolve_context(context, namespace, key, match.group(0))

    text = include_pattern.sub(include, text)
    return variable_pattern.sub(variable, text)


def render_source(source, output, context):
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_markdown(source.read_text(encoding="utf-8"), context)
    output.write_text(rendered, encoding="utf-8")


def page_context(context, prefix):
    page = dict(context)
    site = dict(context.get("site", {}))
    site["nav"] = site_nav(prefix)
    page["site"] = site
    return page


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


def keep_public_line(line):
    if "TODO" in line:
        return False
    if line == "**Selected achievements**":
        return False
    return True


def section_has_public_content(lines):
    for line in lines:
        if not line:
            continue
        if line.startswith("## ") or line.startswith("### "):
            continue
        if line == "**Selected achievements**":
            continue
        return True
    return False


def flush_block(output, block):
    if block and section_has_public_content(block):
        output.extend(block)
        output.append("")


def remove_empty_blocks(lines, heading_prefix):
    output = []
    current = []

    for line in lines:
        if line.startswith(heading_prefix) and current:
            flush_block(output, current)
            current = []
        current.append(line)

    flush_block(output, current)
    return output


def public_resume(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    public_lines = []

    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line

        if line.startswith("Seville, Spain |"):
            line = "Seville, Spain"

        line = re.sub(r"\s*\| TODO.*", "", line)

        if keep_public_line(line):
            public_lines.append(line)

    public_lines = remove_empty_blocks(public_lines, "### ")
    public_lines = remove_empty_blocks(public_lines, "## ")

    output.write_text("\n".join(public_lines).rstrip() + "\n", encoding="utf-8")


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def pandoc_attr(block):
    if block.get("t") == "Header":
        return block["c"][1]
    if block.get("t") == "Div":
        return block["c"][0]
    return None


def add_pandoc_class(block, class_name):
    attr = pandoc_attr(block)
    if attr is not None and class_name not in attr[1]:
        attr[1].append(class_name)


def pandoc_div(blocks, element_id="", classes=None):
    return {
        "t": "Div",
        "c": [[element_id, classes or [], []], blocks],
    }


def wrap_experience_entries(blocks):
    output = []
    entry = None

    for block in blocks:
        if block.get("t") == "Header" and block["c"][0] == 3:
            if entry:
                output.append(pandoc_div(entry, classes=["experience-entry"]))
            add_pandoc_class(block, "experience-organization")
            entry = [block]
        elif entry is not None:
            entry.append(block)
        else:
            output.append(block)

    if entry:
        output.append(pandoc_div(entry, classes=["experience-entry"]))

    return output


def structure_resume_ast(document):
    source = document["blocks"]
    output = []
    index = 0

    while index < len(source):
        block = source[index]

        if block.get("t") == "Header" and block["c"][0] == 1:
            add_pandoc_class(block, "resume-name")
            header = [block]
            index += 1
            detail_index = 0

            while index < len(source):
                detail = source[index]
                if detail.get("t") == "Header" and detail["c"][0] == 2:
                    break
                if detail.get("t") == "Para" and detail_index == 0:
                    header.append(pandoc_div([detail], classes=["resume-title"]))
                    detail_index += 1
                elif detail.get("t") == "Para" and detail_index == 1:
                    header.append(pandoc_div([detail], classes=["contact-links"]))
                    detail_index += 1
                else:
                    header.append(detail)
                index += 1

            output.append(pandoc_div(header, classes=["resume-header"]))
            continue

        if block.get("t") == "Header" and block["c"][0] == 2:
            section_id = block["c"][1][0]
            add_pandoc_class(block, "resume-section-heading")
            section = [block]
            index += 1

            while index < len(source):
                child = source[index]
                if child.get("t") == "Header" and child["c"][0] == 2:
                    break
                section.append(child)
                index += 1

            if section_id == "professional-experience":
                section = wrap_experience_entries(section)

            output.append(
                pandoc_div(
                    section,
                    element_id=section_id,
                    classes=["resume-section", f"resume-section-{section_id}"],
                )
            )
            continue

        output.append(block)
        index += 1

    document["blocks"] = output
    return document


def build_resume_html(source, output, css):
    ast_path = BUILD_DIR / f"{output.stem}.ast.json"
    run(
        [
            "pandoc",
            str(source.relative_to(ROOT)),
            "--to=json",
            "--output",
            str(ast_path.relative_to(ROOT)),
        ]
    )
    document = json.loads(ast_path.read_text(encoding="utf-8"))
    structured = structure_resume_ast(document)
    ast_path.write_text(json.dumps(structured), encoding="utf-8")
    run(
        [
            "pandoc",
            str(ast_path.relative_to(ROOT)),
            "--from=json",
            "--standalone",
            "--template",
            "templates/resume.html",
            "--css",
            css,
            "--wrap=none",
            "--output",
            str(output.relative_to(ROOT)),
        ]
    )


def find_chrome():
    configured = os.environ.get("CHROME")
    if configured:
        return configured

    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac_chrome.exists():
        return str(mac_chrome)

    for candidate in ("google-chrome", "chromium"):
        path = shutil.which(candidate)
        if path:
            return path

    raise RuntimeError("Chrome or Chromium is required to generate PDFs from HTML.")


def html_to_pdf(input_html, output_pdf):
    chrome = find_chrome()
    input_path = input_html.resolve()
    output_path = output_pdf.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_pdf = output_path.with_name(f"{output_path.name}.tmp.{os.getpid()}")

    if tmp_pdf.exists():
        tmp_pdf.unlink()

    with tempfile.TemporaryDirectory(prefix="resume-chrome.") as profile_dir:
        chrome_args = shlex.split(os.environ.get("CHROME_EXTRA_ARGS", ""))
        chrome_stderr = Path(profile_dir) / "chrome-stderr.log"
        with chrome_stderr.open("wb") as stderr_handle:
            process = subprocess.Popen(
                [
                    chrome,
                    "--headless",
                    "--disable-gpu",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-sync",
                    "--disable-translate",
                    "--metrics-recording-only",
                    "--no-default-browser-check",
                    "--no-first-run",
                    f"--user-data-dir={profile_dir}",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={tmp_pdf}",
                    *chrome_args,
                    f"file://{input_path}",
                ],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=stderr_handle,
            )

            for _ in range(180):
                if tmp_pdf.exists() and tmp_pdf.stat().st_size > 0:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                    tmp_pdf.replace(output_path)
                    return

                if process.poll() is not None:
                    break

                time.sleep(1)

            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

        stderr_output = chrome_stderr.read_text(encoding="utf-8", errors="replace").strip()

    if stderr_output:
        tail = "\n".join(stderr_output.splitlines()[-10:])
        raise RuntimeError(
            f"Failed to generate PDF: {output_path}\n"
            f"Chrome stderr:\n{tail}"
        )

    raise RuntimeError(f"Failed to generate PDF: {output_path}")


def build_site():
    context = build_context()

    prepare_public_site()

    render_source(INDEX_SOURCE, RENDERED_INDEX, page_context(context, ""))
    render_source(RESUME_SOURCE, RENDERED_RESUME, page_context(context, ""))
    render_source(COMMUNITY_SOURCE, RENDERED_COMMUNITY, page_context(context, ""))
    public_resume(RENDERED_RESUME, PUBLIC_RESUME)
    build_talk_pages(context)
    build_organizing_pages(context)

    run(
        [
            "pandoc",
            str(RENDERED_INDEX.relative_to(ROOT)),
            "--standalone",
            "--template",
            "templates/page.html",
            "--wrap=none",
            "--output",
            str(INDEX_HTML.relative_to(ROOT)),
        ]
    )

    run(
        [
            "pandoc",
            str(RENDERED_COMMUNITY.relative_to(ROOT)),
            "--standalone",
            "--template",
            "templates/page.html",
            "--wrap=none",
            "--output",
            str(COMMUNITY_HTML.relative_to(ROOT)),
        ]
    )

    build_resume_html(PUBLIC_RESUME, RESUME_HTML, "assets/css/resume.css")


def build_pdf():
    build_site()
    private_context = build_context(include_private=True)
    render_source(
        RESUME_SOURCE,
        RENDERED_RESUME,
        page_context(private_context, ""),
    )
    public_resume(RENDERED_RESUME, PRIVATE_RESUME)
    build_resume_html(
        PRIVATE_RESUME,
        PRIVATE_RESUME_HTML,
        "../assets/css/resume.css",
    )
    html_to_pdf(PRIVATE_RESUME_HTML, RESUME_PDF)


def clean():
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.rmtree(PUBLIC_DIR, ignore_errors=True)
    shutil.rmtree(TALKS_DIR, ignore_errors=True)
    shutil.rmtree(ORGANIZING_DIR, ignore_errors=True)
    for path in (ROOT / "index.html", ROOT / "resume.html", ROOT / "community.html"):
        path.unlink(missing_ok=True)
    for path in ROOT.glob("talks/*.html"):
        path.unlink(missing_ok=True)
    for path in ROOT.glob("organizing/*.html"):
        path.unlink(missing_ok=True)
    (ROOT / "outputs/pdf/resume.pdf").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["site", "pdf", "all", "clean"])
    args = parser.parse_args()

    if args.target == "site":
        build_site()
        print("Built site")
    elif args.target == "pdf":
        build_pdf()
        print("Built site and PDF")
    elif args.target == "all":
        build_pdf()
        print("Built site and PDF")
    elif args.target == "clean":
        clean()
        print("Cleaned generated files")


if __name__ == "__main__":
    main()
