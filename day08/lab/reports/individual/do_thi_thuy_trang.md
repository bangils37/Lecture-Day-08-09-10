# Báo Cáo Cá Nhân — Lab Day 08: RAG Pipeline

**Họ và tên:** Đỗ Thị Thùy Trang  
**Vai trò trong nhóm:** Eval Owner  
**Ngày nộp:** 2026-04-13  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi đã làm gì trong lab này? (100-150 từ)

Trong dự án RAG Pipeline lần này, tôi đảm nhận vai trò **Eval Owner**, chịu trách nhiệm thiết lập "thước đo" cho toàn bộ hệ thống ở các Sprint 3 và 4. Công việc của tôi bắt đầu từ việc xây dựng bộ dữ liệu đánh giá trong `test_questions.json`, bao gồm việc xác định các câu hỏi kiểm thử từ mức độ Dễ đến Khó và định nghĩa `expected_answer` kèm theo `expected_sources` (Ground Truth).

Tôi đã trực tiếp thiết lập framework đánh giá tự động sử dụng phương pháp **LLM-as-Judge**. Tôi đã hiện thực hóa các metrics quan trọng như Faithfulness, Answer Relevance, Context Recall và Completeness trong file `eval.py`. Tôi cũng là người thực hiện các lượt chạy Scorecard để so sánh hiệu năng giữa phiên bản Baseline (Dense) và Variant (Hybrid), từ đó cung cấp số liệu thực tế để nhóm đưa ra các quyết định điều chỉnh tham số. Kết quả của tôi chính là cơ sở dữ liệu cho các phân tích trong `tuning-log.md` và báo cáo nhóm.

---

## 2. Điều tôi hiểu rõ hơn sau lab này (100-150 từ)

Sau lab này, tôi thực sự thấu hiểu khái niệm **Evaluation Loop** trong phát triển RAG. Trước đây, tôi nghĩ rằng việc đánh giá một hệ thống AI là công việc cảm tính bằng cách "thử một vài câu hỏi và thấy nó trả lời ổn". Tuy nhiên, qua thực tế triển khai, tôi nhận ra rằng nếu không có một bộ trắc nghiệm ổn định (Scorecard) và các chỉ số đo lường cụ thể, chúng ta sẽ không thể biết được việc đổi sang Hybrid search hay đổi Chunking strategy thực sự cải thiện hệ thống hay lại làm nó tệ đi ở một khía cạnh khác.

Đặc biệt, tôi rất ấn tượng với phương pháp **LLM-as-Judge**. Việc dùng một model LLM mạnh để chấm điểm cho kết quả của một model RAG khác mang lại sự linh hoạt và khả năng hiểu ngữ nghĩa sâu sắc mà các metrics truyền thống như ROUGE hay BLEU không làm được. Tôi đã hiểu cách viết các tiêu chí chấm điểm (rubrics) chi tiết để Judge có thể đưa ra điểm số khách quan và giải thích được nguyên nhân tại sao lại chấm như vậy.

---

## 3. Điều tôi ngạc nhiên hoặc gặp khó khăn (100-150 từ)

Khó khăn lớn nhất mà tôi gặp phải là hiện tượng **"Judge Bias"**. Trong quá trình thử nghiệm ban đầu, tôi nhận thấy LLM Judge thường chấm điểm Faithfulness rất cao dù câu trả lời có chứa một số thông tin không xuất hiện trong context. Tôi đã phải mất nhiều thời gian để tinh chỉnh prompt của Judge, bổ sung các hướng dẫn cực kỳ nghiêm ngặt như "Chỉ cho 5 điểm nếu từng chi tiết nhỏ đều được chứng minh bởi context" và yêu cầu Judge phải trích dẫn lại đoạn văn đó trong phần "reason".

Một điều ngạc nhiên khác là sự khác biệt giữa **Context Recall** và **Completeness**. Có những trường hợp retriever mang về 100% tài liệu đúng (Recall tuyệt đối), nhưng điểm Completeness vẫn thấp vì LLM generator đã tóm tắt quá mức và bỏ sót các điều kiện ngoại lệ quan trọng. Điều này giúp tôi nhận ra rằng một hệ thống RAG hoàn hảo đòi hỏi sự tối ưu đồng bộ ở cả hai khâu: Tìm kiếm phải đủ và Trình bày phải đầy.

---

## 4. Phân tích một câu hỏi trong scorecard (150-200 từ)

Tôi chọn phân tích câu hỏi **q09: "ERR-403-AUTH là lỗi gì và cách xử lý?"**

**Câu hỏi:** Đây là một "câu hỏi bẫy" với ID q09, mã lỗi này không hề tồn tại trong bộ tài liệu 5 file txt của nhóm. Mục tiêu là kiểm tra khả năng **Abstain (từ chối trả lời)** của hệ thống.

**Phân tích:**
- **Kết quả Baseline (Dense):** Baseline đã rất xuất sắc khi trả lời: "Tôi không tìm thấy thông tin về lỗi ERR-403-AUTH trong tài liệu được cung cấp". Điểm Faithfulness đạt 5/5. Tuy nhiên, điểm Relevance chỉ đạt 1/5 và Completeness đạt 1/5 vì theo rubric, việc không trả lời được vấn đề người dùng hỏi (dù là do thiếu dữ liệu) thì điểm về nội dung sẽ thấp.
- **Lỗi ở đâu?** Thực tế đây không phải lỗi của hệ thống mà là một tính năng an toàn. Nó cho thấy pipeline của chúng ta không bị **Hallucination** (ảo giác).
- **Variant (Hybrid) có cải thiện không?** Variant Hybrid cũng cho kết quả tương tự. Điều thú vị là ở bản Hybrid, trong phần giải thích của Judge, Judge đã nhận xét rằng: "Hệ thống đã thực hiện tra cứu từ khóa ERR-403-AUTH nhưng không có kết quả khớp, việc từ chối trả lời là hành động đúng đắn nhất để đảm bảo tính trung thực". Điều này khẳng định rằng cả hai phiên bản đều đạt được mục tiêu "Grounding" - yếu tố tiên quyết trong các ứng dụng RAG cho doanh nghiệp.

---

## 5. Nếu có thêm thời gian, tôi sẽ làm gì? (50-100 từ)

Nếu có thêm thời gian, tôi muốn triển khai **Human-in-the-loop Evaluation**. Mặc dù LLM-as-Judge rất nhanh, nhưng đôi khi nó vẫn bỏ lỡ các sắc thái văn hóa hoặc ngữ cảnh nghiệp vụ đặc thù của công ty. Tôi sẽ xây dựng một giao diện đơn giản để chuyên gia (SME) có thể "audit" (kiểm tra lại) các điểm số mà LLM đã chấm, từ đó tạo ra một bộ dữ liệu vàng (Golden Dataset) có độ tin cậy tuyệt đối để fine-tune pipeline trong tương lai.

---
