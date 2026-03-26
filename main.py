import fitz  
import cv2
import numpy as np
from PIL import Image
import os

# --- IMPORT TỪ CÁC FILE CỦA ANH ---
from xu_li_anh import sort_boxes, enhance_image_for_ocr, apply_custom_nms
from ai_model import yolo_model, math_ocr_model, text_ocr_model
from dong_goi import export_to_latex_and_zip


# --- CẤU HÌNH DEBUG ---
IS_DEBUG = True  # Bật/Tắt chế độ gỡ lỗi
DEBUG_DIR_TEXT = "debugtext"  # Tên thư mục lưu ảnh debug
DEBUG_DIR_MATH = "debugmath"  # Tên thư mục lưu ảnh debug
if IS_DEBUG and not os.path.exists(DEBUG_DIR_TEXT):
    os.makedirs(DEBUG_DIR_TEXT)
    print(f"[DEBUG] Đã tạo thư mục: {DEBUG_DIR_TEXT}")
if IS_DEBUG and not os.path.exists(DEBUG_DIR_MATH):
    os.makedirs(DEBUG_DIR_MATH)
    print(f"[DEBUG] Đã tạo thư mục: {DEBUG_DIR_MATH}")



# ==========================================
# 3. HÀM XỬ LÝ CHÍNH VÀ PHÂN LUỒNG (ROUTING)
# ==========================================
def process_pdf_advanced(pdf_path, output_dir="output_images"):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    all_pages_data = []
    
    for page_num in range(len(doc)):
        print(f"\n--- Đang xử lý Trang {page_num + 1}/{len(doc)} ---")
        page = doc[page_num]
        pix = page.get_pixmap(dpi=400) 
        
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4: img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        elif pix.n == 3: img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
        # 3.1. DÙNG YOLO QUÉT VÀ LẤY TỌA ĐỘ
        results = yolo_model(
            source=img_array,
            imgsz=1024,
            conf=0.25,
            iou=0.45,
            line_width=1,
            max_det=1000,
            
            
        )
        boxes = results[0].boxes
        
        detected_items = []
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            label = yolo_model.names[int(box.cls[0])]
            # ---  Trích xuất thêm độ tự tin (Confidence) ---
            conf_score = float(box.conf[0]) 
            
            # Đưa conf vào từ điển để hàm lọc có dữ liệu so sánh
            detected_items.append({
                "label": label, 
                "box": (x1, y1, x2, y2),
                "conf": conf_score
            })
            
        # 3.2. LỌC TRÙNG LẶP VÀ SẮP XẾP LẠI THỨ TỰ
        # BƯỚC QUAN TRỌNG: Gọi hàm lọc thủ công với ngưỡng đè nhau 80% (0.8)
        cleaned_items = apply_custom_nms(detected_items, iou_threshold=0.8)
        
        # Sau khi lọc sạch rác và nhãn ảo, mới đưa vào sắp xếp thứ tự đọc
        sorted_items = sort_boxes(cleaned_items)
        page_content = []
        
        # 3.3. BỘ ĐỊNH TUYẾN (ROUTER) ĐẾN CÁC ENGINE OCR
        for idx, item in enumerate(sorted_items):
            label = item['label']
            
            # --- -------------------------------- ---
            if label == 'newline':
                # Truyền lệnh ngắt dòng sang cho hệ thống đóng gói
                page_content.append({"type": "newline", "content": ""})
                continue
            # ----------------------------------------
            
            x1, y1, x2, y2 = item['box']
            
            # 1. Cắt ảnh với Padding an toàn
            pad = 6 
            crop_img = img_array[max(0, int(y1)-pad) : min(img_array.shape[0], int(y2)+pad), 
                                 max(0, int(x1)-pad) : min(img_array.shape[1], int(x2)+pad)]
            
            if crop_img.size == 0: continue
            
            # --- CHẠY HÀM LÀM NÉT ẢNH Ở ĐÂY ---
            # Chỉ làm nét cho TEXT và MATH, không làm nét DIAGRAM (biểu đồ) vì dễ làm hỏng màu sắc
            if label in ['text', 'math']:
                crop_img = enhance_image_for_ocr(crop_img)

            # ==========================================
            # LUỒNG 1: ĐỌC CHỮ TIẾNG VIỆT
            # ==========================================
            if label in ['text']:
                try:
                    if IS_DEBUG:
                        debug_filename = f"p{page_num+1}_i{idx}_{label}.png"
                        cv2.imwrite(os.path.join(DEBUG_DIR_TEXT, debug_filename), crop_img)

                    
                    # 2. Chuyển đổi từ OpenCV (NumPy) sang định dạng PIL Image mà VietOCR yêu cầu
                    pil_crop = Image.fromarray(cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB))
                    
                    # 3. Đưa vào VietOCR đọc (Cực kỳ đơn giản, không cần bóc tách mảng phức tạp như PaddleOCR)
                    # Thêm replace và strip ở cuối để dọn sạch dấu enter ngầm
                    extracted_text = text_ocr_model.predict(pil_crop).replace('\n', ' ').strip()
                    
                    # Định dạng lại theo nhãn
                    if label == 'header': extracted_text = f"### {extracted_text.strip()}"
                    elif label == 'equation_number': extracted_text = f"({extracted_text.strip()})"
                    
                    page_content.append({"type": label, "content": extracted_text})
                    print(f"[{label.upper()}]: {extracted_text}")
                    
                except Exception as e:
                    print(f"[LỖI VIETOCR]: {e}")

            # --- LUỒNG 2: ĐỌC TOÁN HỌC (MATH) ---
            elif label == 'math':
                pil_img = Image.fromarray(cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB))
                try:

                    # ------ BẮT ĐẦU PHẦN GỠ LỖI (DEBUG) ------
                    if IS_DEBUG:
                        # Tạo tên file: debug/p0_i3_header.png (Trang 0, Item 3, nhãn header)
                        debug_filename = f"p{page_num}_i{idx}_{label}.png"
                        debug_path = os.path.join(DEBUG_DIR_MATH, debug_filename)
                        # Lưu ảnh cắt (OpenCV dùng BGR nên lưu trực tiếp)
                        cv2.imwrite(debug_path, crop_img)
                    # ------ KẾT THÚC PHẦN GỠ LỖI (DEBUG) ------
                    # Dọn sạch dấu enter ngầm của Pix2Tex
                    latex_text = math_ocr_model(pil_img).replace('\n', ' ').strip()
                    
                    # CỰC KỲ QUAN TRỌNG: Viết liền dấu $ vào chữ, KHÔNG CÓ \n
                    final_math = f"${latex_text}$"
                    page_content.append({"type": label, "content": final_math})
                    print(f"[MATH]: {final_math}")
                except Exception as e:
                    print(f"[LỖI MATH OCR]: {e}")

            # --- LUỒNG 3: HÌNH ẢNH VÀ BIỂU ĐỒ (DIAGRAM) ---
            elif label == 'graphics':
                # Offline cực kỳ khó đọc hiểu biểu đồ, cách tốt nhất là lưu ảnh lại
                img_name = f"page_{page_num+1}_diagram_{idx}.jpg"
                img_path = os.path.join(output_dir, img_name)
                cv2.imwrite(img_path, crop_img)
                
                # Chèn đường dẫn ảnh vào nội dung
                placeholder = f"![Diagram]({img_name})"
                page_content.append({"type": label, "content": placeholder})
                print(f"[DIAGRAM]: Đã lưu hình ảnh tại {img_path}")



        all_pages_data.append({"page": page_num + 1, "content": page_content})
        
    return all_pages_data


# ==========================================
# KHỞI CHẠY
# ==========================================
if __name__ == "__main__":
    pdf_path = "data/tesst.pdf" 
    output_folder = "output_images" 
    
    print(f"Bắt đầu xử lý file: {pdf_path}")
    data_ket_qua = process_pdf_advanced(pdf_path, output_dir=output_folder)
    
    export_to_latex_and_zip(data_ket_qua, output_dir=output_folder, zip_filename="Ket_Qua_OCR_Final.zip")
    print("\nHOÀN TẤT TOÀN BỘ QUY TRÌNH!")