import json
import re
from urllib.parse import urljoin

from .commands import run
from .paths import BUILD_DIR, ROOT


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


def decorate_document_links(node, base_url=None):
    if isinstance(node, dict):
        if node.get("t") == "Link":
            attr, _, target = node["c"]
            href = target[0]
            if base_url and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
                target[0] = urljoin(f"{base_url.rstrip('/')}/", href)
            attributes = attr[2]
            attributes[:] = [
                item
                for item in attributes
                if item[0] not in {"target", "rel"}
            ]
            attributes.extend(
                [
                    ["target", "_blank"],
                    ["rel", "noopener noreferrer"],
                ]
            )
        for value in node.values():
            decorate_document_links(value, base_url)
    elif isinstance(node, list):
        for value in node:
            decorate_document_links(value, base_url)


def wrap_experience_entries(blocks):
    output = []
    entry = None

    for block in blocks:
        if block.get("t") == "Header" and block["c"][0] == 3:
            if entry:
                output.append(pandoc_div(entry, classes=["experience-entry"]))
            add_pandoc_class(block, "experience-organization")
            add_experience_marker(block)
            entry = [block]
        elif entry is not None:
            entry.append(block)
        else:
            output.append(block)

    if entry:
        output.append(pandoc_div(entry, classes=["experience-entry"]))

    return output


def add_experience_marker(header):
    inlines = header["c"][2]
    if inlines and inlines[0].get("t") == "Span":
        classes = inlines[0]["c"][0][1]
        if "experience-marker" in classes:
            return

    inlines[:0] = [
        {
            "t": "Span",
            "c": [["", ["experience-marker"], []], [{"t": "Str", "c": ">"}]],
        },
        {"t": "Space"},
    ]


def structure_resume_ast(document, base_url=None):
    decorate_document_links(document, base_url)
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


def build_resume_html(source, output, css, base_url=None):
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
    structured = structure_resume_ast(document, base_url)
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
