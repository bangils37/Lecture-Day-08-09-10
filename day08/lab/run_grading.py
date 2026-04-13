import json
import os
from datetime import datetime
from rag_answer import rag_answer
from pathlib import Path

def run_grading():
    """
    Script để chạy pipeline và tạo grading_run.json theo yêu cầu của SCORING.md.
    Hệ thống sẽ dùng cấu hình 'hybrid' là cấu hình tốt nhất đã qua kiểm chứng.
    """
    questions_path = Path("data/grading_questions.json")
    output_path = Path("logs/grading_run.json")
    
    if not questions_path.exists():
        print(f"Lỗi: Không tìm thấy {questions_path}")
        print("Vui lòng copy file grading_questions.json vào thư mục data/ lúc 17:00.")
        return

    print(f"Đang đọc câu hỏi từ {questions_path}...")
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"Chạy pipeline cho {len(questions)} câu hỏi...")
    log = []
    
    for q in questions:
        print(f"  Đang xử lý {q['id']}...")
        result = rag_answer(
            query=q["question"], 
            retrieval_mode="hybrid", 
            verbose=False
        )
        
        log.append({
            "id": q["id"],
            "question": q["question"],
            "answer": result["answer"],
            "sources": result["sources"],
            "chunks_retrieved": len(result["chunks_used"]),
            "retrieval_mode": result["config"]["retrieval_mode"],
            "timestamp": datetime.now().isoformat(),
        })

    # Tạo thư mục logs nếu chưa có
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        
    print(f"\nHoàn thành! Kết quả đã lưu vào {output_path}")
    print("Vui lòng kiểm tra file trước khi nộp bài.")

if __name__ == "__main__":
    run_grading()
