# 📄 Hệ Thống Document AI Trích Xuất Tài Liệu (PDF to LaTeX)

Một hệ thống Trí tuệ Nhân tạo (Document AI) hoàn chỉnh, có khả năng tự động đọc hiểu, bóc tách cấu trúc tài liệu PDF (văn bản tiếng Việt, công thức Toán học, Hình ảnh/Biểu đồ) và xuất kết quả ra định dạng mã nguồn LaTeX chuẩn xác, sẵn sàng cho việc in ấn hoặc biên tập.

##  Tính năng nổi bật

* **Phân tích bố cục thông minh (Layout Analysis):** * Sử dụng mô hình YOLOv8 tự huấn luyện để nhận diện các vùng: `text` (văn bản), `math` (công thức toán), `graphics` (hình ảnh).
  * Ứng dụng kỹ thuật quét ảnh độ phân giải siêu cao (Super High-Res Inference) đảm bảo không bỏ sót công thức nhỏ hoặc chữ mờ.
* **Định tuyến & Xử lý song song (Smart Routing):**
  * **Văn bản tiếng Việt:** Trích xuất chính xác với kiến trúc mạng Transformer (VietOCR).
  * **Toán học:** Đọc và dịch trực tiếp hình ảnh công thức sang mã LaTeX (Pix2Tex / LaTeX OCR).
  * **Đồ họa:** Tự động cắt, lưu trữ và chèn đường dẫn hình ảnh vào mã nguồn một cách mượt mà.
* **Tiền xử lý ảnh chuyên sâu (Image Enhancement):** Tự động thêm Padding, khử răng cưa (Anti-aliasing), hàn gắn nét đứt (Morphology Closing), và nhị phân hóa Otsu để cứu các vùng ảnh bị vỡ, nhòe (VD: dấu %, số mũ li ti).
* **Đóng gói tự động (Auto-Packaging):** * Thuật toán gom dòng thông minh (Smart Sorting) giúp giữ nguyên trật tự đọc từ trên xuống dưới, trái qua phải.
  * Tự động sinh file `document.tex` chuẩn cấu trúc LaTeX và nén toàn bộ dữ liệu vào một file `.zip` duy nhất.
* **Hậu kiểm bằng LLM (LLM Post-processing):** Tích hợp Local LLM (chạy cục bộ) để tự động rà soát và sửa lỗi chính tả tiếng Việt mà không làm hỏng cấu trúc mã lệnh LaTeX.

---

##  Cấu trúc thư mục

```text
📁 Project_Root/
├── 📄 main.py            # Chứa luồng thực thi chính (Đọc PDF -> YOLO -> Phân luồng)
├── 📄 ai_model.py        # Khởi tạo và tải các mô hình AI (YOLO, VietOCR, Pix2Tex) vào RAM
├── 📄 xu_li_anh.py       # Chứa các hàm tiền xử lý ảnh (Làm nét, Padding) và Sắp xếp tọa độ
├── 📄 dong_goi.py        # Chứa thuật toán nối dòng và xuất file .tex, nén .zip
├── 📄 llm.py             # Module gọi Local LLM (Ollama) để hiệu đính văn bản
├── 📁 data/              # Thư mục chứa các file PDF đầu vào cần xử lý
├── 📁 output_images/     # Thư mục chứa file .tex, hình ảnh đồ họa được trích xuất
├── 📁 debugtext/         # (Chế độ Debug) Lưu ảnh cắt của văn bản để gỡ lỗi OCR
└── 📁 debugmath/         # (Chế độ Debug) Lưu ảnh cắt của toán học để gỡ lỗi OCR


Cài đặt và Yêu cầu hệ thống
Đảm bảo máy tính của bạn đã cài đặt Python 3.8+ và ưu tiên có GPU (CUDA) để tăng tốc độ nhận diện.

1. Cài đặt các thư viện lõi:

Bash
pip install ultralytics torch torchvision torchaudio
pip install opencv-python numpy Pillow PyMuPDF
2. Cài đặt các thư viện OCR:

Bash
pip install vietocr
pip install pix2tex[gui]


***** Hướng dẫn sử dụng****
Chỉ cần chạy file thực thi chính. Hệ thống sẽ tự động quét file PDF trong thư mục data/ và trả về kết quả.

Bash
python main.py
Kết quả đầu ra:
Sau khi chạy xong, hãy kiểm tra thư mục gốc để lấy file Ket_Qua_OCR_Final.zip. Giải nén file này, bạn sẽ nhận được:

document.tex: File mã nguồn LaTeX đã được biên soạn.

Các file hình ảnh .jpg (nếu tài liệu gốc có chứa hình ảnh/biểu đồ).

document_LLM_da_sua.tex (nếu bật tính năng hậu kiểm bằng LLM).

 Xử lý sự cố (Troubleshooting)
YOLO nhận diện thiếu chữ/toán: Tăng tham số imgsz trong main.py lên 1920 hoặc 2560 để AI nhìn rõ hơn ở độ phân giải gốc.

Chữ bị lặp lại (Ghost Predictions): Giảm tham số iou trong cấu hình YOLO (khuyến nghị iou=0.45) để thuật toán NMS mạnh tay xóa các hộp đè lên nhau.

Pix2Tex/VietOCR đọc sai chữ ở viền: Đảm bảo hàm enhance_image_for_ocr trong xu_li_anh.py đang có tham số padding (viền trắng) đủ lớn (VD: pad_size = 10 hoặc 15).
