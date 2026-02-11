from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client
import requests
from typing import Optional

app = FastAPI()

# --- إعدادات Supabase ---
# ملاحظة: يفضل استخدام مفتاح (service_role) بدلاً من (publishable) لتجنب مشاكل الصلاحيات
SUPABASE_URL = "https://xeqptybimdbstpturgvc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlcXB0eWJpbWRic3RwdHVyZ3ZjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDYzMzg2MiwiZXhwIjoyMDg2MjA5ODYyfQ.xbFwC9PL9_OuCtY7mdYdjjkiSwfM6upMddMHhnqURxM" 
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- إعدادات OneSignal ---
ONESIGNAL_APP_ID = "2eeb59a2-7292-43aa-961e-f40fc3239677"
# ضع هنا المفتاح الذي يبدأ بـ os_v2_app... الذي نسخته وظهر لك لمرة واحدة
ONESIGNAL_REST_KEY = "os_v2_app_f3vvtitssjb2vfq66qh4gi4wo6hf6nveogsefdm4yp6wvjc3k6qfswqzx3tebguk734vmhnvhjz5zv6vpak6cm6nsb65xlw4efloi7a" 

class MotionData(BaseModel):
    status: str
    camera_name: str
    image_url: Optional[str] = None

def send_onesignal_alert(camera_name, image_url):
    """إرسال التنبيه باستخدام أحدث معايير OneSignal 2026"""
    # تحديث الرابط للمسار الرسمي الجديد
    url = "https://api.onesignal.com/notifications"
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        # التغيير الجوهري: استخدام 'key' بدلاً من 'Basic' للمفاتيح الحديثة
        "Authorization": f"key {ONESIGNAL_REST_KEY}"
    }
    
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["All"], # "All" تضمن وصولها لجميع الأجهزة المسجلة
        "headings": {"en": "⚠️ تنبيه: رصد حركة!"},
        "contents": {"en": f"الكاميرا [{camera_name}] رصدت جسماً غريباً"},
        "big_picture": image_url,
        "data": {"img_url": image_url},
        "android_accent_color": "FFFF0000", # لون أحمر للتنبيه
        "priority": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        # طباعة النتيجة في Logs لمراقبة النجاح أو الفشل
        print(f"OneSignal Log: Status {response.status_code}, Response: {response.text}")
        return response.status_code
    except Exception as e:
        print(f"OneSignal Critical Error: {e}")
        return None

@app.post("/alert")
async def receive_alert(data: MotionData):
    try:
        # 1. الحفظ في Supabase
        supabase.table("alerts").insert({
            "status": data.status,
            "camera_name": data.camera_name,
            "image_url": data.image_url
        }).execute()
        
        # 2. محاولة إرسال التنبيه
        status = send_onesignal_alert(data.camera_name, data.image_url)
        
        return {"status": "success", "onesignal_status": status}
    except Exception as e:
        print(f"Alert Processing Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/latest-image")
async def get_latest_image():
    # جلب آخر صورة مع ترتيب تنازلي حسب الوقت
    try:
        res = supabase.table("alerts").select("image_url").order("created_at", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]['image_url']
    except:
        pass
    return ""

@app.get("/camIp")
async def get_camera_ip():
    res = supabase.table("cameras").select("ip_address").execute()
    if res.data:
        return {"ip_address": res.data[0]['ip_address']}
    return {"ip_address": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)

