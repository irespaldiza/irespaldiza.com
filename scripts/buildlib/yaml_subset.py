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
