from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client
import requests
from typing import Optional

app = FastAPI()


# --- إعدادات Supabase ---
SUPABASE_URL = "https://xeqptybimdbstpturgvc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlcXB0eWJpbWRic3RwdHVyZ3ZjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDYzMzg2MiwiZXhwIjoyMDg2MjA5ODYyfQ.xbFwC9PL9_OuCtY7mdYdjjkiSwfM6upMddMHhnqURxM" # المفتاح السري (Service Role)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- إعدادات OneSignal ---
ONESIGNAL_APP_ID = "2eeb59a2-7292-43aa-961e-f40fc3239677"
ONESIGNAL_REST_KEY = "os_v2_app_f3vvtitssjb2vfq66qh4gi4wo53ffhh5cdbu4q5zgyjilfbw6wzxfsmsufeijqmkydzxqjkjo4234qcplfzxzds3ke7a4wnjiocycha"

class MotionData(BaseModel):
    status: str
    camera_name: str
    image_url: Optional[str] = None

def send_onesignal_alert(camera_name, image_url):
    """إرسال التنبيه لهاتفك عبر OneSignal"""
    url = "https://onesignal.com/api/v1/notifications"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_REST_KEY}"
    }
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Subscribed Users"],
        "headings": {"en": "⚠️ رصد حركة!"},
        "contents": {"en": f"الكاميرا: {camera_name} رصدت نشاطاً"},
        "big_picture": image_url, # تظهر الصورة داخل الإشعار
        "data": {"img_url": image_url} # بيانات إضافية يقرأها تطبيق Kodular
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"OneSignal Response Status: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"OneSignal Error: {e}")
        return None

@app.post("/alert")
async def receive_alert(data: MotionData):
    try:
        # 1. الحفظ في جدول alerts في Supabase
        supabase.table("alerts").insert({
            "status": data.status,
            "camera_name": data.camera_name,
            "image_url": data.image_url
        }).execute()
        
        # 2. إرسال التنبيه فوراً
        send_onesignal_alert(data.camera_name, data.image_url)
        
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/camIp")
async def get_camera_ip():
    # جلب IP الكاميرا من جدول الكاميرات
    res = supabase.table("cameras").select("ip_address").execute()
    if res.data:
        return {"ip_address": res.data[0]['ip_address']}
    return {"ip_address": 0}

@app.get("/latest-image")
async def get_latest_image():
    # جلب آخر سطر تم إضافته في جدول التنبيهات
    res = supabase.table("alerts").select("image_url").order("created_at", desc=True).limit(1).execute()
    if res.data:
        return res.data[0]['image_url']
    return ""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)
