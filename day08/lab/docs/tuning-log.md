# Tuning Log — RAG Pipeline (Day 08 Lab)

> Template: Ghi lại mỗi thay đổi và kết quả quan sát được.
> A/B Rule: Chỉ đổi MỘT biến mỗi lần.

---

## Baseline (Sprint 2)

**Ngày:** 2026-04-13  
**Config:**
```
retrieval_mode = "dense"
chunk_size = 500 characters (paragraph based)
overlap = 100 characters
top_k_search = 10
top_k_select = 3
use_rerank = False
llm_model = gemini-1.5-flash
```

**Scorecard Baseline:**
| Metric | Average Score |
|--------|--------------|
| Faithfulness | 4.70 /5 |
| Answer Relevance | 3.40 /5 |
| Context Recall | 5.00 /5 |
| Completeness | 3.70 /5 |

**Câu hỏi yếu nhất (điểm thấp):**
> TODO: Liệt kê 2-3 câu hỏi có điểm thấp nhất và lý do tại sao.
> Ví dụ: "q07 (Approval Matrix) - context recall = 1/5 vì dense bỏ lỡ alias."

**Giả thuyết nguyên nhân (Error Tree):**
- [ ] Indexing: Chunking cắt giữa điều khoản
- [ ] Indexing: Metadata thiếu effective_date
- [ ] Retrieval: Dense bỏ lỡ exact keyword / alias
- [ ] Retrieval: Top-k quá ít → thiếu evidence
- [ ] Generation: Prompt không đủ grounding
- [ ] Generation: Context quá dài → lost in the middle

---

## Variant 1 (Sprint 3)

**Ngày:** 2026-04-13  
**Biến thay đổi:** Hybrid Retrieval (Dense + BM25) với RRF  
**Lý do chọn biến này:**
- Dense retrieval có thể bỏ lỡ các từ khóa chính xác (mã lỗi như ERR-403) nếu embedding không nhạy bén với các chuỗi ký tự đặc biệt.
- Hybrid giúp kết hợp thế mạnh của semantic search (ý nghĩa) và keyword search (từ khóa chính xác).
- RRF (Reciprocal Rank Fusion) cung cấp cách kết hợp kết quả từ 2 phương pháp mà không cần chuẩn hóa scale điểm số khác nhau.

**Config thay đổi:**
```
retrieval_mode = "hybrid"
top_k_search = 10
top_k_select = 3
# Thêm BM25 index pre-computed
```

**Scorecard Variant 1:**
| Metric | Baseline | Variant 1 | Delta |
|--------|----------|-----------|-------|
| Faithfulness | 4.70/5 | 5.00/5 | +0.30 |
| Answer Relevance | 3.40/5 | 3.30/5 | -0.10 |
| Context Recall | 5.00/5 | 5.00/5 | 0.00 |
| Completeness | 3.70/5 | 3.80/5 | +0.10 |

**Nhận xét:**
- Variant 1 (Hybrid) cải thiện Faithfulness lên 5.0, giúp model bám sát context tốt hơn.
- Context Recall đạt mức tối đa ở cả 2 bản, cho thấy tập dữ liệu nhỏ giúp việc tìm kiếm khá dễ dàng.
- Tuy nhiên, Answer Relevance giảm nhẹ, có thể do việc đưa thêm các chunk từ BM25 làm loãng context cho LLM ở một số câu hỏi tự nhiên.

**Kết luận:**
- Hybrid Retrieval tốt hơn trong việc đảm bảo tính trung thực (Faithfulness) do BM25 giúp confirm các keyword quan trọng.
- Cho tập dữ liệu này, Hybrid là một lựa chọn an toàn để cân bằng giữa semantic và keyword search.

---

## Variant 2 (nếu có thời gian)

**Biến thay đổi:** ___________  
**Config:**
```
# TODO
```

**Scorecard Variant 2:**
| Metric | Baseline | Variant 1 | Variant 2 | Best |
|--------|----------|-----------|-----------|------|
| Faithfulness | ? | ? | ? | ? |
| Answer Relevance | ? | ? | ? | ? |
| Context Recall | ? | ? | ? | ? |
| Completeness | ? | ? | ? | ? |

---

## Tóm tắt học được

> TODO (Sprint 4): Điền sau khi hoàn thành evaluation.

1. **Lỗi phổ biến nhất trong pipeline này là gì?**
   > _____________

2. **Biến nào có tác động lớn nhất tới chất lượng?**
   > _____________

3. **Nếu có thêm 1 giờ, nhóm sẽ thử gì tiếp theo?**
   > _____________
