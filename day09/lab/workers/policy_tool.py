import os
import sys
from typing import Dict, List
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from mcp_server import dispatch_tool, list_tools
from datetime import datetime

def run(state: dict) -> dict:
    """
    Policy Tool Worker: Analyzes retrieved chunks for specific policy rules.
    Detects exceptions and calls MCP tools if needed.
    """
    task = state["task"].lower()
    chunks = state.get("retrieved_chunks", [])
    mcp_tools_used = []
    
    # Aggregated text from chunks for analysis
    context_text = " ".join([c["text"] for c in chunks]).lower()
    
    policy_result = {
        "policy_applies": False,
        "policy_name": "general_inquiry",
        "exceptions_found": [],
        "source": []
    }
    
    # --- MCP Tool Integration ---
    if state.get("needs_tool"):
        # 1. Access Permission Tool
        if "access" in task or "quyền" in task:
            level = 1
            if "level 3" in task: level = 3
            elif "level 2" in task: level = 2
            
            is_emergency = "khẩn cấp" in task or "emergency" in task
            
            mcp_res = dispatch_tool("check_access_permission", {
                "access_level": level,
                "requester_role": "employee", # Mock role
                "is_emergency": is_emergency
            })
            
            mcp_tools_used.append({
                "tool": "check_access_permission",
                "input": {"level": level, "emergency": is_emergency},
                "output": mcp_res,
                "timestamp": datetime.now().isoformat()
            })
            
            if "error" not in mcp_res:
                policy_result["policy_applies"] = mcp_res.get("can_grant", False)
                policy_result["policy_name"] = "access_control_sop"
                for note in mcp_res.get("notes", []):
                    policy_result["exceptions_found"].append({
                        "type": "mcp_permission_note",
                        "rule": note,
                        "source": mcp_res.get("source")
                    })

        # 2. Ticket Info Tool
        if "ticket" in task or "p1-" in task or "it-" in task:
            ticket_id = "P1-LATEST"
            if "it-1234" in task: ticket_id = "IT-1234"
            
            mcp_res = dispatch_tool("get_ticket_info", {"ticket_id": ticket_id})
            mcp_tools_used.append({
                "tool": "get_ticket_info",
                "input": {"ticket_id": ticket_id},
                "output": mcp_res,
                "timestamp": datetime.now().isoformat()
            })
            
            if "error" not in mcp_res:
                policy_result["policy_name"] = "ticket_system"
                policy_result["policy_applies"] = True
                policy_result["exceptions_found"].append({
                    "type": "ticket_info",
                    "rule": f"Status: {mcp_res.get('status')} | Assignee: {mcp_res.get('assignee')}",
                    "source": "jira_mcp"
                })

    # --- Traditional Chunk-based Logic (Fallback or Complement) ---
    # (Only run if MCP wasn't definitive or as additional evidence)
    
    # Refund Policy logic (No MCP tool for refund yet, use chunks)
    if any(kw in task for kw in ["hoàn tiền", "refund"]):
        policy_result["policy_name"] = "refund_policy_v4"
        
        # Standard rule check
        if "hoàn tiền" in context_text or "refund" in context_text:
            policy_result["policy_applies"] = True
            for c in chunks:
                if "refund" in c["text"].lower() or "hoàn tiền" in c["text"].lower():
                    if c["source"] not in policy_result["source"]:
                        policy_result["source"].append(c["source"])
        
        # Exception: Flash Sale
        if "flash sale" in task or "flash sale" in context_text:
            policy_result["exceptions_found"].append({
                "type": "flash_sale_exception",
                "rule": "Sản phẩm Flash Sale không được hoàn tiền trừ khi có lỗi kỹ thuật nặng.",
                "source": "policy_refund_v4.txt"
            })
            policy_result["policy_applies"] = False # Overridden
            
        # Exception: Digital Product
        if "digital" in task or "kỹ thuật số" in task:
            policy_result["exceptions_found"].append({
                "type": "digital_product_exception",
                "rule": "Sản phẩm kỹ thuật số (e-book, license) không được hoàn trả sau khi đã kích hoạt.",
                "source": "policy_refund_v4.txt"
            })
            policy_result["policy_applies"] = False

    # 2. Access Control SOP logic
    elif any(kw in task for kw in ["cấp quyền", "access", "quyền truy cập"]):
        policy_result["policy_name"] = "access_control_sop"
        
        if "quyền" in context_text or "access" in context_text:
            policy_result["policy_applies"] = True
            for c in chunks:
                if "access" in c["text"].lower() or "quyền" in c["text"].lower():
                    if c["source"] not in policy_result["source"]:
                        policy_result["source"].append(c["source"])

        # Emergency Check
        if "khẩn cấp" in task or "emergency" in task:
            policy_result["policy_applies"] = True
            policy_result["exceptions_found"].append({
                "type": "emergency_access",
                "rule": "Quy trình khẩn cấp cho phép cấp quyền tạm thời với approval từ Line Manager và IT Admin on-call.",
                "source": "access_control_sop.txt"
            })

    return {
        "policy_result": policy_result,
        "mcp_tools_used": mcp_tools_used,
        "history": [f"[policy_tool_worker] policy check complete: {policy_result['policy_name']}"],
        "workers_called": ["policy_tool_worker"]
    }

if __name__ == "__main__":
    # Test
    test_state = {
        "task": "Hoàn tiền cho sản phẩm Flash Sale",
        "retrieved_chunks": [
            {"text": "Chính sách hoàn tiền v4 áp dụng cho mọi hóa đơn.", "source": "policy_refund_v4.txt"},
            {"text": "Mục 4.2: Flash Sale không hoàn tiền.", "source": "policy_refund_v4.txt"}
        ]
    }
    res = run(test_state)
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))
