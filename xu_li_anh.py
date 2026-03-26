import cv2
import numpy as np
# ==========================================
# HÀM TÍNH ĐỘ GIAO NHAU (IOU) GIỮA 2 HỘP
# ==========================================
def calculate_iou(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # Tính tọa độ của vùng giao nhau (Hình chữ nhật phần lõi)
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)

    # Nếu không giao nhau
    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # Diện tích vùng giao nhau
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # Diện tích của từng hộp
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

    # Diện tích tổng (Union)
    union_area = box1_area + box2_area - intersection_area

    # Tính tỷ lệ IOU
    if union_area == 0: return 0.0
    return intersection_area / union_area

# ==========================================
# HÀM LỌC HỘP TRÙNG LẶP DỰA TRÊN CONFIDENCE (CUSTOM NMS)
# ==========================================
def apply_custom_nms(detected_items, iou_threshold=0.8):
    """
    Giữ lại hộp có độ tự tin (conf) cao nhất khi có nhiều hộp đè lên nhau.
    """
    if not detected_items:
        return []

    # 1. Sắp xếp danh sách các hộp theo điểm tự tin (conf) GIẢM DẦN
    # Hộp nào AI tự tin nhất sẽ đứng đầu và được ưu tiên xét trước
    sorted_items = sorted(detected_items, key=lambda x: x['conf'], reverse=True)
    
    keep = []
    
    for item in sorted_items:
        box = item['box']
        overlap = False
        
        # 2. So sánh hộp đang xét với các hộp ĐÃ ĐƯỢC GIỮ LẠI
        for kept_item in keep:
            kept_box = kept_item['box']
            iou = calculate_iou(box, kept_box)
            
            # Nếu hộp đang xét đè lên hộp đã giữ (hộp điểm cao) quá nhiều
            if iou > iou_threshold:
                overlap = True
                break # Bỏ qua hộp đang xét, không lưu vào danh sách keep
                
        # 3. Nếu không đè lên ai (hoặc đè rất ít), thì giữ lại hộp này
        if not overlap:
            keep.append(item)
            
    return keep
# ==========================================
# 2. HÀM SẮP XẾP THỨ TỰ (NÂNG CẤP ĐỘNG)
# ==========================================
def sort_boxes(boxes_list):
    if not boxes_list: return []

    # 1. TÍNH TOÁN TÂM Y (cy) VÀ CHIỀU CAO (h) CỦA TỪNG HỘP
    # Thay vì dùng mép trên y1, ta dùng tâm của chữ sẽ chuẩn xác hơn nhiều đối với toán học
    for b in boxes_list:
        x1, y1, x2, y2 = b['box']
        b['cy'] = (y1 + y2) / 2
        b['h'] = y2 - y1

    # Sắp xếp sơ bộ từ trên xuống dưới theo tâm Y
    boxes_list.sort(key=lambda b: b['cy'])

    lines = []
    current_line = [boxes_list[0]]

    for box in boxes_list[1:]:
        # Tính chiều cao trung bình và tâm Y trung bình của dòng hiện tại
        avg_h = sum(b['h'] for b in current_line) / len(current_line)
        avg_cy = sum(b['cy'] for b in current_line) / len(current_line)
        
        # NGƯỠNG ĐỘNG: Lệch Y tối đa bằng 40% chiều cao của dòng chữ đó
        # (Giúp chữ to thì ngưỡng lớn, chữ nhỏ thì ngưỡng nhỏ, không bị fix cứng 30px)
        dynamic_y_threshold = avg_h * 0.4 

        # Nếu box mới có tâm Y nằm trong ngưỡng an toàn -> Gom vào dòng hiện tại
        if abs(box['cy'] - avg_cy) < dynamic_y_threshold:
            current_line.append(box)
        else:
            # Sang dòng mới: Sắp xếp dòng cũ từ trái qua phải (trục x1)
            current_line.sort(key=lambda b: b['box'][0])
            lines.append(current_line)
            current_line = [box] 

    if current_line:
        current_line.sort(key=lambda b: b['box'][0])
        lines.append(current_line)

    sorted_list = []
    for line in lines:
        sorted_list.extend(line)
        sorted_list.append({"label": "newline", "box": (0, 0, 0, 0)})

    return sorted_list

# ==========================================
# 2.5. HÀM RỬA ẢNH (CHUYÊN TRỊ ẢNH VỠ, RĂNG CƯA)
# ==========================================
def enhance_image_for_ocr(image):
    # 1. THÊM VIỀN TRẮNG (PADDING) - Cực kỳ quan trọng
    # Pix2Tex và VietOCR sẽ bị "mù" nếu nét chữ chạm thẳng vào viền ảnh.
    # Ta phải thêm 10px viền trắng bao quanh để AI có không gian nhận diện.
    pad_size = 10
    padded = cv2.copyMakeBorder(image, pad_size, pad_size, pad_size, pad_size, 
                                cv2.BORDER_CONSTANT, value=[255, 255, 255])

    # 2. Phóng to ảnh gấp 2 lần (Bicubic)
    enlarged = cv2.resize(padded, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    # 3. LÀM MỜ CHỐNG RĂNG CƯA (Anti-aliasing)
    # Thay vì làm nét, ta làm mờ nhẹ (Gaussian Blur) để các góc cạnh bị vỡ hạt (như ảnh 0,9%) trở nên mềm mại.
    blurred = cv2.GaussianBlur(enlarged, (3, 3), 0)
    
    # 4. Chuyển xám và Nhị phân hóa Otsu
    # Lúc này Otsu sẽ cắt nền cực kỳ mượt mà vì ảnh đã được làm mềm.
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 5. HÀN GẮN NÉT ĐỨT (Morphology Closing)
    # Thuật toán này sẽ "nối" các nét đứt vi mô lại với nhau thành 1 khối đen đặc.
    kernel_morph = np.ones((2, 2), np.uint8)
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_morph)
    
    final_img = cv2.cvtColor(closed, cv2.COLOR_GRAY2BGR)
    return final_img