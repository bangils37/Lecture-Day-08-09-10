# Single Agent vs Multi-Agent Comparison — Lab Day 09

Dữ liệu trong file này được điền trực tiếp từ `artifacts/eval_report.json`.

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Ghi chú |
|--------|------------------------|----------------------|---------|
| Total questions/traces | 15 | 157 traces | Day 08 là baseline theo câu hỏi, Day 09 là tổng trace đã chạy |
| Avg confidence | 0.0 | 0.589 | Day 08 chưa có confidence thực nghiệm để so sánh công bằng |
| Avg latency (ms) | 0 | 8495 | Day 08 trong eval_report chưa có số đo latency |
| Abstain rate | ? | Không có field trực tiếp | Cần bổ sung evaluator per-question |
| Multi-hop accuracy | ? | Không có field trực tiếp | Cần benchmark theo rubric grading |
| Routing visibility | Không có | Có `route_reason` từng câu | Theo phần `analysis.routing_visibility` |
| MCP usage rate | N/A | 34/157 (21%) | Day 09 có external tools qua MCP |
| HITL rate | N/A | 9/157 (5%) | Day 09 có nhánh human_review |

## 2. Nhận xét theo eval_report

### 2.1 Điểm mạnh của Day 09

1. **Debuggability cao hơn**: `eval_report.analysis.debuggability` ghi rõ Day 09 có thể test từng worker độc lập, trong khi Day 08 không làm được.
2. **Quan sát routing tốt hơn**: có `route_reason` cho từng truy vấn, giúp truy vết lý do supervisor chọn worker.
3. **Mở rộng tốt hơn với MCP**: `analysis.mcp_benefit` xác nhận có thể thêm capability qua MCP mà không sửa core orchestration.

### 2.2 Hạn chế hiện tại của so sánh

1. Day 08 trong eval_report chưa có số đo thực tế (`avg_confidence=0.0`, `avg_latency_ms=0`, abstain/multi-hop là `?`).
2. Chưa có accuracy delta định lượng vì `analysis.accuracy_delta` còn TODO.
3. Chưa có latency delta định lượng vì `analysis.latency_delta` còn TODO.

## 3. Source Coverage Insight (Day 09)

Top tài liệu được sử dụng nhiều nhất trong multi-agent runtime:

1. `policy_refund_v4.txt` — 92 lượt
2. `access_control_sop.txt` — 70 lượt
3. `sla_p1_2026.txt` — 57 lượt
4. `it_helpdesk_faq.txt` — 25 lượt
5. `hr_leave_policy.txt` — 9 lượt

Insight: workload đang tập trung mạnh vào nhóm câu Refund + Access + SLA, phù hợp với tỷ lệ route đáng kể sang `policy_tool_worker` (45%).

## 4. Kết luận tạm thời

- Day 09 vượt trội Day 08 về **kiến trúc vận hành**: traceability, khả năng tách worker để debug, và khả năng mở rộng tool qua MCP.
- Với số liệu hiện tại, chưa thể kết luận chính xác mức tăng/giảm về **accuracy** và **latency delta** giữa Day 08 và Day 09 vì baseline Day 08 trong eval_report còn thiếu.
- Bước tiếp theo để hoàn tất so sánh là thu thập lại baseline Day 08 cùng bộ câu hỏi và cùng format metrics.

---
*Lưu tại: `docs/single_vs_multi_comparison.md`*