# Báo Cáo Cá Nhân — Lab Day 10

**Họ và tên:** Nguyen Bằng Anh 
**MSSV:** 2A202600136
**Vai trò:** Embed Owner  
**Ngày:** 2026-04-15  

---

## 1. Phần phụ trách cụ thể

Trong bài Lab Day 10, tôi đảm nhận vai trò **Embed Owner** và chịu trách nhiệm chính về Vector Store. Công việc chính của tôi bao gồm:
- Thiết lập và quản lý collection `day10_kb` trên Chroma DB (hoặc Qdrant theo cấu hình).
- Triển khai cơ chế **Idempotent Embed**: Sử dụng `upsert` theo `chunk_id` và thêm logic **Pruning** để xóa bỏ các vector cũ không còn xuất hiện trong bộ dữ liệu cleaned mới nhất.
- Thực hiện và đánh giá kết quả retrieval thông qua `eval_retrieval.py`, cung cấp bằng chứng định lượng cho nhóm về chất lượng dữ liệu.
- Phối hợp với Ingestion Owner để tích hợp `run_id` vào metadata của mỗi chunk.

## 2. Một quyết định kỹ thuật tiêu biểu

Tôi đã quyết định sử dụng strategy **Snapshot Publish (Delete-before-Upsert logic)** thay vì chỉ `upsert` đơn thuần.
**Lý do**: Nếu chỉ `upsert`, các vector cũ (stale) từ các run trước đó sẽ vẫn tồn tại trong database nếu `chunk_id` của chúng thay đổi hoặc không còn trong file cleaned mới. Điều này gây ra hiện tượng "nhiễu" kết quả tìm kiếm (retrieval noise). Việc xóa (prune) các ID không có trong bộ cleaned mới nhất giúp collection luôn phản ánh đúng trạng thái "Source of Truth" của pipeline hiện tại, triệt tiêu hoàn toàn rủi ro Agent trả lời dựa trên thông tin cũ.

## 3. Một sự cố / anomaly đã xử lý

**Phát hiện**: Khi chạy Sprint 3 với kịch bản inject dữ liệu bẩn (`--no-refund-fix`), kết quả `eval_retrieval.py` cho thấy `hits_forbidden=yes` dù top-1 có vẻ đúng. 
**Fix**: Tôi đã thực hiện xóa (prune) 1 record cũ và `upsert` lại dữ liệu chuẩn. Sau đó, tôi chạy lại pipeline chuẩn và xác nhận `hits_forbidden` đã về `no`.
**Evidence**: Log pipeline in ra: `embed_prune_removed=1` và `embed_upsert count=6`, chứng minh logic pruning đã hoạt động hiệu quả để dọn dẹp dữ liệu stale.

## 4. Bằng chứng Before / After

Kết quả eval sau khi fix refund window:
```csv
question_id,question,top1_preview,hits_forbidden
q_refund_window,Khách hàng có bao nhiêu ngày...?,...7 ngày làm việc...,no
```
Kết quả eval khi inject dữ liệu bẩn:
```csv
question_id,question,top1_preview,hits_forbidden
q_refund_window,Khách hàng có bao nhiêu ngày...?,...7 ngày làm việc...,yes
```

## 5. Cải tiến trong 2 giờ tới

Nếu có thêm 2 giờ, tôi sẽ triển khai **Reranker (như BGE-Reranker)** sau bước retrieval. Hiện tại chúng tôi mới chỉ dùng retrieval thô (top-k cosine similarity). Việc có thêm một layer reranker sẽ giúp tinh lọc kết quả tìm kiếm dựa trên ngữ nghĩa sâu hơn, đặc biệt hữu ích khi có nhiều chính sách tương tự nhau (ví dụ: các bản cập nhật policy refund qua từng năm) để luôn ưu tiên bản mới nhất cho Agent.
