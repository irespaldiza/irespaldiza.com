import re
from pathlib import Path

from .collections import markdown_collection_index, markdown_organizing_list
from .markdown import (
    markdown_grouped_lists,
    markdown_key_values,
    markdown_list,
    render_markdown,
)
from .paths import (
    COMMUNITY_PATH,
    EXPERIENCE_PATH,
    PRIVATE_PROFILE_PATH,
    PROFILE_PATH,
    PUBLICATIONS_PATH,
    SKILLS_PATH,
    TRAINING_PATH,
)
from .site import site_nav
from .yaml_subset import read_yaml_subset


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


def render_community_summary(community, profile):
    if not community.get("summary_md"):
        return ""

    return render_markdown(
        Path(community["summary_md"]).read_text(encoding="utf-8"),
        {"profile": profile, "skills": {}},
    ).strip()


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
    community_summary = render_community_summary(community, profile)

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
                f"**{language}:** {level}."
                for language, level in skills["languages"].items()
            ),
        },
        "community": {
            "summary": community_summary,
            "talks": markdown_collection_index(community.get("talks", []), "talks"),
            "organizing": markdown_collection_index(
                community.get("organizing", []),
                "organizing",
            ),
            "page": "\n\n".join(
                part
                for part in [
                    community_summary,
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
                    community_summary,
                    markdown_organizing_list(community.get("organizing", []))
                    if community.get("organizing")
                    else "",
                ]
                if part
            ),
            "publications": markdown_list(publications["items"]),
            "training": markdown_list(training["items"]),
            "tagline": " | ".join(skills["focus"]),
        },
    }
