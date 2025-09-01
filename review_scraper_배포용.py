#######################################
# 스마트스토어 상품의 리뷰 스크래퍼입니다.
#######################################

import os, glob, random, time, sys, signal
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
import logging

# --- 로깅 설정 ---
LOG_FILE = "naver_review_scraper.log"
logger = logging.getLogger("review_scraper")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
info_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(info_handler)

def log_info(msg): print(msg); logger.info(msg)
def log_warning(msg): print(msg); logger.warning(msg)
def log_error(msg): print(msg); logger.error(msg)

# --- 사람처럼 보이는 랜덤 대기 함수 ---
def human_sleep(min_time, max_time, jitter=0.3):
    """
    사람처럼 랜덤한 대기 시간을 적용
    - min_time: 최소 대기 시간
    - max_time: 최대 대기 시간
    - jitter: +/- 변동폭
    """
    base = random.uniform(min_time, max_time)
    variation = random.uniform(-jitter, jitter)
    t = max(0.1, base + variation)
    time.sleep(t)

# --- 설정 ---
MAX_PAGES = 2000
WAIT_MIN = 3.5
WAIT_MAX = 7.0
MID_SAVE = 50

# --- URL 및 파일명 설정 ---
url = 'https://brand.naver.com/brandname/products/0000000000' 
# 크롤링 하려는 스마트스토어 상품 주소를 입력해주세요
parsed_url = urlparse(url)
path_parts = parsed_url.path.split('/')
brand_name = path_parts[1]
product_id = path_parts[-1]
base_file_name = f'reviews_{brand_name}_{product_id}'

# --- 중간 저장 리뷰 리스트 ---
all_reviews = []

# --- Ctrl+C 처리 ---
stop_scraping = False
def signal_handler(sig, frame):
    global stop_scraping
    stop_scraping = True
    log_warning("\n강제 종료 감지! 현재까지 수집된 리뷰 저장 중...")
    try:
        driver.quit()
    except:
        pass
    save_reviews(intermediate=True)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# --- 리뷰 저장 ---
def save_reviews(intermediate=False):
    global all_reviews
    if not all_reviews:
        return

    # 이전 중간 저장 파일 병합
    mid_files = sorted(glob.glob(f"{base_file_name}_p*.csv"))
    merged_reviews = all_reviews.copy()
    for f in mid_files:
        df = pd.read_csv(f, encoding='utf-8-sig')
        for r in df.to_dict('records'):
            if not any(existing["author"]==r["author"] and existing["date"]==r["date"] and existing["text"]==r["text"] for existing in merged_reviews):
                merged_reviews.append(r)

    sorted_reviews = sorted(merged_reviews, key=lambda r: r["page"])
    last_completed_page = max([r["page"] for r in sorted_reviews])

    if intermediate:
        mid_file = f'{base_file_name}_p{last_completed_page}.csv'
        for f in mid_files:
            os.remove(f)
        pd.DataFrame(sorted_reviews).to_csv(mid_file, index=False, encoding='utf-8-sig')
        log_info(f"[중간 저장] 페이지 {last_completed_page}, 리뷰 {len(sorted_reviews)}, 파일: {mid_file}")
    else:
        final_file = f'{base_file_name}.csv'
        pd.DataFrame(sorted_reviews).to_csv(final_file, index=False, encoding='utf-8-sig')
        log_info(f"[최종 저장 완료] 페이지 {last_completed_page}, 리뷰 {len(sorted_reviews)}, 파일: {final_file}")

# --- 오류 처리 & 재시작 ---
def handle_error(msg):
    log_warning(msg)
    save_reviews(intermediate=True)
    try:
        driver.quit()
    except:
        pass
    human_sleep(1, 3)#3,6

# --- 크롬 초기화 ---
def init_driver():
    options = Options()
    options.add_argument("window-size=1920x1080")
    options.add_argument("disable-gpu")
    options.add_argument("disable-infobars")
    options.add_argument("disable-extensions")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=options)
    drv.implicitly_wait(4)
    return drv

# --- CAPTCHA 체크 ---
def check_captcha():
    try:
        driver.find_element(By.ID, "rcpt_answer")
        return True
    except NoSuchElementException:
        return False

# --- AJAX 리뷰 안정화 ---
def wait_for_reviews(timeout=20):
    start = time.time()
    last_count = 0
    while time.time() - start < timeout:
        reviews = driver.find_elements(By.CSS_SELECTOR, 'li.PxsZltB5tV')
        if len(reviews) != last_count:
            last_count = len(reviews)
            human_sleep(0.3, 0.5)
        else:
            return reviews
    return reviews

# --- 페이지 이동 ---
def go_to_page(target_page, fast_mode=False):
    try:
        current_page = max([r["page"] for r in all_reviews], default=1) if all_reviews else 1
        if fast_mode:
            target_block_start = ((target_page - 1) // 10) * 10 + 1
            while current_page + 10 <= target_block_start:
                try:
                    next_block_btn = driver.find_element(By.XPATH, '//a[text()="다음" and contains(@class, "I3i1NSoFdB")]')
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_block_btn)
                    driver.execute_script("arguments[0].click();", next_block_btn)
                    current_page += 10
                    human_sleep(0.8, 1.5)
                except NoSuchElementException:
                    log_warning(f"[알림] 블록 이동 버튼 없음. 현재 페이지 {current_page}")
                    break
        while current_page < target_page:
            try:
                page_btn = driver.find_element(By.LINK_TEXT, str(current_page + 1))
                driver.execute_script("arguments[0].scrollIntoView(true);", page_btn)
                driver.execute_script("arguments[0].click();", page_btn)
                current_page += 1
                human_sleep(WAIT_MIN, WAIT_MAX)
            except NoSuchElementException:
                try:
                    next_block_btn = driver.find_element(By.XPATH, '//a[text()="다음" and contains(@class, "I3i1NSoFdB")]')
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_block_btn)
                    driver.execute_script("arguments[0].click();", next_block_btn)
                    human_sleep(2.0, 3.0)
                except NoSuchElementException:
                    raise Exception(f"페이지 {current_page+1} 버튼 없음")
        return True
    except Exception as e:
        raise Exception(f"페이지 이동 실패: {e}")

# --- 메인 수집 루프 ---
stop_scraping = False
while not stop_scraping:
    retry_once = True
    try:
        driver = init_driver()
        driver.get(url)
        human_sleep(3.5, 7.0)

        # 페이지 진입 후, 리뷰 탭 위치까지 스크롤 다운
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        human_sleep(1, 2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        human_sleep(1, 2)
        
        # 리뷰 탭 클릭
        try:
            review_tab = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-name="REVIEW"]'))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", review_tab)
            driver.execute_script("arguments[0].click();", review_tab)
            #human_sleep(3.5, 7.0)
        except TimeoutException:
            log_warning("리뷰 탭 클릭 실패. 재시작 후 중간 저장부터 재수집")
            save_reviews(intermediate=True)
            driver.quit()
            human_sleep(1, 3)#2,5
            continue

        # 이전 중간 저장 불러오기
        mid_files = sorted(glob.glob(f"{base_file_name}_p*.csv"))
        if mid_files:
            last_file = mid_files[-1]
            log_info(f"[이어서 수집] 마지막 중간 저장 파일 불러오기: {last_file}")
            df = pd.read_csv(last_file, encoding='utf-8-sig')
            all_reviews = df.to_dict('records')
            page_count = max([r["page"] for r in all_reviews])
        else:
            all_reviews = []
            page_count = 1

        if page_count > 1:
            log_info(f"[이어서 수집] 페이지 {page_count}부터 시작")
            go_to_page(page_count, fast_mode=True)

        while page_count <= MAX_PAGES and not stop_scraping:
            log_info(f"페이지 {page_count} 수집 중...")
            try:
                # CAPTCHA 대기 최대 5분
                if check_captcha():
                    log_warning("자동 봇 방지 문제 발생! 최대 5분 동안 브라우저에서 CAPTCHA를 풀어주세요.")
                    wait_time = 0
                    max_wait = 300  # 5분
                    interval = 5
                    while wait_time < max_wait:
                        human_sleep(interval, interval)
                        wait_time += interval
                        if not check_captcha():
                            log_info(f"CAPTCHA 해결됨. 대기 시간: {wait_time}초")
                            break
                    else:
                        log_warning("5분 초과! CAPTCHA가 아직 남아 있음")

                human_sleep(WAIT_MIN, WAIT_MAX)
                reviews = wait_for_reviews(timeout=20)
                if not reviews:
                    raise Exception("리뷰 로딩 실패")

                for review in reviews:
                    try:
                        more_btn = review.find_element(By.CSS_SELECTOR, 'a.DpXj3MxW8W')
                        driver.execute_script("arguments[0].click();", more_btn)
                        human_sleep(0.05, 0.15)#1,5
                    except (NoSuchElementException, ElementClickInterceptedException):
                        pass
                    text = review.find_element(By.CSS_SELECTOR, 'div.KqJ8Qqw082 span.MX91DFZo2F').text if review.find_elements(By.CSS_SELECTOR, 'div.KqJ8Qqw082 span.MX91DFZo2F') else ""
                    date = review.find_element(By.CSS_SELECTOR, 'span.MX91DFZo2F').text if review.find_elements(By.CSS_SELECTOR, 'span.MX91DFZo2F') else ""
                    author = review.find_element(By.CSS_SELECTOR, 'strong.MX91DFZo2F').text if review.find_elements(By.CSS_SELECTOR, 'strong.MX91DFZo2F') else ""
                    rating = review.find_element(By.CSS_SELECTOR, 'em.n6zq2yy0KA').text if review.find_elements(By.CSS_SELECTOR, 'em.n6zq2yy0KA') else ""
                    option_text = review.find_element(By.CSS_SELECTOR, 'div.b_caIle8kC').text if review.find_elements(By.CSS_SELECTOR, 'div.b_caIle8kC') else ""
                    if not any(r["author"]==author and r["date"]==date and r["text"]==text for r in all_reviews):
                        all_reviews.append({"page":page_count,"author":author,"date":date,"rating":rating,"text":text,"option":option_text})
                    #human_sleep(0.2, 0.5)

                if page_count % MID_SAVE == 0:
                    save_reviews(intermediate=True)

                # 다음 페이지 이동
                try:
                    go_to_page(page_count + 1)
                    page_count += 1
                    retry_once = True
                except Exception as e:
                    msg = str(e)
                    if "페이지 이동 실패" in msg and "버튼 없음" in msg:
                        if retry_once:
                            log_warning(f"페이지 {page_count+1} 이동 실패! 1회 재시도 중...")
                            retry_once = False
                            save_reviews(intermediate=True)
                            driver.quit()
                            human_sleep(3, 5)
                            break
                        else:
                            log_info(f"페이지 {page_count+1} 이동 실패 연속 발생! 마지막 페이지로 간주 후 종료")
                            save_reviews(intermediate=True)
                            save_reviews(intermediate=False)
                            driver.quit()
                            sys.exit(0)
                    else:
                        handle_error(f"[재시작] 페이지 {page_count}에서 오류 발생: {msg}")
                        break

            except Exception as e:
                handle_error(f"[재시작] 페이지 {page_count}에서 오류 발생: {e}")
                break

    except Exception as e:
        log_warning(f"[외부 루프] 오류 발생: {e}")
        human_sleep(3, 5)
        if stop_scraping:
            break

save_reviews(intermediate=False)
driver.quit()
