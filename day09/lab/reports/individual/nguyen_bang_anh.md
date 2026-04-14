# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Bằng Anh  
**Vai trò trong nhóm:** Worker Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ  

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi chịu trách nhiệm về "trái tim tri thức" của hệ thống - các Worker Agents. Công việc của tôi tập trung vào việc hiện thực hóa các chức năng cụ thể mà Supervisor yêu cầu:
- **`workers/retrieval.py`**: Xây dựng hệ thống tìm kiếm thông tin từ Knowledge Base.
- **`workers/policy_tool.py`**: Triển khai logic kiểm tra chính sách và tích hợp MCP tools.
- **`workers/synthesis.py`**: Thiết kế prompt để LLM (Gemini 2.0) tổng hợp câu trả lời cuối cùng.
- **`contracts/worker_contracts.yaml`**: Định nghĩa chuẩn giao tiếp (input/output) cho tất cả các workers.

Nhiệm vụ của tôi là đảm bảo kết quả trả về cho user phải **Grounded** (dựa trên tài liệu) và tuân thủ đúng các business rules (ví dụ: sản phẩm Flash Sale không được hoàn tiền).

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Triển khai **Robust Keyword Fallback** trong Retrieval Worker để thay thế cho Semantic Search khi gặp lỗi môi trường.

**Lý do:**
Trong quá trình phát hành Sprint 2, tôi nhận thấy môi trường lab rất không ổn định với Qdrant local. Thường xuyên xảy ra lỗi `storage.sqlite locked` hoặc model embedding `all-MiniLM-L6-v2` tải quá chậm gây timeout.

Tôi quyết định không chỉ sửa lỗi (error handling) mà còn viết một logic tìm kiếm dự phòng:
- Ưu tiên gọi Qdrant để lấy semantic context.
- Nếu Qdrant trả về lỗi hoặc timeout, hệ thống tự động quét trực tiếp nội dung các file `.txt` trong `data/docs/` bằng giải thuật keyword matching đơn giản.

**Bằng chứng:**
Code trong `workers/retrieval.py`:
```python
except Exception as e:
    print(f"  [retrieval] Qdrant failed: {e}. Falling back to keyword search.")
    # logic scan files directly
```
Quyết định này "cứu" nhóm khỏi việc bị treo pipeline trong lúc evaluation (q01-q15). Dù độ chính xác có thể giảm nhẹ nhưng Success Rate của pipeline đạt 100%.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** **Synthesis Worker bị Hallucination (bịa đặt thông tin) khi tài liệu không có câu trả lời.**

**Symptom:** Với câu hỏi `gq07` (về mức phạt tài chính vi phạm SLA P1), tài liệu không hề nhắc tới con số cụ thể. Tuy nhiên, model thỉnh thoảng tự bịa ra con số 5% hoặc 10% để trả lời user.

**Root cause:** 
Prompt ban đầu của tôi quá mở, yêu cầu model "hãy giúp đỡ người dùng hết sức có thể". Điều này khiến LLM cố gắng suy luận từ kiến thức ngoại cảnh khi Context rỗng.

**Cách sửa:**
- Tôi đã cập nhật lại System Prompt trong `synthesis.py` với các quy tắc cực kỳ khắt khe (Grounded RAG rules).
- Thêm câu lệnh: "Nếu context không có thông tin, bắt buộc nói 'Tôi không tìm thấy thông tin cụ thể' và KHÔNG được dùng kiến thức ngoài."
- Triển khai logic check `confidence`: Nếu Retrieval trả về 0 chunks, Synthesis sẽ tự động set confidence xuống 0.3 và trả về thông báo Abstain.

**Bằng chứng:** Sau khi cập nhật, trace [run_20260414_145006.json] cho thấy systems đã trả lời đúng yêu cầu "Abstain" của SCORING.md cho câu gq07.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Khả năng viết code ổn định (robust code). Các workers của tôi luôn có exception handling tốt, đảm bảo graph không bao giờ bị crash giữa chừng.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Kỹ năng Prompt Engineering của tôi còn cần cải thiện để model trích dẫn nguồn (citation) mượt mà hơn, thay vì chỉ chèn [1] ở cuối câu.

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu workers của tôi không trả về dữ liệu đúng contract, Supervisor của Anh sẽ route đúng nhưng người dùng vẫn nhận được thông tin sai hoặc rác.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ nâng cấp logic trong `policy_tool.py` để sử dụng **Reranker** (như BGE-Reranker) giúp lọc lại 10 chunks tìm được từ Retrieval, nhằm đảm bảo chỉ những thông tin policy thực sự liên quan nhất mới được đưa vào Synthesis.

---
*Lưu tại: `reports/individual/nguyen_bang_anh.md`*
