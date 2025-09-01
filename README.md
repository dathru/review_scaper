# Naver SmartStore Review Scraper

네이버 **스마트스토어 상품 리뷰**를 자동으로 수집하는 파이썬 스크립트입니다.  
Selenium 기반으로 동작하며, 페이지네이션 처리, 중간 저장, CAPTCHA 대응을 포함합니다.

---

## 주요 기능
- 지정한 스마트스토어 상품 페이지의 리뷰를 최대 `2000 페이지`까지 수집 (수정가능)
- 리뷰 중복 제거 및 자동 CSV 저장
- 일정 간격마다 **중간 저장 파일** 생성 (`reviews_{brand}_{product_id}_pN.csv`)
- 스크래핑 중 오류 발생 시 자동 재시작 및 로그 기록
- 사람이 쓰는 것처럼 보이는 랜덤 대기(`human_sleep`) 적용
- CAPTCHA 발생 시 수동 입력 후 다시 진행 가능

---

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/dathru/review_scaper.git
cd review_scaper
