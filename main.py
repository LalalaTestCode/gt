# main.py
import requests
import time
from fastapi import FastAPI, BackgroundTasks
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

URL = "https://www.luyenthi123.com/member/128972"
COOKIE_FILE = "cookie_clean.txt"  # đổi tên cho rõ ràng

def fire():
    logging.info("Bắt đầu chạy fire()")
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Không tìm thấy file: {COOKIE_FILE}")
        return

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.luyenthi123.com/member/864039"
    }

    for idx, content in enumerate(lines, start=1):
        cookies = {
            "PHPSESSID": f"eevba7e9akfpka2phs2mbbpc5i{idx}",
            "_ga": "GA1.2.1193990977.1773491054",
            "_gid": "GA1.2.1388131978.1773491054",
            "_fbp": "fb.1.1773491054332.513919956909999410",
            "Visitor_Returning": "true",
            "lt123_pass": "MDAwMDAw",
            "lt123_user": "aGVsbG94eXo1NQ%3D%3D",
            "lt123_cookie": content
        }

        try:
            resp = session.get(URL, headers=headers, cookies=cookies, timeout=15)
            logging.info(f"[{idx}] Status: {resp.status_code} CookieLen: {len(content)}")
            # nếu cần lưu kết quả, ghi vào file log hoặc DB ở đây
        except requests.RequestException as e:
            logging.error(f"[{idx}] Request lỗi: {e}")

        # tránh gửi quá nhanh
        time.sleep(0.5)

    logging.info("Kết thúc fire()")

@app.post("/trigger")
def trigger(background_tasks: BackgroundTasks):
    background_tasks.add_task(fire)
    return {"status": "started"}
