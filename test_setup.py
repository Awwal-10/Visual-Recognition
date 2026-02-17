import cv2
import imagehash
import torch
from torchvision import models
from PIL import Image

print("Testing all dependencies...\n")

# Test OpenCV
print("✅ OpenCV version:", cv2.__version__)

# Test ImageHash
print("✅ ImageHash version:", imagehash.__version__)

# Test PyTorch
print("✅ PyTorch version:", torch.__version__)

# Test loading a model (this is the BIG test)
print("\n🔄 Loading EfficientNet model (this takes 10-20 seconds)...")
model = models.efficientnet_b0(pretrained=True)
print("✅ EfficientNet loaded successfully!")

print("\n🎉 ALL SYSTEMS GO! Ready to build!")