import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL", "models/gemini-2.0-flash") # Fallback to 2.0 flash

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def run(state: dict) -> dict:
    """Synthesis Worker: Generates a grounded answer with citations."""
    task = state["task"]
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})
    
    # Prepare context
    context_str = ""
    for i, chunk in enumerate(chunks, 1):
        context_str += f"DOC [{i}]: {chunk['source']}\nCONTENT: {chunk['text']}\n\n"
    
    if policy_result:
        context_str += f"SYSTEM STATUS: Policy Check '{policy_result.get('policy_name')}'\n"
        context_str += f"POLICY APPLIES: {'YES' if policy_result.get('policy_applies') else 'NO'}\n"
        for ex in policy_result.get("exceptions_found", []):
            context_str += f"EXCEPTION FOUND: {ex['type']} - {ex['rule']} (Source: {ex['source']})\n"

    prompt = f"""
Bạn là một trợ lý ảo hỗ trợ CS + IT Helpdesk chuyên nghiệp.
Nhiệm vụ: Trả lời câu hỏi của người dùng dựa TRÊN context được cung cấp bên dưới.
Quy tắc:
1. KHÔNG được dùng kiến thức ngoài context.
2. NẾU context không có câu trả lời, hãy nói: "Tôi không tìm thấy thông tin cụ thể trong tài liệu nội bộ."
3. TRÍCH DẪN số thứ tự tài liệu dưới dạng [1], [2]... hoặc [tên_file] ngay sau thông tin được lấy.
4. Trả lời bằng tiếng Việt, súc tích, chuyên nghiệp.

CONTEXT:
{context_str}

USER TASK: {task}

ANSWER:
"""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        # Add timeout to avoid hanging
        response = model.generate_content(prompt, request_options={"timeout": 30})
        final_answer = response.text.strip()
    except Exception as e:
        print(f"  [synthesis] Gemini failed or timed out: {e}. Using rule-based fallback.")
        # Rule-based fallback synthesis
        if chunks:
            final_answer = f"Dựa trên tài liệu [{chunks[0]['source']}], thông tin cho biết: {chunks[0]['text'][:200]}..."
        else:
            final_answer = "Tôi không tìm thấy thông tin cụ thể trong tài liệu nội bộ."

    # Basic confidence scoring
    confidence = 0.5
    if chunks:
        confidence = 0.9
    if "không tìm thấy" in final_answer.lower():
        confidence = 0.3
    if not GOOGLE_API_KEY:
        confidence = 0.0
        final_answer = "MISSING GOOGLE_API_KEY. Cannot synthesize answer."

    return {
        "final_answer": final_answer,
        "sources": state.get("retrieved_sources", []),
        "confidence": confidence,
        "history": [f"[synthesis_worker] generated answer (conf={confidence})"],
        "workers_called": ["synthesis_worker"]
    }

if __name__ == "__main__":
    # Test
    test_state = {
        "task": "SLA xử lý ticket P1?",
        "retrieved_chunks": [
            {"text": "SLA P1: phản hồi 15p, xử lý 4h.", "source": "sla_p1_2026.txt"},
            {"text": "Escalation occurs after 2h of no movement.", "source": "sla_p1_2026.txt"}
        ],
        "retrieved_sources": ["sla_p1_2026.txt"],
        "policy_result": {}
    }
    result = run(test_state)
    print(f"Confidence: {result['confidence']}")
    print(f"Answer:\n{result['final_answer']}")
