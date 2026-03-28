import os
import zipfile
import re
import requests # Thêm thư viện này để gọi API Local

# ==========================================
# HÀM GỌI LOCAL LLM SỬA LỖI CHÍNH TẢ
# ==========================================
def fix_typos_with_llm(tex_filepath,tex_llm_filename, model_name="qwen2.5:7b"):
    print(f"\n[LLM] Đang đọc file {tex_filepath} để sửa lỗi chính tả...")
    
    # 1. Đọc nội dung file LaTeX vừa tạo
    with open(tex_filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # 2. Câu lệnh (Prompt) TRÓI TAY LLM cực kỳ nghiêm ngặt
    prompt = f"""You are a LaTeX cleanup system.

Input:
- Noisy OCR LaTeX text from a Vietnamese math exam.

Tasks:
1. Remove meaningless LaTeX commands.
2. Fix Vietnamese text encoding.
3. Keep valid math expressions.
4. Convert incorrect math to plain text when needed.
5. DO NOT invent new content.
6. Output clean LaTeX only.

NỘI DUNG GỐC:
{original_content}
"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    try:
        # Gọi xuống server Ollama đang chạy ngầm trên máy
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        response.raise_for_status() # Báo lỗi nếu API sập
        
        # Lấy kết quả LLM trả về
        corrected_content = response.json().get("response", original_content)
        
        # Xóa các dấu ```latex mà LLM hay tự ý sinh ra ở đầu/cuối chuỗi
        corrected_content = corrected_content.replace("```latex", "").replace("```", "").strip()

        # 3. Ghi đè file LaTeX với nội dung sạch sẽ
        with open(tex_llm_filename, 'w', encoding='utf-8') as f:
            f.write(corrected_content)
            
        print("[LLM] Đã quét và sửa xong lỗi chính tả thành công!")
        
    except Exception as e:
        print(f"[LLM ERROR] Không thể gọi Local LLM. Đang giữ nguyên file gốc. Lỗi: {e}")
