from flask import Flask, request, redirect, url_for, render_template_string
import requests
import os

app = Flask(__name__)

# --- কনফিগারেশন (আপনার দেওয়া টোকেন এবং আইডি) ---
BOT_TOKEN = '8370128447:AAGQ320GgSw0louz69GLe6vAlgrrnLkz8Eg' 
CHAT_ID = '6361822194'

# HTML ফর্ম কোড
HTML_FORM = """
<!doctype html>
<title>টেলিগ্রাম ক্লাউড আপলোডার</title>
<h1>আপনার ব্যক্তিগত টেলিগ্রাম ক্লাউডে ফাইল আপলোড করুন</h1>
<p>মোবাইল বা পিসি থেকে ফাইল নির্বাচন করে আপলোড বাটনে ক্লিক করুন।</p>
<form method=post enctype=multipart/form-data>
  <input type=file name=file required>
  <input type=submit value=আপলোড করুন>
</form>
"""

def upload_to_telegram(file_stream, filename, file_type='document'):
    """ফাইল স্ট্রিমকে টেলিগ্রাম API ব্যবহার করে আপলোড করে"""
    
    # ফাইলের প্রকারভেদ অনুযায়ী API মেথড এবং ফাইল কী নির্ধারণ
    if file_type == 'photo':
        api_method = 'sendPhoto'
        file_key = 'photo'
    elif file_type == 'video':
        api_method = 'sendVideo'
        file_key = 'video'
    else:
        api_method = 'sendDocument'
        file_key = 'document'
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{api_method}"
    
    files = {file_key: (filename, file_stream)}
    data = {'chat_id': CHAT_ID, 'caption': f"Uploaded via Web: {filename}"}
    
    response = requests.post(url, data=data, files=files)
    
    return response.status_code == 200, response.json()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'কোনো ফাইল পাওয়া যায়নি', 400
        
        file = request.files['file']
        
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        # ফাইলের এক্সটেনশন দেখে তার প্রকারভেদ (photo/video/document) নির্ধারণ করা
        file_type = 'document'
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            file_type = 'photo'
        elif file_extension in ['.mp4', '.mov', '.avi']:
            file_type = 'video'
        
        success, response_data = upload_to_telegram(file.stream, filename, file_type)

        if success:
            return redirect(url_for('upload_success'))
        else:
            # টেলিগ্রামের এরর মেসেজ দেখাচ্ছে
            error_msg = response_data.get("description", "Unknown error")
            return f'টেলিগ্রাম আপলোডে ব্যর্থ। সমস্যা: {error_msg}', 500

    return render_template_string(HTML_FORM)

@app.route('/success')
def upload_success():
    return '<h1>✅ ফাইলটি সফলভাবে টেলিগ্রামে আপলোড হয়েছে!</h1><p><a href="/">অন্য ফাইল আপলোড করুন</a></p>'

# Render-এর জন্য কোনো লোকাল রান কোড দরকার নেই
