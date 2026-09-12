from __future__ import annotations
"""Load CSV, TSV, or JSONL files into a list of dicts with column names."""
import csv
import json
import os


def load_file(path: str) -> tuple[list[dict], list[str]]:
    """
    Returns (rows, columns).
    rows: list of dicts — each dict is one record
    columns: ordered list of column names
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".jsonl":
        return _load_jsonl(path)
    return _load_csv(path, ext)


def _load_csv(path: str, ext: str) -> tuple[list[dict], list[str]]:
    delimiter = "\t" if ext == ".tsv" else _detect_delimiter(path)
    rows = []
    columns = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        columns = list(reader.fieldnames or [])
        for row in reader:
            rows.append(dict(row))
    return rows, columns


def _load_jsonl(path: str) -> tuple[list[dict], list[str]]:
    rows = []
    columns_seen: dict[str, int] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append(obj)
            for k in obj:
                if k not in columns_seen:
                    columns_seen[k] = len(columns_seen)
    columns = sorted(columns_seen, key=lambda k: columns_seen[k])
    return rows, columns


def _detect_delimiter(path: str) -> str:
    """Sniff delimiter from first 4KB of file."""
    with open(path, encoding="utf-8-sig") as f:
        sample = f.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def sample_rows(rows: list[dict], n: int = 5) -> list[dict]:
    """Return first n rows as sample for preview."""
    return rows[:n]


def get_column_stats(rows: list[dict], columns: list[str]) -> dict[str, dict]:
    """
    Compute per-column stats:
      - avg_len: average string length (for text columns)
      - unique_ratio: unique values / total rows (for categorical detection)
    """
    stats = {}
    n = len(rows)
    if n == 0:
        return stats
    for col in columns:
        values = [str(row.get(col, "") or "") for row in rows]
        avg_len = sum(len(v) for v in values) / n
        unique_ratio = len(set(values)) / n
        stats[col] = {"avg_len": round(avg_len, 1), "unique_ratio": round(unique_ratio, 3)}
    return stats
