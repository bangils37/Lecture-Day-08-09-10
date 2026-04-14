import json
import os
from datetime import datetime
from graph import run_graph

def run_grading():
    # Paths
    input_file = "data/grading_questions.json"
    output_file = "artifacts/grading_run.jsonl"
    
    # 1. Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found. Please wait until 17:00 to run grading.")
        return

    # 2. Load questions
    with open(input_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    print(f"📋 Running grading for {len(questions)} questions...")
    print("============================================================")

    # 3. Open output file for writing
    with open(output_file, "w", encoding="utf-8") as out:
        for q in questions:
            q_id = q.get("id")
            question = q.get("question")
            
            print(f"[{q_id}] Processing: {question[:60]}...")
            
            try:
                # Run the graph
                result = run_graph(question)
                
                # Format the grading record according to SCORING.md rubric
                record = {
                    "id": q_id,
                    "question": question,
                    "answer": result.get("final_answer"),
                    "sources": result.get("retrieved_sources", []),
                    "supervisor_route": result.get("supervisor_route"),
                    "route_reason": result.get("route_reason"),
                    "workers_called": result.get("workers_called", []),
                    "mcp_tools_used": result.get("mcp_tools_used", []),
                    "confidence": result.get("confidence"),
                    "latency_ms": result.get("latency_ms"),
                    "hitl_triggered": result.get("hitl_triggered", False),
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Write to JSONL
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"  ✓ Success ({result.get('latency_ms', 0)}ms)")
                
            except Exception as e:
                print(f"  ❌ Failed: {str(e)}")
                error_record = {
                    "id": q_id,
                    "question": question,
                    "answer": f"PIPELINE_ERROR: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                out.write(json.dumps(error_record, ensure_ascii=False) + "\n")

    print("============================================================")
    print(f"✅ Done. Grading log saved to: {output_file}")

if __name__ == "__main__":
    run_grading()
