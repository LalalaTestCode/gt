# main.py
import sys
import time
import uuid
import logging
from typing import Dict, Any

import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException

# --- Cấu hình logging xuất ra stdout (Render sẽ hiển thị) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Cấu hình chung ---
URL = "https://www.luyenthi123.com/member/128972"
COOKIE_FILE = "cookie_clean.txt"      # file chứa mỗi dòng là một lt123_cookie
APP_LOG_FILE = "/tmp/fire_log.txt"    # file log phụ để kiểm chứng
REQUEST_TIMEOUT = 15                  # timeout cho mỗi request (giây)
DELAY_BETWEEN_REQUESTS = 0.1         # delay giữa các request (giây)

# Trạng thái job đơn giản lưu trong bộ nhớ (khi restart sẽ mất)
jobs: Dict[str, Dict[str, Any]] = {}

# --- helper: ghi log phụ vào file để dễ kiểm chứng ---
def append_log(text: str) -> None:
    try:
        with open(APP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {text}\n")
    except Exception as e:
        logger.error("Không thể ghi vào file log phụ: %s", e)

# --- hàm thực thi công việc (chạy trong background) ---
def fire_job(job_id: str) -> None:
    logger.info("Job %s: bắt đầu", job_id)
    append_log(f"Job {job_id}: started")
    jobs[job_id] = {"status": "running", "processed": 0, "total": 0}

    # Đọc file cookie
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        msg = f"Cookie file not found: {COOKIE_FILE}"
        logger.error(msg)
        append_log(f"Job {job_id}: {msg}")
        jobs[job_id].update({"status": "error", "error": msg})
        return
    except Exception as e:
        msg = f"Error reading cookie file: {e}"
        logger.error(msg)
        append_log(f"Job {job_id}: {msg}")
        jobs[job_id].update({"status": "error", "error": msg})
        return

    total = len(lines)
    jobs[job_id]["total"] = total
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
        # Cập nhật cookie (ví dụ thêm idx vào PHPSESSID để khác nhau)
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
            resp = session.get(URL, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            logger.info("Job %s [%d/%d] Status: %s CookieLen: %d", job_id, idx, total, resp.status_code, len(content))
            append_log(f"Job {job_id} [{idx}/{total}] Status: {resp.status_code} CookieLen: {len(content)}")
            jobs[job_id]["processed"] = idx
        except requests.RequestException as e:
            logger.error("Job %s [%d/%d] Request lỗi: %s", job_id, idx, total, e)
            append_log(f"Job {job_id} [{idx}/{total}] Request lỗi: {e}")
            # tiếp tục vòng lặp, nhưng ghi lỗi
        # tránh gửi quá nhanh
        time.sleep(DELAY_BETWEEN_REQUESTS)

    jobs[job_id]["status"] = "done"
    logger.info("Job %s: hoàn tất", job_id)
    append_log(f"Job {job_id}: finished")

# --- endpoint: khởi chạy background job ---
@app.post("/trigger")
def trigger(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "processed": 0, "total": 0}
    background_tasks.add_task(fire_job, job_id)
    logger.info("Đã queue job %s", job_id)
    append_log(f"Queued job {job_id}")
    return {"status": "started", "job_id": job_id}

# --- endpoint: chạy đồng bộ (dùng để test, blocking) ---
@app.post("/trigger_sync")
def trigger_sync():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "processed": 0, "total": 0}
    logger.info("Chạy sync job %s", job_id)
    append_log(f"Sync job {job_id} started")
    # chạy trực tiếp (blocking)
    fire_job(job_id)
    return {"status": jobs[job_id]["status"], "job_id": job_id, "processed": jobs[job_id]["processed"], "total": jobs[job_id]["total"]}

# --- endpoint: kiểm tra trạng thái job ---
@app.get("/job/{job_id}")
def job_status(job_id: str):
    info = jobs.get(job_id)
    if not info:
        raise HTTPException(status_code=404, detail="job_id not found")
    return info

# --- endpoint: lấy log phụ (một vài dòng cuối) ---
@app.get("/logs")
def get_logs(lines: int = 200):
    try:
        with open(APP_LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        return {"logs": [], "note": "No log file yet"}
    # trả về các dòng cuối
    tail = [l.rstrip("\n") for l in all_lines[-lines:]]
    return {"logs": tail}

# --- root để kiểm tra service alive ---
@app.get("/")
def root():
    return {"ok": True, "note": "Use POST /trigger to start background job or POST /trigger_sync to run synchronously."}
