import cv2
import requests
import time
import os
from supabase import create_client

# --- الإعدادات ---
SERVER_URL = "https://defense-system-mocha.vercel.app/"
SUPABASE_URL = "https://xeqptybimdbstpturgvc.supabase.co"
SUPABASE_KEY = "sb_publishable_vax-h0FYB0Xu2QUfWivnvw_fEUHoVan"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image(file_path, file_name):
# هون بنرفع الصةرة على bucket
    try:
        with open(file_path, "rb") as f:
            supabase.storage.from_("alert-images").upload(file_name, f)
        # بنرجع رابط الصورة
        url = supabase.storage.from_("alert-images").get_public_url(file_name)
        return url
    except Exception as e:
        print(f"Upload Error: {e}")
        return None

try:
    res = requests.get(f"{SERVER_URL}/camIp")
    CAM_URL = res.json().get("ip_address", 0)
except:
    CAM_URL = 0

cap = cv2.VideoCapture(0) #بنغيرها بعدين 0 كاميرا اللابتوب
ret, frame1 = cap.read()
ret, frame2 = cap.read()
last_alert_time = 0

while cap.isOpened():
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    movement = False
    for contour in contours:
        if cv2.contourArea(contour) < 5000: continue
        movement = True
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 0, 255), 2)

    if movement and (time.time() - last_alert_time > 15):
        # تجهيز الصورة وحذفها مشان المساحة
        img_filename = f"alert_{int(time.time())}.jpg"
        cv2.imwrite(img_filename, frame1)
        
        # Bucket
        public_url = upload_image(img_filename, img_filename)
        
        if public_url:
            payload = {
                "status": "Movement Detected",
                "camera_name": "Home_Cam_1",
                "image_url": public_url
            }
            requests.post(f"{SERVER_URL}/alert", json=payload)
            print(">>> Image Uploaded and Alert Sent!")
            
        os.remove(img_filename) # delete p   
        last_alert_time = time.time()

    cv2.imshow(" Reson | defense", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()