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
        # For 2-term queries (like 'thejas aadhar' or 'final draft'), match if at least 1 term matches (coverage >= 0.50)
        is_hit = matched_count >= 1 and coverage >= 0.50
    else:
        # 3 or more terms: require at least 40% coverage (e.g. 1 out of 3 with prefix/token match, 2 out of 4)
        is_hit = coverage >= 0.40

    return is_hit, coverage


# Regex Patterns for Natural Language Entity Extraction
PROVIDER_PATTERNS = [
    (re.compile(r"\b(?:in|on|from|across|inside)?\s*(?:my\s*)?google[\s_-]?drive\b", re.IGNORECASE), "google_drive"),
    (re.compile(r"\b(?:in|on|from|across|inside)?\s*(?:my\s*)?gdrive\b", re.IGNORECASE), "google_drive"),
    (re.compile(r"\b(?:in|on|from|across|inside)?\s*(?:my\s*)?one[\s_-]?drive\b", re.IGNORECASE), "onedrive"),
    (re.compile(r"\b(?:in|on|from|across|inside)?\s*(?:my\s*)?dropbox\b", re.IGNORECASE), "dropbox"),
    (re.compile(r"\b(?:in|on|from|across|inside)?\s*(?:my\s*)?(?:[c-zC-Z]\s*(?:drive|disk|storage)|[c-zC-Z]:[\\\/]?)\b", re.IGNORECASE), "local"),
    (re.compile(r"\b(?:in|on|from|across|inside)?\s*(?:my\s*)?(?:local[\s_-]?(?:drive|disk|storage)?|this drive|pc|system|local|hard[\s_-]?drive)\b", re.IGNORECASE), "local"),
]

FOLDER_PATTERNS = [
    re.compile(r"\b(?:in|inside|under|from)\s+(?:the\s+)?(?:folder|directory|path|subfolder)\s+['\"]?([a-zA-Z0-9_\-\.\/\\:]+)['\"]?", re.IGNORECASE),
    re.compile(r"\b(?:folder|directory|path):\s*['\"]?([a-zA-Z0-9_\-\.\/\\:]+)['\"]?", re.IGNORECASE),
    re.compile(r"\b(?:in|inside|under|from)\s+(?:the\s+)?(downloads|documents|desktop|pictures|videos|music)(?:\s*(?:folder|directory))?\b", re.IGNORECASE),
    re.compile(r"\b(?:in|inside|under|from|on)\s+([c-zC-Z]:[\\\/]?|[c-zC-Z]\s*(?:drive|disk))\b", re.IGNORECASE),
    re.compile(r"\b(downloads|documents|desktop)\b", re.IGNORECASE),
]

FILE_TYPE_PATTERNS = [
    (re.compile(r"\b(?:pdf|pdfs|acrobat)\b", re.IGNORECASE), "pdf"),
    (re.compile(r"\b(?:word|docx?|document|documents)\b", re.IGNORECASE), "docx"),
    (re.compile(r"\b(?:excel|spreadsheets?|xlsx?|sheets?)\b", re.IGNORECASE), "xlsx"),
    (re.compile(r"\bcsv\b", re.IGNORECASE), "csv"),
    (re.compile(r"\b(?:images?|photos?|pictures?|png|jpg|jpeg)\b", re.IGNORECASE), "image"),
    (re.compile(r"\b(?:python|scripts?|py|code)\b", re.IGNORECASE), "py"),
]


def parse_natural_language_query(query: str) -> dict:
    """
    Parses conversational queries to isolate target files, storage locations, folders, and extensions.
    Example: 'search for fees in google drive under folder 2026'
    -> clean_target: 'fees', provider: 'google_drive', folder: '2026'
    """
    if not query:
        return {
            "raw_query": "",
            "clean_target": "*",
            "provider": None,
            "folder": None,
            "file_type": None,
            "terms": [],
        }

    q_work = query
    detected_provider = None
    detected_folder = None
    detected_type = None

    # Clean out conversational preamble phrases like "there are", "i feel like", "can you find"
    conv_paterns = [
        re.compile(r"\b(?:there\s+are|there\s+is|i\s+have|i\s+feel\s+like|can\s+you\s+find|please\s+find|search\s+for|look\s+for|find|show\s+me|get|list|display)\b", re.IGNORECASE),
        re.compile(r"\b(?:is\s+being\s+searched|are\s+being\s+searched|not\s+working|working)\b", re.IGNORECASE),
    ]
    for cp in conv_paterns:
        q_work = cp.sub(" ", q_work)

    # 1. Detect target storage provider
    for pat, p_id in PROVIDER_PATTERNS:
        match = pat.search(q_work)
        if match:
            detected_provider = p_id
            q_work = pat.sub(" ", q_work)
            break

    # 2. Detect location folder/path
    for pat in FOLDER_PATTERNS:
        match = pat.search(q_work)
        if match:
            detected_folder = match.group(1).strip()
            q_work = pat.sub(" ", q_work)
            if not detected_provider and any(k in detected_folder.lower() for k in ["download", "document", "desktop", "c:", "d:", "c drive", "d drive"]):
                detected_provider = "local"
            break

    # 3. Detect file type
    for pat, ext in FILE_TYPE_PATTERNS:
        match = pat.search(q_work)
        if match:
            detected_type = ext
            break

    # 4. Clean keywords without carrier verbs or provider tokens
    terms = extract_terms(q_work, keep_recency=False)
    provider_words = {"google", "drive", "gdrive", "onedrive", "dropbox", "local", "disk", "pc", "folder", "directory", "c", "d", "e", "downloads", "documents", "desktop"}
    final_terms = [t for t in terms if t.lower() not in provider_words]
    clean_target = " ".join(final_terms) if final_terms else clean_query_text(q_work)

    return {
        "raw_query": query,
        "clean_target": clean_target.strip() or "*",
        "provider": detected_provider,
        "folder": detected_folder,
        "file_type": detected_type,
        "terms": final_terms,
    }

