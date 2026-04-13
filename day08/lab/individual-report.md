# Lab Report: RAG Pipeline Implementation & Tuning

## 1. Objective
Xây dựng pipeline RAG hoàn chỉnh từ indexing đến evaluation để hỗ trợ tra cứu tài liệu nội bộ (Refund Policy, SLA, Access Control).

## 2. Methodology

### Sprint 1: Indexing
- **Preprocessing:** Trích xuất metadata (Source, Department, Effective Date) tự động từ header tài liệu.
- **Chunking:** Sử dụng Paragraph-based chunking (split by `\n\n`) với size ~500 chars và overlap 100 chars để giữ ngữ cảnh tốt nhất.
- **Vector DB:** Sử dụng Qdrant (Cloud) để lưu trữ vector.
- **Embedding:** `Qwen/Qwen3-Embedding-0.6B` mang lại performance tốt cho tiếng Việt/Anh hybrid.

### Sprint 2: Baseline RAG
- **Retrieval:** Dense retrieval (top-k=10).
- **Generation:** Gemini 1.5 Flash với grounded prompt ép model chỉ trả lời dựa trên context và trích dẫn nguồn [1][2].

### Sprint 3: Tuning
- **Strategy:** Hybrid Retrieval (Dense + BM25) kết hợp bằng Reciprocal Rank Fusion (RRF).
- **Rationale:** Khắc phục nhược điểm của Dense retrieval khi gặp các từ khóa chính xác (keyword-heavy) như mã lỗi "ERR-403" hoặc mã Ticket "P1".

### Sprint 4: Evaluation
- **Metrics:** Sử dụng 4 metric (Faithfulness, Relevance, Recall, Completeness) chấm qua LLM-as-Judge.
- **Result:** Hybrid cải thiện tính trung thực (Faithfulness) từ 4.7 lên 5.0.

## 3. Results & Discussion

| Metric | Baseline (Dense) | Variant (Hybrid) | Delta |
|--------|------------------|------------------|-------|
| Faithfulness | 4.70 | 5.00 | +0.30 |
| Answer Relevance | 3.40 | 3.30 | -0.10 |
| Context Recall | 5.00 | 5.00 | 0.00 |
| Completeness | 3.70 | 3.80 | +0.10 |

- **Key Finding:** Hệ thống hoạt động rất tốt trong việc tìm đúng tài liệu (Recall 5.0/5.0). Hybrid giúp model bám sát context tốt hơn nhưng đôi khi làm loãng sự tập trung của LLM ở các câu hỏi mang tính diễn giải.

## 4. Conclusion
Dự án đã hoàn thành cả 4 sprints đúng hạn, đạt được độ tin cậy cao (Faithfulness 5.0) và khả năng trích dẫn chính xác. Hướng phát triển tiếp theo là áp dụng Rerank (Cross-Encoder) để lọc nhiễu tốt hơn sau khi Hybrid retrieval.
