from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests
import os
from typing import Optional

app = FastAPI()

TARGET_URL = os.getenv("TARGET_URL", "https://www.luyenthi123.com/member/128972")
COOKIE_FILE_PATH = os.getenv("COOKIE_FILE_PATH", "cookie_clean.txt")
MAX_RUNS = int(os.getenv("MAX_RUNS", "0"))  # 0 = no limit

class RunRequest(BaseModel):
    start_index: Optional[int] = 0
    limit: Optional[int] = None  # số cookie muốn chạy; None = tất cả

def do_work(start_index: int = 0, limit: Optional[int] = None):
    cnt = start_index
    processed = 0
    try:
        with open(COOKIE_FILE_PATH, 'r', encoding='utf-8') as file:
            for line in file:
                if limit is not None and processed >= limit:
                    break
                content = line.strip()
                if not content:
                    continue

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
                    # Ghi log đơn giản ra stdout (Render sẽ thu logs)
                    print(f"[{cnt}] Status: {response.status_code}")
                    print(f"[{cnt}] Body sample: {response.text[:200]}")
                except Exception as e:
                    print(f"[{cnt}] Request failed: {e}")

                cnt += 1
                processed += 1

                if MAX_RUNS and processed >= MAX_RUNS:
                    break
    except FileNotFoundError:
        print("Cookie file not found:", COOKIE_FILE_PATH)
    except Exception as e:
        print("Unexpected error in do_work:", e)

@app.post("/run")
def run_endpoint(req: RunRequest, background_tasks: BackgroundTasks):
    # Bảo vệ endpoint: có thể thêm token auth bằng env var
    api_key = os.getenv("API_KEY")
    # Nếu bạn muốn bắt buộc header Authorization, kiểm tra ở đây (ví dụ)
    # (Ở ví dụ này ta không kiểm tra để đơn giản; khuyến nghị bật auth)
    if not os.path.exists(COOKIE_FILE_PATH):
        raise HTTPException(status_code=400, detail="Cookie file not found on server.")
    background_tasks.add_task(do_work, req.start_index, req.limit)
    return {"status": "started", "start_index": req.start_index, "limit": req.limit}
