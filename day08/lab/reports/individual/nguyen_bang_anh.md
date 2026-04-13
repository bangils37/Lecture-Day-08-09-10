# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Nguyễn Bằng Anh  
**Vai trò trong nhóm:** Retrieval Owner  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong dự án lab lần này, với vai trò là **Retrieval Owner**, tôi chịu trách nhiệm chính về toàn bộ "phần dưới" của pipeline RAG, bao gồm các Sprint 1 và Sprint 3. Tôi đã trực tiếp thiết kế chiến lược chunking dựa trên cấu trúc tự nhiên của văn bản (Paragraph-based chunking) để đảm bảo các thông tin quan trọng trong một quy trình IT hay chính sách HR không bị cắt rời. 

Tôi đã hiện thực hóa việc lưu trữ dữ liệu vào **Qdrant Vector Database**, cấu hình collection với các metadata phong phú để hỗ trợ tra cứu chính xác. Đặc biệt ở Sprint 3, tôi đã nghiên cứu và triển khai **Hybrid Retrieval** kết hợp giữa Dense Search (Cosine similarity) và Sparse Search (BM25 OKapi). Tôi cũng đã thực hiện việc điều chỉnh trọng số (tuning) thông qua thuật toán **Reciprocal Rank Fusion (RRF)** để tìm ra điểm cân bằng tối ưu giữa việc hiểu ngữ nghĩa và khớp từ khóa. Công việc của tôi cung cấp nền tảng dữ liệu cho Tech Lead xây dựng prompt và là đối tượng chính để Eval Owner thực hiện các bài đánh giá A/B.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Một trong những điều tôi hiểu rõ nhất sau lab này chính là tầm quan trọng của **Chunking Strategy**. Trước đây, tôi thường sử dụng `RecursiveCharacterTextSplitter` một cách máy móc theo kích thước token cố định. Tuy nhiên, khi làm việc với các tài liệu quy trình (SOP), tôi nhận ra rằng việc cắt ngang một câu hoặc một bước trong quy trình sẽ làm giảm đáng kể khả năng trả lời đúng của LLM. Việc chuyển sang tách theo đoạn văn (`\n\n`) kết hợp với `overlap` hợp lý giúp các chunk mang tính tự giải thích (self-contained) cao hơn nhiều.

Thứ hai là khái niệm **Hybrid Search và RRF**. Tôi đã hiểu tại sao các hệ thống RAG thực tế không bao giờ chỉ dùng mỗi Vector Search. Khả năng "bắt" từ khóa cực mạnh của BM25 cho các thực thể cụ thể (Mã lỗi, tên riêng, số hiệu phiên bản) là mảnh ghép còn thiếu mà Dense Embedding đôi khi bỏ qua do tập trung quá nhiều vào Semantic Space. RRF là một phương pháp gộp kết quả cực kỳ hiệu quả mà không cần lo lắng về việc chuẩn hóa thang điểm (score normalization) giữa hai thuật toán khác nhau.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn lớn nhất mà tôi gặp phải nằm ở việc thiết lập **BM25 Search** trên môi trường local. Vì Qdrant mặc định mạnh về Vector Search, việc tích hợp thêm một thư viện BM25 ngoài (`rank-bm25`) yêu cầu tôi phải xử lý việc đồng bộ hóa dữ liệu giữa bộ nhớ (In-memory) và database. Tôi đã mất khá nhiều thời gian để tối ưu hóa quá trình tokenizer cho tiếng Việt để đảm bảo các từ khóa quan trọng không bị tách sai khi tính toán điểm BM25.

Điều làm tôi ngạc nhiên là sự nhạy cảm của kết quả đối với các tham số **RRF weight**. Trong các thử nghiệm ban đầu, tôi để trọng số 50-50 cho Dense và Sparse, nhưng kết quả thu được lại có nhiều nhiễu. Thực tế cho thấy, với tập dữ liệu của lab, việc ưu tiên Dense hơn một chút (`0.7/0.3`) mang lại sự ổn định cao hơn cho các câu hỏi mang tính diễn giải, trong khi vẫn giữ được độ chính xác cho các câu hỏi tra cứu mã lỗi. Giả thuyết ban đầu của tôi là Sparse sẽ đóng vai trò phụ, nhưng thực tế nó lại là yếu tố quyết định giúp cải thiện điểm số ở các câu hỏi khó nhất.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

Tôi chọn phân tích câu hỏi **q01: "SLA xử lý ticket P1 là bao lâu?"** dưới góc độ của người làm Retrieval.

**Câu hỏi:** Câu hỏi này yêu cầu trích xuất một con số cụ thể (4 giờ) từ một tài liệu có nhiều mốc thời gian khác nhau (SLA phản hồi 15p, SLA xử lý cũ 6 giờ).

**Phân tích:**
- **Baseline (Dense) thực hiện tốt nhưng chưa hoàn hảo:** Trong bản Baseline, model embedding tìm được file `sla-p1-2026.pdf`. Tuy nhiên, vì nội dung file này chứa cả thông tin về phiên bản cũ (v2025 - 6 giờ) và phiên bản mới (v2026 - 4 giờ), Dense search đôi khi trả về cả hai chunk này với điểm số tương đương nhau. Điều này khiến LLM đôi khi bị nhầm lẫn giữa hai con số.
- **Lỗi nằm ở Indexing/Metadata:** Tôi nhận ra rằng nếu chỉ dựa vào embedding, model không phân biệt được đâu là thông tin "mới nhất" nếu hai đoạn văn có cấu trúc từ ngữ giống hệt nhau.
- **Variant (Hybrid) mang lại sự khác biệt:** Nhờ BM25, khi query có chứa cụm từ "SLA P1", các chunk thuộc file `sla-p1-2026.pdf` được ưu tiên cực cao. Đặc biệt, việc tôi bổ sung metadata `effective_date` vào payload và hiển thị nó trong `context_block` đã giúp LLM nhận diện được đoạn văn chứa thông tin cập nhật mới nhất (4 giờ). Điểm Faithfulness đạt 5/5 và Recall đạt 100% cho câu hỏi này là bằng chứng cho thấy sự kết hợp giữa Hybrid retrieval và Metadata extraction là hướng đi đúng đắn.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ triển khai **Multi-stage Retrieval** với một bước **Reranker (Cross-Encoder)**. Kết quả đánh giá cho thấy Hybrid search mang về khá nhiều chunk (Top-10), và dù chúng ta có RRF nhưng vẫn có sự xuất hiện của các đoạn văn không thực sự trả lời được câu hỏi. Một model Rerank mạnh sẽ giúp lọc bỏ các chunk "có vẻ liên quan" nhưng thiếu thông tin trả lời, giúp LLM tập trung hơn và nâng cao điểm Relevance cho toàn hệ thống.

---
