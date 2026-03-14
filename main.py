import requests
from fastapi import FastAPI, BackgroundTasks
import time

app = FastAPI()
cnt = 0
url = "https://www.luyenthi123.com/member/128972"
def fire():
# Mở file để đọc ('r') với bảng mã utf-8
    with open('cookie_clean.json', 'r', encoding='utf-8') as file:
        for line in file:
            # line.strip() giúp loại bỏ các ký tự xuống dòng dư thừa (\n)
            content = line.strip()
            if content:  # Kiểm tra nếu dòng không trống
                cookies = {
                    "PHPSESSID": "eevba7e9akfpka2phs2mbbpc5i" + str(cnt),
                    "_ga": "GA1.2.1193990977.1773491054",
                    "_gid": "GA1.2.1388131978.1773491054",
                    "_fbp": "fb.1.1773491054332.513919956909999410",
                    "Visitor_Returning": "true",
                    "lt123_pass": "MDAwMDAw",
                    "lt123_user": "aGVsbG94eXo1NQ%3D%3D",
                    "lt123_cookie": content
                    # thêm các cookie khác nếu cần
                }

                # Headers cơ bản
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

                # Gửi request
                response = requests.get(url, headers=headers, cookies=cookies)
                cnt+=1

        
@app.get("/trigger")
async def trigger_requests(background_tasks: BackgroundTasks):
    # Đưa tác vụ gửi 100 request vào chạy ngầm
    background_tasks.add_task(fire)
    
    # Phản hồi ngay lập tức cho bạn biết lệnh đã được nhận
    return {"status": "success", "message": "Đã nhận lệnh! Render đang bắn 100 requests trong nền."}