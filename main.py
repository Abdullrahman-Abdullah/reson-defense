from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from supabase import create_client
import requests
from typing import Optional

app = FastAPI()

# --- 1. إعدادات Supabase ---
SUPABASE_URL = "https://xeqptybimdbstpturgvc.supabase.co"
# تم استخدام مفتاح الـ Service Role لضمان تخطي أي قيود صلاحيات (Access Policies)
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlcXB0eWJpbWRic3RwdHVyZ3ZjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDYzMzg2MiwiZXhwIjoyMDg2MjA5ODYyfQ.xbFwC9PL9_OuCtY7mdYdjjkiSwfM6upMddMHhnqURxM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. إعدادات OneSignal ---
ONESIGNAL_APP_ID = "2eeb59a2-7292-43aa-961e-f40fc3239677"
# تم تصحيح المفتاح - تأكد من نسخه كاملاً بدون فراغات
ONESIGNAL_REST_KEY = "os_v2_app_f3vvtitssjb2vfq66qh4gi4wo53ffhh5cdbu4q5zgyjilfbw6wzxfsmsufeijqmkydzxqjkjo4234qcplfzxzds3ke7a4wnjiocycha"

class MotionData(BaseModel):
    status: str
    camera_name: str
    image_url: Optional[str] = None

def send_onesignal_notification(camera_name, file_url):
    """إرسال الإشعار مع تصحيح الهيدر لحل مشكلة 403"""
    url = "https://api.onesignal.com/notifications"
    
    # حل مشكلة 403: استخدام Basic Authentication مع مفتاح os_v2
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_REST_KEY}"
    }
    
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"],
        "headings": {"en": "🚨 رصد حركة متحركة!"},
        "contents": {"en": f"نشاط جديد من كاميرا: {camera_name}"},
        "big_picture": file_url, # لرؤية الـ GIF في الإشعار
        "android_accent_color": "FFFF0000",
        "priority": 10,
        "data": {"url": file_url}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"OneSignal Response: {response.status_code} - {response.text}")
        return response.status_code
    except Exception as e:
        print(f"OneSignal Error: {e}")
        return 500

@app.get("/")
def home():
    return {"message": "Defense System Server is Running"}

@app.post("/alert")
async def receive_alert(data: MotionData):
    """استقبال البيانات من جهاز الكمبيوتر"""
    try:
        # 1. تسجيل البيانات في قاعدة بيانات Supabase
        supabase.table("alerts").insert({
            "status": data.status,
            "camera_name": data.camera_name,
            "image_url": data.image_url
        }).execute()
        
        # 2. إرسال الإشعار الفوري للهاتف
        os_status = send_onesignal_notification(data.camera_name, data.image_url)
        
        return {
            "status": "success", 
            "database": "saved", 
            "onesignal_code": os_status
        }
    except Exception as e:
        print(f"Global Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/camIp")
async def get_camera_ip():
    """جلب عنوان IP الكاميرا من القاعدة"""
    try:
        res = supabase.table("cameras").select("ip_address").execute()
        if res.data:
            return {"ip_address": res.data[0]['ip_address']}
    except:
        pass
    return {"ip_address": 0}

# ملاحظة: uvicorn لا نحتاجه في Vercel لأنه يستخدم WSGI/ASGI خاص به
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
