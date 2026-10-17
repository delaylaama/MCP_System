"""
NLP Query Parser & Intent Cleaner.
Strips conversational filler phrases, carrier verbs, and stopwords to extract
the true semantic subject and keywords from natural language queries.
"""

import re
from typing import List, Set, Tuple

# Conversational carrier words, filler pronouns, articles, and generic search verbs
STOPWORDS: Set[str] = {
    "find", "search", "show", "get", "fetch", "display", "give", "list", "see",
    "look", "locate", "seek", "browse", "bring", "pull", "open", "view",
    "my", "me", "mine", "i", "we", "our", "ours", "us", "you", "your", "yours",
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "for", "from",
    "with", "by", "about", "into", "through", "over", "between",
    "please", "can", "could", "would", "will", "should", "want", "need", "like",
    "file", "files", "document", "documents", "doc", "docs", "item", "items",
    "stuff", "data", "folder", "directory", "record", "records",
    "all", "any", "some", "every", "each", "both",
    "related", "concerning", "regarding", "having", "containing",
    "where", "is", "are", "was", "were", "been", "being", "have", "has", "had",
    "do", "does", "did", "tell", "what", "which", "who", "whom", "whose",
}

# Time/recency intent keywords (used to detect sort/temporal filtering)
RECENCY_KEYWORDS: Set[str] = {
    "latest", "recent", "newest", "last", "current", "fresh", "updated", "new", "recently"
}


def extract_terms(query: str, keep_recency: bool = False) -> List[str]:
    """
    Extracts meaningful, non-stopword tokens from a raw natural-language query.
    Handles camelCase (e.g. finalDraft -> ['final', 'draft']), underscores, and hyphens.
    """
    if not query:
        return []
    # Expand camelCase boundaries: 'finalDraft' -> 'final Draft', 'DreamFolks' -> 'Dream Folks'
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", query)
    clean = re.sub(r"[_\-\s\.,;:\?!'\"/\\()\[\]]+", " ", expanded.lower()).strip()
    words = clean.split()
    
    meaningful = []
    for w in words:
        if len(w) <= 1:
            continue
        if w in STOPWORDS:
            continue
        if not keep_recency and w in RECENCY_KEYWORDS:
            continue
        meaningful.append(w)
    return meaningful


def clean_query_text(query: str) -> str:
    """
    Returns the distilled semantic subject of a query.
    Example: 'find my final year fees' -> 'final year fees'
    """
    terms = extract_terms(query, keep_recency=True)
    return " ".join(terms) if terms else query.strip()


def is_recency_query(query: str) -> bool:
    """Detects if query asks for latest/recent files."""
    q_lower = query.lower()
    return any(re.search(rf"\b{w}\b", q_lower) for w in RECENCY_KEYWORDS)


def compute_term_match(terms: List[str], text: str) -> Tuple[bool, float]:
    """
    Evaluates whether a text (filename, path, or content) matches the query terms.
    Returns: (is_match: bool, coverage_ratio: float)
    """
    if not terms:
        return False, 0.0

    text_lower = text.lower()
    full_phrase = " ".join(terms)

    # 1. Compact alphanumeric match for camelCase, concatenated words, etc. (e.g. finalDraft vs finaldraft)
    q_compact = re.sub(r"[^a-z0-9]", "", full_phrase)
    t_compact = re.sub(r"[^a-z0-9]", "", text_lower)
    if q_compact and (q_compact in t_compact):
        return True, 1.0

    # 2. Exact phrase match gets instant 100%
    text_normalized = re.sub(r"[_\-\s]+", " ", text_lower)
    if full_phrase in text_normalized:
        return True, 1.0

    # 3. Count term matches across tokens split by underscores, hyphens, dots, whitespace
    text_words = set(w for w in re.split(r"[_\-\s\.,;:\(\)\[\]/\\!]+", text_lower) if w)
    matched_count = 0
    for t in terms:
        # Exact word match or valid prefix match (minimum 3 chars to prevent single letter matches like 'd' matching 'draft')
        if t in text_words:
            matched_count += 1
        elif any(len(t) >= 3 and w.startswith(t) for w in text_words):
            matched_count += 1
        elif any(len(w) >= 4 and t.startswith(w) for w in text_words):
            matched_count += 1

    coverage = matched_count / len(terms)

    if len(terms) == 1:
        is_hit = matched_count >= 1
    elif len(terms) == 2:
        # For 2-term queries (like 'final draft'), require both terms or exact phrase
        is_hit = matched_count >= 2
    else:
        # 3 or more terms: require at least 66% coverage (e.g. 2 out of 3, 3 out of 4)
        is_hit = coverage >= 0.60

    return is_hit, coverage
