"""
workers/synthesis.py — Synthesis Worker
Sprint 2: Tổng hợp câu trả lời từ retrieved_chunks và policy_result.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: evidence từ retrieval_worker
    - policy_result: kết quả từ policy_tool_worker

Output (vào AgentState):
    - final_answer: câu trả lời cuối với citation
    - sources: danh sách nguồn tài liệu được cite
    - confidence: mức độ tin cậy (0.0 - 1.0)

Gọi độc lập để test:
    python workers/synthesis.py
"""

import os

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là trợ lý IT Helpdesk nội bộ.

Quy tắc nghiêm ngặt:
1. CHỈ trả lời dựa vào context được cung cấp. KHÔNG dùng kiến thức ngoài.
2. Nếu context không đủ để trả lời → nói rõ "Không đủ thông tin trong tài liệu nội bộ".
3. Trích dẫn nguồn cuối mỗi câu quan trọng: [tên_file].
4. Trả lời súc tích, có cấu trúc. Không dài dòng.
5. Nếu có exceptions/ngoại lệ → nêu rõ ràng trước khi kết luận.
"""


def _call_llm(messages: list) -> str:
    """
    Gọi LLM để tổng hợp câu trả lời.
    Thứ tự cố gắng: Mock (for testing) → Gemini → OpenAI → Error
    """
    # Option 0: Mock LLM (cho Sprint 2 testing — comment nếu muốn thật)
    use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
    if use_mock:
        return _mock_llm_grounded(messages)

    # Option B: Gemini (thực tế)
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        combined = "\n".join([m["content"] for m in messages])
        response = model.generate_content(combined)
        return response.text
    except Exception as e:
        pass

    # Option A: OpenAI (thực tế)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  # Low temperature để grounded
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        pass

    # Fallback: trả về message báo lỗi (không hallucinate)
    return "[SYNTHESIS ERROR] Không thể gọi LLM. Kiểm tra API key trong .env."


def _mock_llm_grounded(messages: list) -> str:
    """
    Mock LLM cho Sprint 2 testing — tách câu hỏi và context, trả lời dựa vào context.
    
    Không hallucinate: nếu context không đủ → abstain.
    """
    if not messages:
        return "[Mock: No messages provided]"
    
    # Lấy user message (thường là cuối cùng hoặc role=='user')
    user_msg = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_msg = msg.get("content", "")
            break
    
    if not user_msg:
        return "[Mock: No user message found]"
    
    # Check if context section exists
    has_context = "TÀI LIỆU THAM KHẢO" in user_msg or "Nguồn:" in user_msg
    
    # Extract context section (between headers or entire context)
    context_length = len(user_msg.split("Hãy trả lời")[0]) if "Hãy trả lời" in user_msg else len(user_msg)
    
    # If context is very short or marked as "(Không có context)", abstain
    if ("Không có context" in user_msg or 
        (not has_context) or 
        context_length < 80):
        return "Không đủ thông tin trong tài liệu nội bộ để trả lời câu hỏi này."
    
    # Context exists, generate grounded answer based on detected topics
    if "P1" in user_msg and ("SLA" in user_msg or "sla_p1_2026.txt" in user_msg):
        return "Dựa vào tài liệu SLA P1 được cung cấp, ticket P1 có các yêu cầu xử lý theo tiêu chuẩn SLA. Liên hệ IT Support để biết chi tiết. [Nguồn: sla_p1_2026.txt]"
    
    if "refund" in user_msg.lower() or "hoàn tiền" in user_msg.lower():
        if "Flash Sale" in user_msg or "flash sale" in user_msg.lower():
            return "Flash Sale orders có các ngoại lệ riêng trong chính sách hoàn tiền. Cần kiểm tra điều kiện cụ thể của đơn hàng. [Nguồn: policy_refund_v4.txt]"
        return "Quy trình hoàn tiền tuân theo chính sách v4. Vui lòng kiểm tra điều kiện và ngoại lệ áp dụng cho trường hợp cụ thể. [Nguồn: policy_refund_v4.txt]"
    
    if "cấp quyền" in user_msg.lower() or "access" in user_msg.lower() or "access_control" in user_msg:
        return "Cấp quyền truy cập cần tuân theo Access Control SOP. Quy trình bao gồm kiểm tra, phê duyệt, và training. Liên hệ IT để bắt đầu. [Nguồn: access_control_sop.txt]"
    
    if "hr_leave" in user_msg or "remote" in user_msg.lower() or "leave" in user_msg.lower():
        return "Chính sách HR chi tiết được cung cấp. Vui lòng liên hệ HR department để được hỗ trợ cụ thể. [Nguồn: hr_leave_policy.txt]"
    
    if "helpdesk" in user_msg or "faq" in user_msg or "it_helpdesk" in user_msg:
        return "Thông tin được cung cấp từ IT Helpdesk FAQ. Liên hệ IT Support nếu cần hỗ trợ thêm. [Nguồn: it_helpdesk_faq.txt]"
    
    # Generic answer when context exists
    if has_context:
        return "Câu hỏi này được trả lời dựa vào tài liệu nội bộ. Vui lòng kiểm tra chi tiết trong tài liệu tham khảo."
    
    return "Không đủ thông tin trong tài liệu nội bộ để trả lời câu hỏi này."


def _build_context(chunks: list, policy_result: dict) -> str:
    """Xây dựng context string từ chunks và policy result."""
    parts = []

    if chunks:
        parts.append("=== TÀI LIỆU THAM KHẢO ===")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            parts.append(f"[{i}] Nguồn: {source} (relevance: {score:.2f})\n{text}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("\n=== POLICY EXCEPTIONS ===")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"- {ex.get('rule', '')}")

    if not parts:
        return "(Không có context)"

    return "\n\n".join(parts)


def _estimate_confidence(chunks: list, answer: str, policy_result: dict) -> float:
    """
    Ước tính confidence dựa vào:
    - Số lượng và quality của chunks
    - Có exceptions không
    - Answer có abstain không

    TODO Sprint 2: Có thể dùng LLM-as-Judge để tính confidence chính xác hơn.
    """
    if not chunks:
        return 0.1  # Không có evidence → low confidence

    if "Không đủ thông tin" in answer or "không có trong tài liệu" in answer.lower():
        return 0.3  # Abstain → moderate-low

    # Weighted average của chunk scores
    if chunks:
        avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    else:
        avg_score = 0

    # Penalty nếu có exceptions (phức tạp hơn)
    exception_penalty = 0.05 * len(policy_result.get("exceptions_found", []))

    confidence = min(0.95, avg_score - exception_penalty)
    return round(max(0.1, confidence), 2)


def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    """
    Tổng hợp câu trả lời từ chunks và policy context.

    Returns:
        {"answer": str, "sources": list, "confidence": float}
    """
    context = _build_context(chunks, policy_result)

    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""Câu hỏi: {task}

{context}

Hãy trả lời câu hỏi dựa vào tài liệu trên."""
        }
    ]

    answer = _call_llm(messages)
    sources = list({c.get("source", "unknown") for c in chunks})
    confidence = _estimate_confidence(chunks, answer, policy_result)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "has_policy": bool(policy_result),
        },
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]

        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
        }
        state["history"].append(
            f"[{WORKER_NAME}] answer generated, confidence={result['confidence']}, "
            f"sources={result['sources']}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(e)}
        state["final_answer"] = f"SYNTHESIS_ERROR: {e}"
        state["confidence"] = 0.0
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Synthesis Worker — Standalone Test")
    print("=" * 50)

    test_state = {
        "task": "SLA ticket P1 là bao lâu?",
        "retrieved_chunks": [
            {
                "text": "Ticket P1: Phản hồi ban đầu 15 phút kể từ khi ticket được tạo. Xử lý và khắc phục 4 giờ. Escalation: tự động escalate lên Senior Engineer nếu không có phản hồi trong 10 phút.",
                "source": "sla_p1_2026.txt",
                "score": 0.92,
            }
        ],
        "policy_result": {},
    }

    result = run(test_state.copy())
    print(f"\nAnswer:\n{result['final_answer']}")
    print(f"\nSources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")

    print("\n--- Test 2: Exception case ---")
    test_state2 = {
        "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì lỗi nhà sản xuất.",
        "retrieved_chunks": [
            {
                "text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền theo Điều 3 chính sách v4.",
                "source": "policy_refund_v4.txt",
                "score": 0.88,
            }
        ],
        "policy_result": {
            "policy_applies": False,
            "exceptions_found": [{"type": "flash_sale_exception", "rule": "Flash Sale không được hoàn tiền."}],
        },
    }
    result2 = run(test_state2.copy())
    print(f"\nAnswer:\n{result2['final_answer']}")
    print(f"Confidence: {result2['confidence']}")

    print("\n✅ synthesis_worker test done.")
