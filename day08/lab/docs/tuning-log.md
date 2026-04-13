# Tuning Log — RAG Pipeline Optimization

**Dự án:** Lab Day 08 - RAG Pipeline
**Ngày:** 2026-04-13
**Người thực hiện:** Bangils

---

## 1. Thử nghiệm: Hybrid Retrieval (Dense + BM25)

### Biến thay đổi (Variable)
- **Baseline:** Dense Retrieval (Cosine similarity on Qwen3 embeddings).
- **Variant:** Hybrid Retrieval (Dense Retrieval + BM25 Sparse Search) sử dụng thuật toán **Reciprocal Rank Fusion (RRF)**.
- **Tham số:** `dense_weight=0.7`, `sparse_weight=0.3`, `top_k_search=10`, `top_k_select=3`.

### Lý do chọn biến (Rationale)
Mô hình Dense retrieval hoạt động tốt cho các câu hỏi mang tính ngữ nghĩa, nhưng thường gặp khó khăn với các thuật ngữ kỹ thuật viết tắt hoặc mã định danh duy nhất (unique identifiers). Trong bộ tài liệu CS/IT Helpdesk của chúng ta, các mã lỗi như `ERR-403-AUTH` hoặc các ký hiệu phân loại như `P1` (Priority 1) là những điểm cực kỳ quan trọng. BM25 (Sparse) vượt trội trong việc khớp chính xác các từ khóa này, bổ khuyết cho khả năng hiểu ý nghĩa của Dense Retrieval.

---

## 2. Kết quả đánh giá (Evaluation Results)

Dưới đây là bảng so sánh hiệu năng giữa Baseline và Variant dựa trên 10 câu hỏi kiểm thử:

| Metric | Baseline (Dense) | Variant (Hybrid) | Delta | Nhận xét |
|--------|------------------|------------------|-------|----------|
| **Faithfulness** | 4.70 | **5.00** | +0.30 | Hybrid giúp trích xuất chính xác context chứa từ khóa kỹ thuật, giảm ảo giác. |
| **Answer Relevance** | **3.40** | 3.30 | -0.10 | Đôi khi việc thêm kết quả từ BM25 mang lại một số context thừa gây nhiễu cho LLM. |
| **Context Recall** | 5.00 | 5.00 | 0.00 | Cả hai đều tìm được đúng tài liệu cho bộ test set hiện tại. |
| **Completeness** | 3.70 | **3.80** | +0.10 | Hybrid giúp lấy được các thông tin bổ sung có cùng từ khóa mà Dense bỏ sót. |

---

## 3. Kết luận (Conclusion)

### Variant tốt hơn/kém hơn ở điểm nào?
- **Tốt hơn:** Variant Hybrid vượt trội ở tính **Trung thực (Faithfulness)**. Việc khớp chính xác từ khóa "P1" hoặc "Refund" giúp LLM nhận được đúng đoạn trích dẫn chứa con số và quy định cụ thể, tránh việc LLM phải suy luận dựa trên các đoạn văn có ý nghĩa tương đương nhưng nội dung khác biệt.
- **Kém hơn:** Điểm **Relevance** giảm nhẹ do RRF đôi khi ưu tiên các chunk có mật độ từ khóa cao nhưng ngữ cảnh tổng thể kém liên quan hơn so với vector embedding.

### Bằng chứng (Evidence)
- Trong câu hỏi **q01 (SLA P1)**, Variant Hybrid luôn đưa chunk về resolution time lên vị trí số 1 nhờ khớp từ khóa "P1", trong khi Baseline đôi khi đưa các chunk về "General Support" lên trên.
- Trong câu hỏi **q09 (Abstain case)**, Hybrid chỉ ra rõ ràng hơn là không có từ khóa `ERR-403-AUTH` trong bất kỳ tài liệu nào, củng cố tính Grounding cho hệ thống.

### Quyết định cuối cùng
Nhóm quyết định sử dụng **Variant Hybrid** cho phiên bản nộp bài cuối cùng (Grading) vì ưu tiên tính chính xác và trung thực của thông tin hỗ trợ kỹ thuật hơn là sự hoa mỹ của câu trả lời.
