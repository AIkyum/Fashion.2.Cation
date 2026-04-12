import os
import requests
import pandas as pd
import time

print("==================================================")
print("🚀 대규모 데이터 수집기 (사진 + 상세 스펙 모두 수집!)")
print("==================================================")

# 1. 폴더 세팅
SAVE_FOLDER = "ai_dataset_large"
IMG_FOLDER = os.path.join(SAVE_FOLDER, "images")
os.makedirs(IMG_FOLDER, exist_ok=True)

API_URL = "https://display-bff-api.29cm.co.kr/api/v1/listing/items?colorchipVariant=treatment"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 수집할 카테고리
TARGET_CATEGORIES = [
    # --- 👨 남성 ---
    {"label_name": "남성_상의", "gender": "남성", "category": "상의", "largeId": 272100100, "middleId": 272103100},
    {"label_name": "남성_하의", "gender": "남성", "category": "하의", "largeId": 272100100, "middleId": 272104100},
    {"label_name": "남성_아우터", "gender": "남성", "category": "아우터", "largeId": 272100100, "middleId": 272102100},
    
    # --- 👩 여성 ---
    {"label_name": "여성_상의", "gender": "여성", "category": "상의", "largeId": 268100100, "middleId": 268103100},
    {"label_name": "여성_하의", "gender": "여성", "category": "하의", "largeId": 268100100, "middleId": 268104100},
    {"label_name": "여성_아우터", "gender": "여성", "category": "아우터", "largeId": 268100100, "middleId": 268102100},
    {"label_name": "여성_원피스", "gender": "여성", "category": "원피스", "largeId": 268100100, "middleId": 268104100},
    {"label_name": "여성_스커트", "gender": "여성", "category": "치마", "largeId": 268100100, "middleId": 268105100},

    # --- 🎒 공용 / 잡화 ---
    {"label_name": "공용_가방", "gender": "공용", "category": "가방", "largeId": 273100100},
    {"label_name": "공용_신발", "gender": "공용", "category": "신발", "largeId": 270100100}  
]

# 3. 수집량 설정
PAGE_SIZE = 50
MAX_PAGES = 6  

collected_data = []

try:
    for target in TARGET_CATEGORIES:
        print(f"\n🎯 [{target['label_name']}] 수집 시작 (목표: {PAGE_SIZE * MAX_PAGES}개)")
        
        for page in range(1, MAX_PAGES + 1):
            print(f"  📄 {page}페이지 상세 데이터 요청 중...")
            
            # API 요청을 위한 포장(Payload) 세팅
            facet_input = {"largeId": target["largeId"]}
            if "middleId" in target:
                facet_input["middleId"] = target["middleId"]
            
            payload = {
                "pageType": "CATEGORY_PLP",
                "sortType": "RECOMMENDED",
                "facets": {
                    "categoryFacetInputs": [facet_input]
                },
                "pageRequest": {"page": page, "size": PAGE_SIZE}
            }
            
            # 🚨 내가 아까 빼먹었던 바로 그 부분! 여기서 서버에 요청을 보냄!
            response = requests.post(API_URL, headers=HEADERS, json=payload)
            
            if response.status_code == 200:
                items = response.json().get("data", {}).get("list", [])
                
                if not items:
                    print("  ⚠️ 더 이상 아이템이 없습니다. 다음 카테고리로 넘어갑니다.")
                    break
                
                for item in items:
                    try:
                        # 1. 아이템 이름 찾기 (여러 경로 대비)
                        item_name = ""
                        if "itemEvent" in item and "eventProperties" in item["itemEvent"]:
                            item_name = item["itemEvent"]["eventProperties"].get("itemName", "")
                        if not item_name:
                            item_name = item.get("itemName", "이름없음")
                            
                        # 사진 주소 찾기
                        img_url = item.get("imageUrl") or f"https://img.29cm.co.kr{item.get('imagePath', '')}"
                        
                        if not img_url or "http" not in img_url:
                            continue
                            
                        # 사진 저장 (이미 있으면 패스해서 초고속으로 넘어감!)
                        img_filename = f"{target['label_name']}_p{page:02d}_{item['itemId']}.jpg"
                        img_path = os.path.join(IMG_FOLDER, img_filename)
                        
                        if not os.path.exists(img_path):
                            img_res = requests.get(img_url).content
                            with open(img_path, "wb") as f:
                                f.write(img_res)
                        
                        # 2. 🔥 [업그레이드] 상세 정보 꼼꼼하게 뒤지기
                        brand_info = item.get("brand", {})
                        brand = brand_info.get("brandName", item.get("frontBrandName", "알수없음"))
                        
                        price_info = item.get("price", {})
                        price = price_info.get("salePrice", item.get("sellPrice", item.get("consumerPrice", 0)))
                        discount_rate = price_info.get("discountRate", item.get("discountRate", 0))
                        
                        review_info = item.get("review", {})
                        review_count = review_info.get("count", item.get("reviewCount", 0))
                        
                        heart_count = item.get("likeCount", item.get("heartCount", 0))

                        # 3. 엑셀에 데이터 넣기
                        collected_data.append({
                            "filename": img_filename,
                            "gender": target["gender"],
                            "category": target["category"],
                            "brand": brand,
                            "product_name": item_name,
                            "price": price,
                            "discount_rate": discount_rate,
                            "review_count": review_count,
                            "heart_count": heart_count
                        })
                        
                    except Exception as e:
                        continue
                
                print(f"  -> ✅ {page}페이지 상세 완료 (누적 {len(collected_data)}개)")
                time.sleep(1)
                
            else:
                print(f"🚨 API 요청 실패: {response.status_code}")
                break

    # 4. 최종 데이터 저장
    if collected_data:
        df = pd.DataFrame(collected_data)
        csv_path = os.path.join(SAVE_FOLDER, "metadata.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n🎉 웅장한 수집 완료! 사진과 상세 정보가 담긴 {len(collected_data)}개의 데이터가 저장되었습니다.")

except KeyboardInterrupt:
    print("\n🛑 수집이 사용자에 의해 중단되었습니다.")
    if collected_data:
        pd.DataFrame(collected_data).to_csv(os.path.join(SAVE_FOLDER, "metadata_partial.csv"), index=False, encoding="utf-8-sig")
        print("💾 중단되기 전까지의 데이터가 metadata_partial.csv로 저장되었습니다.")
        
except Exception as e:
    print(f"\n🚨 치명적 에러 발생: {e}")