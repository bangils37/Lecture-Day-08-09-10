"""Sprint 1: indexing pipeline (Qdrant + Qwen Embedding)."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

# =============================================================================
# CẤU HÌNH
# =============================================================================

DOCS_DIR = Path(__file__).parent / "data" / "docs"
QDRANT_DB_DIR = Path(__file__).parent / "qdrant_db"
QDRANT_COLLECTION = "rag_lab"

# 300-500 tokens/chunk, overlap 50-80 tokens (ước lượng 1 token ~ 4 chars)
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80

EMBEDDING_MODEL_NAME = os.getenv("LOCAL_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
QDRANT_MODE = os.getenv("QDRANT_MODE", "local").strip().lower()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def _get_embedding_model():
    """Lazy-load embedding model để tránh load lại nhiều lần."""
    from sentence_transformers import SentenceTransformer

    model = getattr(_get_embedding_model, "_cached_model", None)
    if model is None:
        print(f"[Embedding] Loading model: {EMBEDDING_MODEL_NAME}")
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        setattr(_get_embedding_model, "_cached_model", model)
    return model


def _get_qdrant_client(db_dir: Path = QDRANT_DB_DIR) -> QdrantClient:
    if QDRANT_MODE == "server":
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    if QDRANT_MODE == "memory":
        return QdrantClient(":memory:")
    db_dir.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(db_dir))


# =============================================================================
# STEP 1: PREPROCESS
# =============================================================================

def preprocess_document(raw_text: str, filepath: str) -> Dict[str, Any]:
    """Extract metadata từ header và làm sạch nội dung tài liệu."""
    lines = raw_text.strip().splitlines()
    metadata = {
        "source": Path(filepath).name,
        "section": "",
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal",
    }

    content_start_idx = 0
    metadata_pattern = re.compile(r"^([A-Za-z ]+):\s*(.+)$")

    for idx, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            continue

        header_match = metadata_pattern.match(stripped)
        if header_match:
            key = header_match.group(1).strip().lower().replace(" ", "_")
            value = header_match.group(2).strip()

            if key == "source":
                metadata["source"] = value
            elif key == "department":
                metadata["department"] = value
            elif key == "effective_date":
                metadata["effective_date"] = value
            elif key == "access":
                metadata["access"] = value

            content_start_idx = idx + 1
            continue

        if stripped.startswith("==="):
            content_start_idx = idx
            break

    content_lines = lines[content_start_idx:]
    cleaned_text = "\n".join(content_lines)
    cleaned_text = re.sub(r"\r\n?", "\n", cleaned_text)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

    return {"text": cleaned_text, "metadata": metadata}


# =============================================================================
# STEP 2: CHUNK
# =============================================================================

def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Chunk theo section heading rồi split theo paragraph để tránh cắt giữa điều khoản."""
    text = doc["text"]
    base_metadata = doc["metadata"].copy()
    sections = _split_sections(text)

    chunks: List[Dict[str, Any]] = []
    for section_name, section_text in sections:
        chunks.extend(
            _split_by_size(
                text=section_text,
                base_metadata=base_metadata,
                section=section_name,
                chunk_chars=CHUNK_SIZE * 4,
                overlap_chars=CHUNK_OVERLAP * 4,
            )
        )
    return chunks


def _split_sections(text: str) -> List[Tuple[str, str]]:
    pattern = re.compile(r"(?m)^===\s*(.+?)\s*===\s*$")
    matches = list(pattern.finditer(text))

    if not matches:
        return [("General", text.strip())] if text.strip() else []

    sections: List[Tuple[str, str]] = []
    preface = text[: matches[0].start()].strip()
    if preface:
        sections.append(("General", preface))

    for i, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        if section_text:
            sections.append((section_name, section_text))
    return sections


def _tail_overlap(text: str, overlap_chars: int) -> str:
    if len(text) <= overlap_chars:
        return text

    start = len(text) - overlap_chars
    while start > 0 and not text[start].isspace():
        start -= 1
    return text[start:].strip()


def _split_by_size(
    text: str,
    base_metadata: Dict[str, Any],
    section: str,
    chunk_chars: int,
    overlap_chars: int,
) -> List[Dict[str, Any]]:
    if len(text) <= chunk_chars:
        return [{"text": text, "metadata": {**base_metadata, "section": section}}]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: List[Dict[str, Any]] = []
    current_paragraphs: List[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        projected = current_len + para_len + (2 if current_paragraphs else 0)

        if current_paragraphs and projected > chunk_chars:
            chunk_text = "\n\n".join(current_paragraphs).strip()
            chunks.append({"text": chunk_text, "metadata": {**base_metadata, "section": section}})

            overlap_text = _tail_overlap(chunk_text, overlap_chars)
            current_paragraphs = [overlap_text, para] if overlap_text else [para]
            current_len = len("\n\n".join(current_paragraphs))
        else:
            current_paragraphs.append(para)
            current_len = projected

    if current_paragraphs:
        chunk_text = "\n\n".join(current_paragraphs).strip()
        chunks.append({"text": chunk_text, "metadata": {**base_metadata, "section": section}})

    return chunks


# =============================================================================
# STEP 3: EMBED + STORE (Qdrant)
# =============================================================================

def get_embedding(text: str) -> List[float]:
    """Tạo embedding vector bằng SentenceTransformer Qwen."""
    model = _get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def _get_embeddings(texts: List[str]) -> List[List[float]]:
    model = _get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [vector.tolist() for vector in vectors]


def build_index(docs_dir: Path = DOCS_DIR, db_dir: Path = QDRANT_DB_DIR) -> None:
    """Đọc docs -> preprocess -> chunk -> embed -> upsert vào Qdrant."""
    print(f"Đang build index từ: {docs_dir}")

    doc_files = sorted(docs_dir.glob("*.txt"))
    if not doc_files:
        print(f"Không tìm thấy file .txt trong {docs_dir}")
        return

    all_chunks: List[Dict[str, Any]] = []
    for filepath in doc_files:
        raw_text = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw_text, str(filepath))
        chunks = chunk_document(doc)

        for i, chunk in enumerate(chunks):
            chunk["metadata"]["chunk_index"] = i
            chunk["metadata"]["document_name"] = filepath.name
            chunk["metadata"]["source_file"] = filepath.name

        all_chunks.extend(chunks)
        print(f"  - {filepath.name}: {len(chunks)} chunks")

    if not all_chunks:
        print("Không có chunk nào để index.")
        return

    texts = [chunk["text"] for chunk in all_chunks]
    vectors = _get_embeddings(texts)
    vector_size = len(vectors[0])

    client = _get_qdrant_client(db_dir)
    client.recreate_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    points: List[PointStruct] = []
    for idx, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        payload = {**chunk["metadata"], "text": chunk["text"]}
        points.append(PointStruct(id=idx, vector=vector, payload=payload))

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)

    print(f"\nHoàn thành index: {len(doc_files)} tài liệu, {len(all_chunks)} chunks")
    print(f"Collection: {QDRANT_COLLECTION}")
    print(f"Qdrant mode: {QDRANT_MODE}")


# =============================================================================
# STEP 4: INSPECT / KIỂM TRA
# =============================================================================

def list_points(db_dir: Path = QDRANT_DB_DIR, n: int = 5) -> None:
    """In ra n points đầu tiên để kiểm tra chunk + metadata."""
    try:
        client = _get_qdrant_client(db_dir)
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=n,
            with_payload=True,
            with_vectors=False,
        )

        print(f"\n=== Top {n} points trong Qdrant ===\n")
        for i, point in enumerate(points, start=1):
            payload = point.payload or {}
            text = payload.get("text", "")
            print(f"[Point {i}] id={point.id}")
            print(f"  Source: {payload.get('source', 'N/A')}")
            print(f"  Section: {payload.get('section', 'N/A')}")
            print(f"  Effective Date: {payload.get('effective_date', 'N/A')}")
            print(f"  Text preview: {text[:140]}...")
            print()
    except Exception as exc:
        print(f"Lỗi khi đọc points: {exc}")
        print("Hãy chạy build_index() trước.")


def inspect_metadata_coverage(db_dir: Path = QDRANT_DB_DIR) -> None:
    """Kiểm tra độ phủ metadata sau khi index."""
    try:
        client = _get_qdrant_client(db_dir)
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=10_000,
            with_payload=True,
            with_vectors=False,
        )
    except Exception as exc:
        print(f"Lỗi: {exc}. Hãy chạy build_index() trước.")
        return

    total = len(points)
    if total == 0:
        print("Collection đang rỗng.")
        return

    departments: Dict[str, int] = {}
    missing_source = 0
    missing_section = 0
    missing_effective_date = 0

    for point in points:
        payload = point.payload or {}
        dept = str(payload.get("department", "unknown"))
        departments[dept] = departments.get(dept, 0) + 1

        if not payload.get("source"):
            missing_source += 1
        if not payload.get("section"):
            missing_section += 1
        if not payload.get("effective_date") or payload.get("effective_date") == "unknown":
            missing_effective_date += 1

    print(f"\nTổng points: {total}")
    print("Phân bố department:")
    for dept, count in sorted(departments.items(), key=lambda item: item[1], reverse=True):
        print(f"  - {dept}: {count}")

    print("\nThiếu metadata:")
    print(f"  - source: {missing_source}")
    print(f"  - section: {missing_section}")
    print(f"  - effective_date: {missing_effective_date}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 1: Build RAG Index (Qdrant + Qwen)")
    print("=" * 60)

    doc_files = sorted(DOCS_DIR.glob("*.txt"))
    print(f"\nTìm thấy {len(doc_files)} tài liệu:")
    for file_path in doc_files:
        print(f"  - {file_path.name}")

    # Preview preprocess + chunking nhanh trên 1 file
    if doc_files:
        sample_raw = doc_files[0].read_text(encoding="utf-8")
        sample_doc = preprocess_document(sample_raw, str(doc_files[0]))
        sample_chunks = chunk_document(sample_doc)
        print("\n--- Preview preprocess + chunking ---")
        print(f"File mẫu: {doc_files[0].name}")
        print(f"Metadata: {sample_doc['metadata']}")
        print(f"Số chunks: {len(sample_chunks)}")
        for i, chunk in enumerate(sample_chunks[:2], start=1):
            print(f"\n[Chunk {i}] {chunk['metadata']['section']}")
            print(chunk["text"][:180] + "...")

    print("\n--- Build Full Index ---")
    build_index()

    print("\n--- Inspect Points ---")
    list_points(n=5)

    print("\n--- Metadata Coverage ---")
    inspect_metadata_coverage()
