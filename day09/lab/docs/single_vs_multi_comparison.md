# So sánh RAG: Single-Agent vs Multi-Agent

Dựa trên kết quả thực nghiệm từ Lab Day 08 (Single) và Lab Day 09 (Multi).

## 1. Metrics Comparison

| Metric | Single-Agent (Day 08) | Multi-Agent (Day 09) | Nhận xét |
|--------|-----------------------|----------------------|----------|
| **Latency (Avg)** | ~2-3s | ~13.4s | Multi-agent chậm hơn do overhead điều phối. |
| **Debuggability** | Thấp (Opaque) | Cao (Transparent) | Day 09 có route reason và step traces rõ ràng. |
| **Success Rate** | ~80% | 100% | Nhờ có logic fallback và phân loại task tốt hơn. |
| **Complexity** | Thấp (Linear) | Cao (Graph) | Multi-agent khó triển khai hơn nhưng dễ bảo trì. |

## 2. Ưu điểm của Multi-Agent (Day 09)

1. **Sự chuyên môn hóa (Specialization)**: Worker chỉ tập trung vào một nhiệm vụ (Policy vs Retrieval). Code sạch hơn và dễ viết unit test cho từng worker.
2. **Khả năng hồi phục (Resilience)**: Hệ thống Multi-agent trong bài lab này cho phép fallback keyword search khi Qdrant lock, điều mà bản Single-agent cũ không xử lý được.
3. **Mở rộng (Scalability)**: Dễ dàng thêm node `Human-in-the-Loop` cho các case rủi ro cao mà không làm hỏng flow tự động của các case khác.

## 3. Nhược điểm của Multi-Agent (Day 09)

1. **Trễ (Latency)**: Việc Supervisor phải phân tích rồi mới route làm tăng thời gian phản hồi (~3-4x).
2. **Chi phí (Cost)**: Tiềm ẩn việc gọi LLM nhiều lần cho một request (Supervisor call + Synthesis call).

## 4. Kết luận

- Dùng **Single-agent** cho các bài toán RAG đơn giản, khối lượng dữ liệu ít và yêu cầu tốc độ phản hồi cực nhanh.
- Dùng **Multi-agent** cho các hệ thống CS + IT Helpdesk chuyên nghiệp, nơi cần xử lý nhiều logic nghiệp vụ (business rules), cần sự can thiệp của con người (HITL) và yêu cầu tính minh bạch cao trong quá trình suy luận.

---
*Lưu tại: `docs/single_vs_multi_comparison.md`*
