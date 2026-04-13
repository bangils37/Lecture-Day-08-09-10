# Group Report — Lab Day 08: RAG Pipeline

**Nhóm:** Bangils (Documentation Owner: Bangils)
**Chủ đề:** Xây dựng hệ thống RAG nội bộ cho CS & IT Helpdesk

## 1. Thành phần hệ thống

Hệ thống RAG của chúng tôi được xây dựng với các thành phần hiện đại nhằm tối ưu hóa độ chính xác và khả năng mở rộng:

- **Vector Database:** **Qdrant** (Cloud/Local) — Được chọn thay vì ChromaDB vì khả năng quản lý collection mạnh mẽ và hỗ trợ Hybrid search hiệu quả.
- **Embedding Model:** **Qwen/Qwen3-Embedding-0.6B** — Một model local nhẹ nhưng hiệu quả cao cho cả tiếng Anh và tiếng Việt.
- **Retrieval Strategy:** **Hybrid Retrieval** kết hợp **Dense Search** và **BM25** thông qua thuật toán **Reciprocal Rank Fusion (RRF)**.
- **LLM:** **Gemini 1.5 Flash** — Cung cấp tốc độ phản hồi nhanh và khả năng hiểu ngữ cảnh tốt với chi phí tối ưu.

## 2. Các quyết định kỹ thuật quan trọng

### Chunking Strategy
Chúng tôi áp dụng **Paragraph-based chunking** với ranh giới là các dấu xuống dòng `\n\n`. Cách tiếp cận này giúp giữ toàn vẹn thông tin trong một điều khoản hoặc một FAQ, tránh tình trạng thông tin bị cắt đôi làm mất ý nghĩa. Chúng tôi sử dụng `overlap` khoảng 100 ký tự để đảm bảo tính liên kết giữa các chunk.

### Hybrid Retrieval (RRF)
Qua quá trình test baseline (Dense-only), chúng tôi nhận thấy một số câu hỏi chứa từ khóa kỹ thuật (như "P1", "ERR-403") dễ bị trôi đi nếu chỉ tìm kiếm theo ngữ nghĩa. Việc kết hợp BM25 giúp các "hard keywords" được ưu tiên, từ đó nâng cao tính trung thực (Faithfulness) và giảm thiểu tình trạng model phải tự bịa câu trả lời.

### Evaluation (LLM-as-Judge)
Thay vì chấm điểm thủ công, nhóm đã triển khai hệ thống chấm điểm tự động trong `eval.py` sử dụng Gemini để đánh giá:
- **Faithfulness**: Liệu câu trả lời có dựa trên context không?
- **Answer Relevance**: Câu trả lời có đúng trọng tâm không?
- **Completeness**: Có bỏ lỡ chi tiết quan trọng nào không?

## 3. Kết quả đánh giá

Hệ thống Hybrid đạt điểm trung bình cao hơn Baseline trên hầu hết các metric, đặc biệt là **Faithfulness (5.0/5.0)**. Khả năng **Recall** cũng đạt mức tối đa cho tập dữ liệu mẫu, xác nhận rằng retriever đã mang về đầy đủ bằng chứng cần thiết cho LLM.

## 4. Phân vai thành viên (Nếu có)
- **Tech Lead:** [Tên] — Framework, End-to-end integration.
- **Retrieval Owner:** [Tên] — Qdrant setup, Hybrid logic, Chunking.
- **Eval Owner:** [Tên] — Scorecard implementation, LLM-as-Judge.
- **Documentation Owner:** **Bangils** — Architecture docs, Tuning log, Group report.
