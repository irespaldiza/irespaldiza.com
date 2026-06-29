import re

from .paths import ROOT


def markdown_key_values(mapping):
    return "\n\n".join(f"**{key}:** {value}" for key, value in mapping.items())


def markdown_grouped_lists(mapping):
    return "\n\n".join(
        f"**{key}:** {', '.join(values)}." for key, values in mapping.items()
    )


def markdown_list(items):
    return "\n".join(f"- {item}" for item in items)


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
