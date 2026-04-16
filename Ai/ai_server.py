import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import os
import pandas as pd
import io
from fastapi import FastAPI, File, UploadFile

# 1. API 서버 생성
app = FastAPI(title="패션 카테고리 감정 AI")

# 2. 하드웨어 & 환경 세팅
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 3. 정답지(카테고리 이름) 불러오기
FINAL_CSV = os.path.join(BASE_DIR, "ai_dataset_large", "final_training_data.csv")
df = pd.read_csv(FINAL_CSV)
df['category'] = df['category'].astype('category')
class_names = df['category'].cat.categories.tolist()

# 4. 🌟 모델을 '서버 켜질 때 딱 한 번만' 불러오기 (매우 중요! 속도 향상)
model = models.resnet18()
model.fc = nn.Linear(model.fc.in_features, 7)
MODEL_PATH = os.path.join(BASE_DIR, "fashion_model.pth")

# 서버(EC2)가 CPU만 있을 수도 있으니 map_location='cpu' 추가
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=True))
model = model.to(device)
model.eval()

# 5. 이미지 변환기
val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# 6. 🚀 사진을 받는 API 창구 (Endpoint)
@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    # 1. 들어온 사진 파일 읽기
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    
    # 2. AI가 먹기 좋게 변환
    image_tensor = val_transform(image).unsqueeze(0).to(device)
    
    # 3. AI 감정 시작!
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = F.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probabilities, 1)
        
    category_name = class_names[predicted_idx.item()]
    conf_score = round(confidence.item() * 100, 2)
    
    # 4. 백엔드(api.js)가 읽기 편한 JSON 형태로 결과 쏴주기
    return {
        "status": "success",
        "category": category_name,
        "confidence": conf_score
    }

# 서버 실행용 시동 버튼 코드
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai_server:app", host="0.0.0.0", port=8001, reload=True)