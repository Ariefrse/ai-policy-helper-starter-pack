import os, re, hashlib
from typing import List, Dict, Tuple
from .settings import settings

def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _md_sections(text: str) -> List[Tuple[str, str]]:
    # Very simple section splitter by Markdown headings
    parts = re.split(r"\n(?=#+\s)", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        lines = p.splitlines()
        title = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("#") else "Body"
        out.append((title, p))
    return out or [("Body", text)]

def _sentences(s: str) -> List[str]:
    # naive sentence splitter that keeps headings and paragraphs intact
    # split on blank lines first, then within paragraphs by punctuation
    paras = re.split(r"\n{2,}", s.strip())
    out: List[str] = []
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if p.startswith("#"):  # keep headings as their own sentence
            out.append(p)
            continue
        # split by sentence enders but keep delimiter
        parts = re.split(r"(?<=[\.!?])\s+", p)
        out.extend([x for x in parts if x])
    return out

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    # sentence-aware packing up to ~chunk_size tokens, overlapping tail tokens
    sents = _sentences(text)
    chunks: List[str] = []
    cur: List[str] = []
    cur_tokens = 0
    for s in sents:
        ts = s.split()
        tlen = len(ts)
        if cur_tokens + tlen > chunk_size and cur:
            chunks.append(" ".join(cur))
            # build overlap tail
            if overlap > 0:
                tail = (" ".join(cur)).split()[-overlap:]
                cur = [" ".join(tail)] if tail else []
                cur_tokens = len(tail)
            else:
                cur, cur_tokens = [], 0
        cur.append(s)
        cur_tokens += tlen
    if cur:
        chunks.append(" ".join(cur))
    return chunks

def load_documents(data_dir: str) -> List[Dict]:
    docs = []
    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith((".md", ".txt")):
            continue
        path = os.path.join(data_dir, fname)
        text = _read_text_file(path)
        for section, body in _md_sections(text):
            docs.append({
                "title": fname,
                "section": section,
                "text": body
            })
    return docs

def doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
