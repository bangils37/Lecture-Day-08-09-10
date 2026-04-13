# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Bùi Trọng Anh
**Vai trò trong nhóm:** Tech Lead & Documentation Owner  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong dự án lab Day 08 lần này, tôi đảm nhận song song hai vai trò là **Tech Lead** và **Documentation Owner**. Với tư cách là Tech Lead, tôi chịu trách nhiệm chính trong việc thiết kế kiến trúc hệ thống tổng thể và tích hợp các thành phần từ Indexing (Sprint 1) đến Evaluation (Sprint 4). Tôi đã trực tiếp triển khai phần tích hợp LLM Gemini 1.5 Flash và viết các Grounded Prompts phức tạp giúp mô hình bám sát dữ liệu và trích dẫn mã nguồn chính xác. 

Trong vai trò Documentation Owner, tôi phụ trách biên soạn `architecture.md` để mô tả chi tiết pipeline, cũng như `tuning-log.md` để ghi lại nhật ký thử nghiệm A/B. Tôi cũng là người thực hiện việc merge code từ các nhánh sprint riêng lẻ vào nhánh chính `all-sprints` và đảm bảo mã nguồn luôn ở trạng thái "Production-ready". Công việc của tôi kết nối chặt chẽ với Retrieval Owner để thống nhất schema dữ liệu và Eval Owner để hiểu rõ các failure modes cần khắc phục trong prompt.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi thực sự hiểu sâu hơn về khái niệm **Grounded Answer Function** và cách thiết kế Prompt để kiểm soát ảo giác (hallucination). Trước đây, tôi chỉ nghĩ đơn giản là đưa context vào là xong, nhưng qua thực tế, tôi nhận ra rằng việc thiết kế cấu trúc `context_block` với các số thứ tự [1], [2] và yêu cầu LLM trích dẫn chính xác số này là yếu tố sống còn để xây dựng niềm tin cho người dùng.

Ngoài ra, tôi cũng hiểu rõ hơn về **Cycle of Evaluation**. Thay vì đoán xem prompt nào tốt hơn, việc chạy scorecard tự động giúp tôi thấy được sự đánh đổi (trade-off) giữa các metric. Ví dụ, việc thêm quá nhiều hướng dẫn trong prompt có thể làm tăng tính **Faithfulness** (trung thực) nhưng đôi khi lại làm giảm điểm **Relevance** vì trả lời quá ngắn gọn và cứng nhắc. Việc cân bằng các metric này là một nghệ thuật trong kỹ nghệ prompt.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Điều làm tôi ngạc nhiên nhất là hiệu năng của model Gemini 1.5 Flash. Ban đầu tôi nghĩ một model "Flash" có thể sẽ không thông minh bằng các bản Pro lớn hơn trong việc tuân thủ các điều kiện logic phức tạp. Tuy nhiên, kết quả scorecard cho thấy nó tuân thủ luật "Abstain" (nói không biết khi thiếu dữ liệu) cực kỳ tốt, đạt điểm tuyệt đối cho câu hỏi q09.

Khó khăn lớn nhất mà tôi gặp phải là lỗi **Lost in the Middle** khi danh sách retrieved chunks quá dài. Ban đầu nhóm lấy Top-10 chunks để đưa vào prompt, nhưng điểm Relevance bị giảm mạnh. Tôi đã mất nhiều thời gian debug và nhận ra rằng LLM bị quá tải thông tin nhiễu. Sau đó, tôi đã phối hợp với Retrieval Owner để áp dụng logic "Top-10 Search but Top-3 Select", chỉ lấy 3 đoạn tốt nhất để gửi vào LLM, giúp điểm số cải thiện rõ rệt.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

Tôi chọn phân tích câu hỏi **q07: "Approval Matrix để cấp quyền hệ thống là tài liệu nào?"**

**Câu hỏi:** Đây là một câu hỏi khó thuộc mức độ "Hard" vì người dùng sử dụng một tên gọi cũ ("Approval Matrix") không xuất hiện trực tiếp trong văn bản hiện tại.

**Phân tích:**
- **Baseline (Dense) trả lời sai:** Baseline chỉ đạt điểm Relevance 1/5 và Recall thấp. Nguyên nhân là do vector embedding của cụm từ "Approval Matrix" không đủ gần với nội dung trong tài liệu "Access Control SOP", dẫn đến việc Retriever mang về các đoạn văn về HR Policy hoặc Refund Policy thay vì tài liệu IT Security cần thiết.
- **Lỗi nằm ở giai đoạn Retrieval:** Đây là một failure mode điển hình của Dense Search khi gặp các Alias hoặc tên gọi cũ mà model embedding chưa được fine-tune để nhận diện sự tương đồng.
- **Variant (Hybrid) có cải thiện vượt trội:** Trong bản Hybrid, sau khi chúng tôi kết hợp BM25 (Sparse) với trọng số phù hợp, từ khóa "Approval" và "Access" đã giúp hệ thống tìm được đúng file `access_control_sop.md`. Variant đã trả lời chính xác: "Tài liệu Approval Matrix hiện có tên mới là Access Control SOP". Điều này minh chứng rằng Hybrid Retrieval là giải pháp bắt buộc cho các hệ thống RAG doanh nghiệp chứa nhiều thuật ngữ chuyên môn và lịch sử thay đổi tài liệu.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi sẽ triển khai **Query Expansion** ở giai đoạn trước khi Retrieval. Qua kết quả eval ở câu q07, tôi thấy rằng nếu chúng ta dùng LLM để sinh ra các từ đồng nghĩa (synonyms) cho query trước khi search, chúng ta có thể cải thiện điểm Recall cho cả Baseline mà không cần phụ thuộc quá nhiều vào BM25. Ngoài ra, tôi muốn thử nghiệm **LangGraph** để xây dựng một agent có khả năng tự sửa lỗi (Self-RAG) khi nhận thấy điểm Faithfulness thấp.

---
