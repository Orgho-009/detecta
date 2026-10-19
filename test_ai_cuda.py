import cv2
import numpy as np
import torch
import onnxruntime as ort
from desktop_client.ai_engine import AIEngine

print("=" * 60)
print("DETECTA AI GPU ACCELERATION CHECK")
print("=" * 60)
print("PyTorch Version:", torch.__version__)
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU Device:", torch.cuda.get_device_name(0))
print("ONNX Providers:", ort.get_available_providers())
print("-" * 60)

# Initialize AI Engine
ai = AIEngine(yolo_path="desktop_client/yolo11n.pt", db_path="desktop_client/known_faces.pkl")

# Generate synthetic frame to test inference
test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(test_frame, "GPU Pipeline Test", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

annotated, inventory = ai.process(test_frame)
print("-" * 60)
print("AI Engine Processed Frame Successfully!")
print("Inventory:", inventory)
print("Annotated Frame Shape:", annotated.shape)
print("=" * 60)
