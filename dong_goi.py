import os
import zipfile
import re
from llm import fix_typos_with_llm

def export_to_latex_and_zip(all_pages_data, output_dir="output_images", zip_filename="Ket_Qua_OCR.zip"):
    print("\n==========================================")
    print(" BẮT ĐẦU XUẤT DỮ LIỆU & ĐÓNG GÓI ZIP")
    print("==========================================")
    
    tex_filename = os.path.join(output_dir, "document.tex")
    tex_llm_filename = os.path.join(output_dir, "document_LLM_da_sua.tex")
    
    latex_content = [
        "\\documentclass[12pt,a4paper]{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[vietnamese]{babel}",
        "\\usepackage{amsmath, amssymb, amsfonts}",
        "\\usepackage{graphicx}",
        "\\usepackage[margin=2cm]{geometry}",
        "\\begin{document}\n"
    ]
    
    for page_data in all_pages_data:
        latex_content.append(f"% --- BẮT ĐẦU TRANG {page_data['page']} ---\n")
        
        # BỘ ĐỆM DÒNG: Dùng để gom chữ và toán đứng ngang hàng nhau
        line_buffer = [] 
        
        for item in page_data['content']:
            label = item['type']
            text = item['content']
            
            # Nhóm 1: Chữ và Toán học (gom chung trên 1 dòng)
            if label in ['text', 'math']:
                line_buffer.append(text)
                
            # Nhóm 2: Nhãn ảo ngắt dòng (Từ thuật toán sort_boxes)
            elif label == 'newline':
                # Khi hết một dòng vật lý, đổ bộ đệm ra kèm \n\n để ngắt đoạn LaTeX
                if line_buffer:
                    latex_content.append(" ".join(line_buffer) + "\n\n")
                    line_buffer = [] 
                    
            # Nhóm 3: Hình ảnh (graphics)
            elif label == 'graphics':
                # Chốt luôn đoạn chữ đang gom dở (nếu có) trước khi chèn ảnh
                if line_buffer:
                    latex_content.append(" ".join(line_buffer) + "\n\n")
                    line_buffer = [] 
                    
                # Trích xuất tên file ảnh từ chuỗi ![...](tên_ảnh.jpg)
                match = re.search(r'\((.*?)\)', text)
                if match:
                    img_name = match.group(1)
                    latex_content.append("\\begin{figure}[htbp]")
                    latex_content.append("  \\centering")
                    latex_content.append(f"  \\includegraphics[width=0.8\\linewidth]{{{img_name}}}")
                    latex_content.append("\\end{figure}\n\n")
        
        # Kết thúc trang, nếu còn chữ đọng lại trong bộ đệm thì đổ nốt ra
        if line_buffer:
            latex_content.append(" ".join(line_buffer) + "\n\n")
            
        latex_content.append("\\newpage\n") 
        
    latex_content.append("\\end{document}")

    # 1. GHI TOÀN BỘ NỘI DUNG RA FILE GỐC (Chưa qua LLM)
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_content))
    print(f"[OK] Đã tạo file LaTeX gốc tại: {tex_filename}")
    
    # 2. GỌI LLM SỬA CHÍNH TẢ VÀ LƯU RA FILE MỚI
    print("\n[LLM] Bắt đầu rà soát lỗi chính tả...")
    try:
        # Tùy thuộc vào việc hàm LLM của anh trả về chuỗi text hay tự lưu file
        # Nếu hàm LLM trả về chuỗi text đã sửa:
        fixed_text = fix_typos_with_llm(tex_filename,tex_llm_filename)

        print(f"[OK] Đã tạo file LaTeX LLM sửa tại: {tex_llm_filename}")
    except Exception as e:
        print(f"[LỖI] Quá trình gọi LLM thất bại: {e}")

    # 3. ĐÓNG GÓI ZIP TOÀN BỘ (Sẽ bao gồm cả bản gốc và bản LLM)
    print(f"\nĐang nén toàn bộ thư mục vào file {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=output_dir)
                zipf.write(file_path, arcname)
                
    print(f"[THÀNH CÔNG] Đã sinh ra file: {zip_filename}")# 1. GHI TOÀN BỘ NỘI DUNG RA FILE GỐC (Chưa qua LLM)
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_content))
    print(f"[OK] Đã tạo file LaTeX gốc tại: {tex_filename}")
    
    # 2. GỌI LLM SỬA CHÍNH TẢ VÀ LƯU RA FILE MỚI
    print("\n[LLM] Bắt đầu rà soát lỗi chính tả...")
    try:
        # Tùy thuộc vào việc hàm LLM của anh trả về chuỗi text hay tự lưu file
        # Nếu hàm LLM trả về chuỗi text đã sửa:
        fixed_text = fix_typos_with_llm(tex_filename,tex_llm_filename)
        if fixed_text:
            with open(tex_llm_filename, "w", encoding="utf-8") as f:
                f.write(fixed_text)
            print(f"[OK] Đã tạo file LaTeX LLM sửa tại: {tex_llm_filename}")
    except Exception as e:
        print(f"[LỖI] Quá trình gọi LLM thất bại: {e}")

    # 3. ĐÓNG GÓI ZIP TOÀN BỘ (Sẽ bao gồm cả bản gốc và bản LLM)
    print(f"\nĐang nén toàn bộ thư mục vào file {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=output_dir)
                zipf.write(file_path, arcname)
                
    print(f"[THÀNH CÔNG] Đã sinh ra file: {zip_filename}")
