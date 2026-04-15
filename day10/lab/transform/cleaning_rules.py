"""
Cleaning rules — raw export → cleaned rows + quarantine.

Baseline gồm các failure mode mở rộng (allowlist doc_id, parse ngày, HR stale version).
Sinh viên thêm ≥3 rule mới: mỗi rule phải ghi `metric_impact` (xem README — chống trivial).
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Khớp export hợp lệ trong lab (mở rộng khi nhóm thêm doc mới — phải đồng bộ contract).
ALLOWED_DOC_IDS = frozenset(
    {
        "policy_refund_v4",
        "sla_p1_2026",
        "it_helpdesk_faq",
        "hr_leave_policy",
    }
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY_SLASH = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
_ISO_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
_SUSPICIOUS_KEYWORDS = frozenset({"[deprecated]", "[todo]", "[fixme]", "[redacted]"})


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_chunk_id(doc_id: str, chunk_text: str, seq: int) -> str:
    h = hashlib.sha256(f"{doc_id}|{chunk_text}|{seq}".encode("utf-8")).hexdigest()[:16]
    return f"{doc_id}_{seq}_{h}"


def _normalize_effective_date(raw: str) -> Tuple[str, str]:
    """
    Trả về (iso_date, error_reason).
    iso_date rỗng nếu không parse được.
    """
    s = (raw or "").strip()
    if not s:
        return "", "empty_effective_date"
    if _ISO_DATE.match(s):
        return s, ""
    m = _DMY_SLASH.match(s)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}", ""
    return "", "invalid_effective_date_format"


def _is_valid_exported_at(raw: str) -> bool:
    """
    RULE 1 (NEW): Validate exported_at format — must be ISO 8601 datetime.
    Quarantine if format looks wrong (anti-garbage ingestion).
    """
    s = (raw or "").strip()
    if not s:
        return False  # Empty exported_at không hợp lệ
    return bool(_ISO_DATETIME.match(s))


def _has_suspicious_keywords(text: str) -> bool:
    """
    RULE 2 (NEW): Check for suspicious markers like [deprecated], [todo], etc.
    These typically indicate unfinished or obsolete content.
    Quarantine if found (data quality).
    """
    lower = (text or "").lower()
    for keyword in _SUSPICIOUS_KEYWORDS:
        if keyword in lower:
            return True
    return False


def _normalize_chunk_text(text: str) -> str:
    """
    RULE 3 (NEW): Trim và normalize whitespace trong chunk_text.
    - Xóa leading/trailing spaces
    - Collapse multiple spaces thành 1
    - Fix line breaks thành space
    Tránh collision từ string whitespace khác biệt.
    """
    s = (text or "").strip()
    # Collapse multiple spaces/newlines thành 1 space
    s = " ".join(s.split())
    return s


def load_raw_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def clean_rows(
    rows: List[Dict[str, str]],
    *,
    apply_refund_window_fix: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Trả về (cleaned, quarantine).

    Baseline (mở rộng theo narrative Day 10):
    1) Quarantine: doc_id không thuộc allowlist (export lạ / catalog sai).
    2) Chuẩn hoá effective_date sang YYYY-MM-DD; quarantine nếu không parse được.
    3) Quarantine: chunk hr_leave_policy có effective_date < 2026-01-01 (bản HR cũ / conflict version).
    4) Quarantine: chunk_text rỗng hoặc effective_date rỗng sau chuẩn hoá.
    5) Loại trùng nội dung chunk_text (giữ bản đầu).
    6) Fix stale refund: policy_refund_v4 chứa '14 ngày làm việc' → 7 ngày.
    7) Rule mới (Nguyễn Bằng Anh): Chuẩn hóa thuật ngữ IT (wifi -> Wi-Fi, portal -> Portal).
    8) Rule mới (Nguyễn Bằng Anh): Masking PII (Email) trong chunk_text.
    9) Rule mới (Nguyễn Bằng Anh): Đảm bảo chunk_text kết thúc bằng dấu chấm (nếu chưa có).
    """
    quarantine: List[Dict[str, Any]] = []
    seen_text: set[str] = set()
    cleaned: List[Dict[str, Any]] = []
    seq = 0

    # Pattern cho PII Email
    _EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    # Merit/Distinction: Read HR policy cutoff from env instead of hard-coding
    hr_cutoff = os.environ.get("HR_LEAVE_POLICY_CUTOFF", "2026-01-01")

    for raw in rows:
        doc_id = raw.get("doc_id", "")
        text = raw.get("chunk_text", "")
        eff_raw = raw.get("effective_date", "")
        exported_at = raw.get("exported_at", "")

        if doc_id not in ALLOWED_DOC_IDS:
            quarantine.append({**raw, "reason": "unknown_doc_id"})
            continue

        eff_norm, eff_err = _normalize_effective_date(eff_raw)
        if eff_err == "empty_effective_date":
            quarantine.append({**raw, "reason": "missing_effective_date"})
            continue
        if eff_err == "invalid_effective_date_format":
            quarantine.append({**raw, "reason": eff_err, "effective_date_raw": eff_raw})
            continue

        if doc_id == "hr_leave_policy" and eff_norm < hr_cutoff:
            quarantine.append(
                {
                    **raw,
                    "reason": "stale_hr_policy_effective_date",
                    "effective_date_normalized": eff_norm,
                    "cutoff_used": hr_cutoff,
                }
            )
            continue

        if not text:
            quarantine.append({**raw, "reason": "missing_chunk_text"})
            continue

        # RULE 1 (NEW): Validate exported_at format — must be ISO 8601 datetime
        if not _is_valid_exported_at(exported_at):
            quarantine.append({**raw, "reason": "invalid_exported_at_format"})
            continue

        # RULE 2 (NEW): Check for suspicious keywords like [deprecated], [todo], etc.
        if _has_suspicious_keywords(text):
            quarantine.append({**raw, "reason": "has_suspicious_keywords"})
            continue

        # RULE 3 (NEW): Normalize whitespace in chunk_text (collapse spaces, fix line breaks)
        text = _normalize_chunk_text(text)

        key = _norm_text(text)
        if key in seen_text:
            quarantine.append({**raw, "reason": "duplicate_chunk_text"})
            continue
        seen_text.add(key)

        fixed_text = text
        if apply_refund_window_fix and doc_id == "policy_refund_v4":
            if "14 ngày làm việc" in fixed_text:
                fixed_text = fixed_text.replace(
                    "14 ngày làm việc",
                    "7 ngày làm việc",
                )
                fixed_text += " [cleaned: stale_refund_window]"

        # Rule 7: Standardize IT terms
        if doc_id == "it_helpdesk_faq":
            if "wifi" in fixed_text.lower():
                fixed_text = re.sub(r"wifi", "Wi-Fi", fixed_text, flags=re.IGNORECASE)
            if "portal" in fixed_text.lower():
                fixed_text = re.sub(r"portal", "Portal", fixed_text, flags=re.IGNORECASE)

        # Rule 8: Mask PII (Email)
        if _EMAIL_PATTERN.search(fixed_text):
            fixed_text = _EMAIL_PATTERN.sub("[EMAIL]", fixed_text)

        # Rule 9: Ensure ending period
        fixed_text = fixed_text.strip()
        if fixed_text and fixed_text[-1] not in (".", "!", "?"):
            fixed_text += "."

        seq += 1
        cleaned.append(
            {
                "chunk_id": _stable_chunk_id(doc_id, fixed_text, seq),
                "doc_id": doc_id,
                "chunk_text": fixed_text,
                "effective_date": eff_norm,
                "exported_at": exported_at or "",
            }
        )

    return cleaned, quarantine


def write_cleaned_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at\n", encoding="utf-8")
        return
    fieldnames = ["chunk_id", "doc_id", "chunk_text", "effective_date", "exported_at"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_quarantine_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at,reason\n", encoding="utf-8")
        return
    keys: List[str] = []
    seen_k: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen_k:
                seen_k.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)
