from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from typing import Optional, List

app = FastAPI()

# Cấu hình từ env
TARGET_URL = os.getenv("TARGET_URL", "https://www.luyenthi123.com/member/128972")
COOKIE_SOURCE = os.getenv("COOKIE_FILE_PATH", "cookie_clean.txt")  # có thể là đường dẫn file hoặc URL
MAX_RUNS = int(os.getenv("MAX_RUNS", "0"))  # 0 = no limit
API_KEY = os.getenv("API_KEY")  # nếu muốn bật auth, đặt API_KEY trong env

# CORS (cho phép frontend gọi từ trình duyệt). Thay "*" bằng domain cụ thể ở production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def load_cookies_from_source() -> List[str]:
    """
    Nếu COOKIE_SOURCE là URL thì tải nội dung qua HTTP một lần.
    Nếu là file cục bộ thì đọc file.
    Trả về danh sách cookie (mỗi dòng một cookie, đã strip).
    """
    try:
        if COOKIE_SOURCE.startswith("http://") or COOKIE_SOURCE.startswith("https://"):
            resp = requests.get(COOKIE_SOURCE, timeout=15)
            resp.raise_for_status()
            lines = resp.text.splitlines()
        else:
            with open(COOKIE_SOURCE, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
        return [ln.strip() for ln in lines if ln.strip()]
    except Exception as e:
        print("Failed to load cookies:", e)
        return []

def do_work(start_index: int = 0, limit: Optional[int] = None):
    """
    Thực hiện vòng lặp gọi TARGET_URL với từng cookie.
    Ghi log ra stdout để Render thu logs.
    """
    cookies_list = load_cookies_from_source()
    if not cookies_list:
        print("No cookies to process.")
        return

    cnt = start_index
    processed = 0
    for idx in range(start_index, len(cookies_list)):
        if limit is not None and processed >= limit:
            break

        content = cookies_list[idx]
        cookies = {
            "PHPSESSID": "eevba7e9akfpka2phs2mbbpc5i" + str(cnt),
            "_ga": "GA1.2.1193990977.1773491054",
            "_gid": "GA1.2.1388131978.1773491054",
            "_fbp": "fb.1.1773491054332.513919956909999410",
            "Visitor_Returning": "true",
            "lt123_pass": "MDAwMDAw",
            "lt123_user": "aGVsbG94eXo1NQ%3D%3D",
            "lt123_cookie": content
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/145.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.luyenthi123.com/member/864039"
        }

        try:
            response = requests.get(TARGET_URL, headers=headers, cookies=cookies, timeout=15)
            print(f"[{cnt}] Status: {response.status_code}")
            print(f"[{cnt}] Body sample: {response.text[:200]}")
        except Exception as e:
            print(f"[{cnt}] Request failed: {e}")

        cnt += 1
        processed += 1

        if MAX_RUNS and processed >= MAX_RUNS:
            break

@app.get("/run")
def run_get(start_index: Optional[int] = 0, limit: Optional[int] = None, request: Request = None, background_tasks: BackgroundTasks = None):
    """
    Truy cập GET /run sẽ khởi động công việc nền.
    Tham số query:
      - start_index (int) : chỉ số bắt đầu (mặc định 0)
      - limit (int) : số cookie muốn xử lý (mặc định None = tất cả)
    Nếu API_KEY được đặt trong env, client phải gửi header: Authorization: Bearer <API_KEY>
    """
    # Nếu bật API_KEY, kiểm tra header Authorization
    if API_KEY:
        auth = request.headers.get("authorization")
        if not auth or not auth.lower().startswith("bearer ") or auth.split(" ", 1)[1] != API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Kiểm tra file/nguồn cookie tồn tại (nếu là file cục bộ)
    if not (COOKIE_SOURCE.startswith("http://") or COOKIE_SOURCE.startswith("https://")):
        if not os.path.exists(COOKIE_SOURCE):
            raise HTTPException(status_code=400, detail=f"Cookie file not found: {COOKIE_SOURCE}")

    # Bắt đầu công việc nền
    background_tasks.add_task(do_work, int(start_index or 0), (int(limit) if limit is not None else None))
    return {"status": "started", "start_index": int(start_index or 0), "limit": (int(limit) if limit is not None else None)}

@app.get("/health")
def health():
    return {"status": "ok"}
