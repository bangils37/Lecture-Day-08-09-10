"""
graph.py — Supervisor Orchestrator
Sprint 1: Implement AgentState, supervisor_node, route_decision và kết nối graph.

Kiến trúc:
    Input → Supervisor → [retrieval_worker | policy_tool_worker | human_review] → synthesis → Output

Chạy thử:
    python graph.py
"""

import json
import os
import time
import operator
import sys
from datetime import datetime
from typing import TypedDict, Literal, Optional, List, Annotated, Union

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

# ─────────────────────────────────────────────
# 1. Shared State — dữ liệu đi xuyên toàn graph
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    # Input
    task: str                           # Câu hỏi đầu vào từ user

    # Supervisor decisions
    route_reason: str                   # Lý do route sang worker nào
    risk_high: bool                     # True → cần HITL hoặc human_review
    needs_tool: bool                    # True → cần gọi external tool qua MCP
    hitl_triggered: bool                # True → đã pause cho human review

    # Worker outputs
    retrieved_chunks: List[dict]        # Output từ retrieval_worker
    retrieved_sources: List[str]        # Danh sách nguồn tài liệu
    policy_result: dict                 # Output từ policy_tool_worker
    mcp_tools_used: List[dict]          # Danh sách MCP tools đã gọi

    # Final output
    final_answer: str                   # Câu trả lời tổng hợp
    sources: List[str]                  # Sources được cite
    confidence: float                   # Mức độ tin cậy (0.0 - 1.0)

    # Trace & history
    history: Annotated[List[str], operator.add]      # Lịch sử các bước đã qua (append)
    workers_called: Annotated[List[str], operator.add] # Danh sách workers đã được gọi (append)
    supervisor_route: str               # Worker được chọn bởi supervisor
    latency_ms: Optional[int]           # Thời gian xử lý (ms)
    run_id: str                         # ID của run này


def make_initial_state(task: str) -> AgentState:
    """Khởi tạo state cho một run mới."""
    return {
        "task": task,
        "route_reason": "",
        "risk_high": False,
        "needs_tool": False,
        "hitl_triggered": False,
        "retrieved_chunks": [],
        "retrieved_sources": [],
        "policy_result": {},
        "mcp_tools_used": [],
        "final_answer": "",
        "sources": [],
        "confidence": 0.0,
        "history": [],
        "workers_called": [],
        "supervisor_route": "",
        "latency_ms": None,
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    }


# ─────────────────────────────────────────────
# 2. Supervisor Node — quyết định route
# ─────────────────────────────────────────────

def supervisor_node(state: AgentState) -> dict:
    """
    Supervisor phân tích task và quyết định route.
    """
    task = state["task"].lower()
    
    # Simple keyword-based routing (Sprint 1)
    route = "retrieval_worker"
    route_reason = "default route"
    needs_tool = False
    risk_high = False

    policy_keywords = ["hoàn tiền", "refund", "flash sale", "license", "cấp quyền", "access", "level 3"]
    risk_keywords = ["emergency", "khẩn cấp", "2am", "không rõ", "err-"]

    if any(kw in task for kw in policy_keywords):
        route = "policy_tool_worker"
        route_reason = "task contains policy/access keyword"
        needs_tool = True

    if any(kw in task for kw in risk_keywords):
        risk_high = True
        route_reason += " | risk_high flagged"

    if risk_high and "err-" in task:
        route = "human_review"
        route_reason = "unknown error code + risk_high → human review"

    return {
        "supervisor_route": route,
        "route_reason": route_reason,
        "needs_tool": needs_tool,
        "risk_high": risk_high,
        "history": [f"[supervisor] route={route} reason={route_reason}"]
    }


# ─────────────────────────────────────────────
# 3. Route Decision — conditional edge
# ─────────────────────────────────────────────

def route_decision(state: AgentState) -> Literal["retrieval_worker", "policy_tool_worker", "human_review"]:
    """Conditional edge logic."""
    return state.get("supervisor_route", "retrieval_worker")


# ─────────────────────────────────────────────
# 4. Human Review Node — HITL placeholder
# ─────────────────────────────────────────────

def human_review_node(state: AgentState) -> dict:
    """HITL node placeholder."""
    print(f"\n[HITL TRIGGERED] for task: {state['task']}")
    return {
        "hitl_triggered": True,
        "workers_called": ["human_review"],
        "history": ["[human_review] HITL triggered — auto-approving"],
        "supervisor_route": "retrieval_worker", # Route back to retrieval after approval
    }


# ─────────────────────────────────────────────
# 5. Import Workers
# ─────────────────────────────────────────────

from workers.retrieval import run as retrieval_run
from workers.policy_tool import run as policy_tool_run
from workers.synthesis import run as synthesis_run

def retrieval_worker_node(state: AgentState) -> dict:
    """Wrapper calling retrieval worker."""
    result = retrieval_run(state)
    return result

def policy_tool_worker_node(state: AgentState) -> dict:
    """Wrapper calling policy worker."""
    result = policy_tool_run(state)
    return result

def synthesis_worker_node(state: AgentState) -> dict:
    """Wrapper calling synthesis worker."""
    result = synthesis_run(state)
    return result


# ─────────────────────────────────────────────
# 6. Build Graph
# ─────────────────────────────────────────────

def build_graph():
    """Build the LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # Define nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("retrieval_worker", retrieval_worker_node)
    workflow.add_node("policy_tool_worker", policy_tool_worker_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("synthesis_worker", synthesis_worker_node)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional edges from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "retrieval_worker": "retrieval_worker",
            "policy_tool_worker": "policy_tool_worker",
            "human_review": "human_review"
        }
    )

    # Extra routing logic
    workflow.add_edge("human_review", "retrieval_worker")
    workflow.add_edge("policy_tool_worker", "retrieval_worker") # Often need retrieval after policy check or vice versa
    workflow.add_edge("retrieval_worker", "synthesis_worker")
    workflow.add_edge("synthesis_worker", END)

    return workflow.compile()


# ─────────────────────────────────────────────
# 7. Public API
# ─────────────────────────────────────────────

_graph = build_graph()


def run_graph(task: str) -> AgentState:
    """Entry point."""
    state = make_initial_state(task)
    start_time = time.time()
    
    # LangGraph invoke
    result = _graph.invoke(state)
    
    result["latency_ms"] = int((time.time() - start_time) * 1000)
    result["history"].append(f"[graph] completed in {result['latency_ms']}ms")
    return result


def save_trace(state: AgentState, output_dir: str = "./artifacts/traces") -> str:
    """Lưu trace ra file JSON."""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{state['run_id']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        # Convert state to dict and handle Annotated lists
        json.dump(dict(state), f, ensure_ascii=False, indent=2)
    return filename


# ─────────────────────────────────────────────
# 8. Manual Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Day 09 Lab — Supervisor-Worker Graph (LangGraph)")
    print("=" * 60)

    test_queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
        "Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?",
        "Gửi mã lỗi ERR-999 khẩn cấp cho admin.",
    ]

    for query in test_queries:
        print(f"\n[QUERY]: {query}")
        result = run_graph(query)
        print(f"  Route   : {result['supervisor_route']}")
        print(f"  Reason  : {result['route_reason']}")
        print(f"  Workers : {result['workers_called']}")
        print(f"  Answer  : {result['final_answer']}")
        print(f"  Latency : {result['latency_ms']}ms")

        trace_file = save_trace(result)
        print(f"  Trace saved → {trace_file}")

    print("\n✅ Sprint 1 complete. LangGraph setup verified.")
