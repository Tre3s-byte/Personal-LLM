"""Message-history normalization utilities for model-compatible payloads."""

def coerce_content_to_text(content):
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, (int, float, bool)):
        return str(content)

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                parts.append(coerce_content_to_text(text))
            else:
                parts.append(str(item))

        return "\n".join(part for part in parts if part)

    if isinstance(content, dict):
        text = content.get("text") or content.get("content")
        return coerce_content_to_text(text)

    return str(content)


def normalize_history_for_model(history):
    if not history:
        return []

    normalized = []

    for item in history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            if item["role"] in {"user", "assistant", "system"}:
                normalized.append(
                    {
                        "role": item["role"],
                        "content": coerce_content_to_text(item["content"]),
                    }
                )
            continue

        if isinstance(item, (list, tuple)) and len(item) == 2:
            user_msg, assistant_msg = item

            if user_msg is not None:
                normalized.append(
                    {"role": "user", "content": coerce_content_to_text(user_msg)}
                )

            if assistant_msg is not None:
                normalized.append(
                    {
                        "role": "assistant",
                        "content": coerce_content_to_text(assistant_msg),
                    }
                )

    return normalized
