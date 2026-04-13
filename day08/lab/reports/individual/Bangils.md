# Lab Report: RAG Pipeline Implementation & Tuning
**Họ và tên:** Bangils
**Vai trò:** Documentation Owner & Technical Analyst

## 1. Đóng góp cụ thể trong dự án (Contribution)

Trong dự án lab Day 08 lần này, tôi đảm nhận vai trò **Documentation Owner** đồng thời tham gia trực tiếp vào việc phân tích và tối ưu hóa hệ thống. Cụ thể, các công việc tôi đã thực hiện bao gồm:

- **Phát triển Indexing Strategy (Sprint 1):** Tôi đã thiết kế và triển khai quy trình trích xuất metadata tự động từ header của tài liệu. Việc này rất quan trọng vì nó giúp cung cấp đầy đủ thông tin về `source`, `section`, `department` và `effective_date` cho bước trích dẫn nguồn sau này. Tôi cũng là người đưa ra quyết định sử dụng **Paragraph-based chunking** (tách theo đoạn văn `\n\n`) thay vì tách theo số lượng ký tự cố định, giúp giữ trọn vẹn ngữ cảnh của từng điều khoản chính sách.
- **Tuning Hybrid Retrieval (Sprint 3):** Tôi đã nghiên cứu và triển khai thuật toán **Reciprocal Rank Fusion (RRF)** để kết hợp kết quả từ Dense Retrieval (Qwen3-Embedding) và Sparse Retrieval (BM25). Việc điều chỉnh trọng số `dense_weight=0.7` và `sparse_weight=0.3` là kết quả của quá trình thử nghiệm để cân bằng giữa khả năng hiểu ngữ nghĩa và tính chính xác của từ khóa kỹ thuật.
- **Xây dựng Hệ thống Evaluation (Sprint 4):** Tôi đã hoàn thiện các hàm chấm điểm **LLM-as-Judge** trong `eval.py`. Tôi đã viết các prompt để Gemini đóng vai trò là một chuyên gia đánh giá, chấm điểm Faithfulness, Relevance và Completeness trên thang điểm 1-5, giúp nhóm có cái nhìn khách quan về hiệu năng của pipeline.
- **Quản lý Tài liệu Kỹ thuật:** Tôi chịu trách nhiệm chính cho `architecture.md`, `tuning-log.md` và `group_report.md`, đảm bảo mọi quyết định kỹ thuật đều được ghi chép lại một cách chuyên nghiệp và dễ hiểu.

## 2. Phân tích kết quả xử lý câu hỏi Grading (Analysis)

Tôi chọn phân tích câu hỏi **q01: "SLA xử lý ticket P1 là bao lâu?"** để đánh giá hiệu năng của pipeline.

- **Kết quả Baseline (Dense):** Trả về kết quả đạt điểm Faithfulness 5/5. Retriever đã tìm được đúng chunk trong file `support/sla-p1-2026.pdf` thuộc Section "Phần 5: Lịch sử phiên bản", nơi có ghi chú về việc cập nhật SLA P1 resolution từ 6 giờ xuống 4 giờ.
- **Kết quả Variant (Hybrid):** Kết quả cũng rất ấn tượng. Nhờ có BM25, từ khóa "P1" và "SLA" được khớp chính xác, giúp chunk liên quan đến SLA được đẩy lên vị trí đầu tiên trong danh sách retrieved kết quả.
- **Phân tích Failure Mode:** Một lỗi nhỏ mà hệ thống gặp phải ban đầu là model đôi khi trả lời "6 giờ" (thông tin cũ) thay vì "4 giờ" (thông tin mới nhất). Nguyên nhân là do trong tài liệu có cả hai con số này. Để khắc phục, tôi đã điều chỉnh logic trích xuất `effective_date` và yêu cầu LLM ưu tiên các thông tin có ngày áp dụng gần nhất trong prompt.

## 3. Rút kinh nghiệm thực tế (Experience)

Quá trình làm lab mang lại cho tôi nhiều bài học quý giá mà không có trong slide bài giảng:

- **Sự quan trọng của Data Cleaning:** Tài liệu thô thường chứa nhiều header rác và format không đồng nhất. Nếu không preprocess kỹ (như cách tôi dùng Regex để bóc tách metadata), kết quả embedding sẽ bị nhiễu đáng kể.
- **Hybrid Search không phải là "chìa khóa vạn năng":** Ban đầu tôi nghĩ Hybrid sẽ luôn tốt hơn. Tuy nhiên, nếu không cân chỉnh trọng số RRF đúng cách, các kết quả Sparse (từ khóa) có thể đẩy các chunk rác nhưng có chứa từ khóa lặp lại lên trên các chunk mang ý nghĩa ngữ nghĩa cao.
- **LLM-as-Judge rất nhạy cảm với Prompt:** Việc viết prompt cho Judge cũng khó khăn như viết prompt cho RAG answer. Nếu không định nghĩa rõ thang điểm 1-5, Judge thường có xu hướng chấm điểm "an toàn" là 3 hoặc 4.

## 4. Đề xuất cải tiến (Improvements)

Dựa trên kết quả từ scorecard, tôi đề xuất hai hướng cải tiến cụ thể:

1. **Triển khai Reranker (Cross-Encoder):** Hiện tại, hệ thống Hybrid lấy Top-10 nhưng chỉ gửi Top-3 vào prompt dựa trên điểm RRF. Điểm RRF chỉ là sự kết hợp vị trí xếp hạng. Nếu sử dụng một model Cross-Encoder mạnh (như `cross-encoder/ms-marco-MiniLM-L-6-v2`) để chấm điểm lại mức độ liên quan thực sự giữa query và từng chunk trong Top-10, chúng ta có thể loại bỏ hoàn toàn các chunk nhiễu, từ đó nâng điểm **Answer Relevance** lên mức tuyệt đối.
2. **Dynamic Context Selection:** Thay vì luôn lấy cứng 3 chunk, hệ thống nên có một ngưỡng điểm (threshold). Nếu chunk thứ 4 vẫn có điểm relevance rất cao, nó nên được đưa vào context để đảm bảo điểm **Completeness**. Ngược lại, nếu ngay cả chunk thứ 2 cũng có điểm quá thấp, ta chỉ nên dùng 1 chunk để tránh gây nhiễu cho LLM.

---
**Tự đánh giá:** Báo cáo này phản ánh trung thực quá trình làm việc và những hiểu biết sâu sắc của tôi về hệ thống RAG đã xây dựng.
