import re


def compute_score(keyword: str, title: str, body: str) -> int:
    """
    Score a keyword match against a content item.
      100 — exact whole-word match in title
       70 — partial/substring match in title
       40 — keyword found only in body
        0 — no match (no flag should be created)
    """
    kw = keyword.lower().strip()
    title_lower = title.lower()
    body_lower = body.lower()

    in_title = kw in title_lower
    in_body = kw in body_lower

    if not in_title and not in_body:
        return 0

    if in_title:
        if _is_exact_word_match(kw, title_lower):
            return 100
        return 70

    return 40


def _is_exact_word_match(keyword: str, text: str) -> bool:
    pattern = r'(?<![a-z0-9])' + re.escape(keyword) + r'(?![a-z0-9])'
    return bool(re.search(pattern, text))