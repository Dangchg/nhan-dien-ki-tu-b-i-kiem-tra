from ultralytics import YOLO
from pix2tex.cli import LatexOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

# ==========================================
# 1. KHỞI TẠO CÁC MÔ HÌNH
# ==========================================
print("Đang khởi tạo các hệ thống AI...")
yolo_model = YOLO("runs\detect\my_yolo_finetune\lan_train_finetune\weights/best.pt") 
print("Khởi tạo 1!\n")
math_ocr_model = LatexOCR()
print("Khởi tạo 2\n")
config = Cfg.load_config_from_name('vgg_transformer')

# Cấu hình chạy trên GPU (nếu có) hoặc CPU
config['device'] = 'cuda:0' # Đổi thành 'cpu' nếu máy không có card NVIDIA
config['cnn']['pretrained'] = False
config['predictor']['beamsearch'] = False # Tắt beamsearch để chạy nhanh hơn

text_ocr_model = Predictor(config)
print("Khởi tạo hoàn tất!\n")