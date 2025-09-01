## Naver SmartStore Review Scraper

네이버 **스마트스토어 상품 리뷰**를 자동으로 수집하는 파이썬 스크립트입니다.  
Selenium 기반으로 동작하며, 페이지네이션 처리, 중간 저장, CAPTCHA 대응을 포함합니다.

---

### 주요 기능
- 지정한 스마트스토어 상품 페이지의 리뷰를 최대 `2000 페이지`까지 수집 (수정가능)
- 리뷰 중복 제거 및 자동 CSV 저장
- 일정 간격마다 **중간 저장 파일** 생성 (`reviews_{brand}_{product_id}_pN.csv`)
- 스크래핑 중 오류 발생 시 자동 재시작 및 로그 기록
- 사람이 쓰는 것처럼 보이는 랜덤 대기(`human_sleep`) 적용
- CAPTCHA 발생 시 수동 입력 후 다시 진행 가능

---

### 설치 방법

1. 저장소 클론
```powershell
git clone https://github.com/dathru/review_scaper.git
cd review_scaper

2. requirements.txt 다운로드

3. 라이브러리 설치
```powershell
pip install -r requirements.txt
pip freeze > requirements.txt

최소 필요 라이브러리:
* selenium
* webdriver-manager
* pandas

4. 사용 방법
1) review_scraper_배포용.py (혹은 코드가 담긴 파일)에서 상품 URL 수정:
url = 'https://brand.naver.com/brandname/products/0000000000'

2) 실행:
```powershell
python scraper.py

3) 리뷰 데이터는 CSV 파일로 저장됩니다:
reviews_{브랜드명}_{상품ID}_pN.csv (중간 저장)
reviews_{브랜드명}_{상품ID}.csv (최종 저장)

4) CSV 결과 예시

| page | author  | date      | rating | text                                 | option                                         |
|------|---------|-----------|--------|--------------------------------------|------------------------------------------------|
| 1    | a****** | 25.08.01. | 5      | 촉촉하니 부드럽게 발림성 좋아요        | 피부타입중성, 주름, 트러블, 모공, 케어, 아주 좋아요, 흡수력, 아주 만족해요, 촉촉함, 촉촉해요 |
| 1    | b****** | 25.08.11. | 5      | 아직 사용전인데 유명해서 구매해봤어요!! | 트러블케어, 잘 모르겠어요, 흡수력, 아주 만족해요, 촉촉함, 보통이에요 |
