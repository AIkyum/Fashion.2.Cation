import os
import time
import platform
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

print("====================================")
print(f"🖥️ 멀티 카테고리 데이터 수집기 (OS: {platform.system()})")
print("====================================")

# 1. 저장 폴더 셋업
SAVE_FOLDER = "ai_dataset_29cm"
IMG_FOLDER = os.path.join(SAVE_FOLDER, "images")
os.makedirs(IMG_FOLDER, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 2. 🌟 여기가 핵심! 로봇의 할 일 목록 (임시 URL들)
# 나중에 진짜 수집할 때 이 안의 URL만 29CM 카테고리 주소로 바꿔주면 돼!
TARGET_CATEGORIES = [
    {"label_name": "남성_상의", "gender": "남성", "category": "상의", "url": "https://www.29cm.co.kr/store/category/list?categoryLargeCode=272100100&categoryMediumCode=272103100&sort=RECOMMENDED&defaultSort=RECOMMENDED&page=1"},
    {"label_name": "여성_아우터", "gender": "여성", "category": "아우터", "url": "https://www.29cm.co.kr/store/category/list?categoryLargeCode=268100100&categoryMediumCode=268102100&sort=RECOMMENDED&defaultSort=RECOMMENDED&page=1"}
]

try:
    print("⏳ 드라이버 준비 중...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    collected_data = []
    
    # 3. 목록을 하나씩 돌면서 수집 시작!
    for target in TARGET_CATEGORIES:
        print(f"\n🚀 [{target['label_name']}] 카테고리 수집을 시작합니다...")
        driver.get(target["url"])
        time.sleep(3) # 로딩 대기
        
        # 상품 이미지 찾기 (안정성을 위해 img 태그를 찾고 크기로 필터링)
        images = driver.find_elements(By.TAG_NAME, "img")
        
        count = 0
        for img in images:
            if count >= 3: # 테스트용으로 각 카테고리당 3개씩만 수집
                break
                
            img_url = img.get_attribute("src")
            name = img.get_attribute("alt")
            
            # 유효한 상품 이미지만 필터링
            if img_url and "http" in img_url and name and len(name) > 2:
                try:
                    # 파일명에 카테고리 이름을 붙여서 섞이지 않게 함 (예: 남성_상의_001.jpg)
                    img_filename = f"{target['label_name']}_{count:03d}.jpg"
                    img_path = os.path.join(IMG_FOLDER, img_filename)
                    
                    img_res = requests.get(img_url).content
                    with open(img_path, "wb") as f:
                        f.write(img_res)
                    
                    # 🌟 AI 정답지(Label) 작성
                    collected_data.append({
                        "filename": img_filename,
                        "product_name": name,
                        "gender": target["gender"],       # AI 태그 1
                        "category": target["category"]    # AI 태그 2
                    })
                    print(f"  -> ✅ 저장 완료: {img_filename}")
                    count += 1
                except Exception as e:
                    continue

    # 4. 최종 데이터 CSV 저장
    if collected_data:
        df = pd.DataFrame(collected_data)
        csv_path = os.path.join(SAVE_FOLDER, "metadata.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n🎉 수집 완료! 총 {len(collected_data)}개의 데이터가 정답지와 함께 저장되었습니다.")

except Exception as e:
    print(f"\n🚨 오류 발생: {e}")

finally:
    driver.quit()
    print("🧹 브라우저 종료.")