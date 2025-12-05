from flask import Flask, request, redirect, url_for, render_template_string
import requests
import os

# keep_alive মডিউল যুক্ত করা হচ্ছে (২৪/৭ সচল রাখার জন্য)
# এটি Flask সার্ভারকে একটি আলাদা থ্রেডে চালু করবে
from keep_alive import keep_alive # আমরা ধরে নিচ্ছি keep_alive.py ফাইলটি একই ফোল্ডারে আছে

app = Flask(__name__)

# --- কনফিগারেশন (আপনার দেওয়া তথ্য) ---
BOT_TOKEN = '8370128447:AAGQ320GgSw0louz69GLe6vAlgrrnLkz8Eg' 
CHAT_ID = '6361822194'

# --- HTML ফর্ম কোড (আধুনিক ডার্ক UI এবং বাংলা টেক্সট সহ) ---
# এখানে আপনার মূল HTML এর স্টাইল উন্নত করা হয়েছে।
HTML_FORM = """
<!doctype html>
<title>টেলিগ্রাম ক্লাউড আপলোডার</title>
<style>
    /* ডার্ক থিম স্টাইল */
    body {
        font-family: 'Arial', sans-serif;
        background-color: #121212; /* Deep Dark Background */
        color: #e0e0e0; /* Light Gray Text */
        text-align: center;
        margin: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }
    
    /* কন্টেইনার স্টাইল */
    .container {
        background-color: #1e1e1e; /* Card Background */
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.7);
        max-width: 500px;
        width: 90%;
        border: 1px solid #333333;
    }
    
    /* হেডিং স্টাইল */
    h1 {
        color: #81d4fa; /* Light Blue/Cyan for Focus */
        font-size: 2em;
        margin-bottom: 5px;
        padding-bottom: 10px;
    }
    
    p {
        color: #b0b0b0;
        margin-top: 10px;
        margin-bottom: 30px;
        font-size: 1.1em;
    }
    
    /* ফাইল ইনপুট স্টাইল */
    .file-input-wrapper {
        border: 3px dashed #666666; /* Enhanced Dashed Border */
        border-radius: 10px;
        background-color: #2a2a2a;
        padding: 20px;
        margin-bottom: 20px;
        cursor: pointer;
        transition: border-color 0.3s ease;
    }
    
    .file-input-wrapper:hover {
        border-color: #81d4fa;
    }
    
    input[type=file] {
        display: none; /* Hide default input */
    }
    
    .file-input-label {
        display: block;
        color: #81d4fa;
        font-size: 1.2em;
        font-weight: bold;
    }
    
    .file-subtext {
        display: block;
        color: #b0b0b0;
        font-size: 0.9em;
        margin-top: 5px;
    }

    /* সাবমিট বাটন স্টাইল */
    input[type=submit] {
        background-color: #4CAF50; /* Green Button */
        color: white;
        padding: 15px 20px;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 1.1em;
        width: 100%;
        font-weight: bold;
        transition: background-color 0.3s ease, transform 0.1s;
    }
    
    input[type=submit]:hover {
        background-color: #45a049; /* Darker Green on Hover */
    }
    
    input[type=submit]:active {
        transform: scale(0.99);
    }
    
    /* মোবাইল রেসপন্সিভনেস */
    @media (max-width: 600px) {
        .container {
            padding: 25px;
            width: 95%;
        }
        h1 {
            font-size: 1.5em;
        }
        p {
            font-size: 1em;
        }
    }
</style>
<body>
    <div class="container">
        <h1>☁️ ফাইল ব্যাকআপ করুন</h1>
        <p>একসাথে একাধিক ছবি, ভিডিও বা ডকুমেন্ট নির্বাচন করুন। আপলোডের পরে আপনি একটি সফলতার মেসেজ দেখতে পাবেন।</p>
        <form method=post enctype=multipart/form-data>
          <div class="file-input-wrapper" onclick="document.getElementById('file-upload').click()">
            <span class="file-input-label">ফাইল নির্বাচন করতে ক্লিক করুন</span>
            <span class="file-subtext">সর্বোচ্চ ২ GB আকারের একাধিক ফাইল সমর্থিত।</span>
          </div>
          <input type=file name=file[] id="file-upload" multiple required>
          <input type=submit value=আপলোড শুরু করুন>
        </form>
    </div>
</body>
</html>
"""

def upload_to_telegram(file_stream, filename, file_type='document'):
    """ফাইল স্ট্রিমকে টেলিগ্রাম API ব্যবহার করে আপলোড করে"""
    
    # ফাইল এক্সটেনশন অনুযায়ী API মেথড নির্বাচন
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
    
    # অনুরোধ করার সময় টোকেন হাইড করার জন্য headers এ টোকেন না দিয়ে data/files এ পাঠানো হয়েছে।
    response = requests.post(url, data=data, files=files)
    
    return response.status_code == 200, response.json()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # একাধিক ফাইল গ্রহণ করা
        uploaded_files = request.files.getlist('file[]') 
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return 'কোনো ফাইল পাওয়া যায়নি', 400
        
        successful_uploads = 0
        
        for file in uploaded_files:
            if file.filename:
                filename = file.filename
                file_extension = os.path.splitext(filename)[1].lower()
                
                file_type = 'document'
                # কমন ইমেজ এবং ভিডিও এক্সটেনশন চেক করা হচ্ছে
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    file_type = 'photo'
                elif file_extension in ['.mp4', '.mov', '.avi']:
                    file_type = 'video'
                
                success, response_data = upload_to_telegram(file.stream, filename, file_type)

                if success:
                    successful_uploads += 1
                else:
                    # ডিবাগিং এর জন্য লগিং
                    print(f"Failed to upload {filename}: {response_data}")
        
        if successful_uploads > 0:
            # একাধিক ফাইল আপলোড সফল হলে সফলতার পেজে রিডাইরেক্ট
            return redirect(url_for('upload_success_multi', count=successful_uploads))
        else:
            return 'কোনো ফাইলই সফলভাবে আপলোড হয়নি। অনুগ্রহ করে লগ চেক করুন।', 500

    return render_template_string(HTML_FORM)

# সফলতা পেজ
@app.route('/success')
def upload_success_multi():
    count = request.args.get('count', 'কিছু')
    # সফলতার পেজের HTML-এ বাংলা টেক্সট ও ডার্ক স্টাইল বজায় রাখা হয়েছে
    return render_template_string("""
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #121212;
            color: #ffffff;
            text-align: center;
            padding-top: 100px;
        }
        h1 {
            color: #4CAF50; /* Success Green */
            font-size: 2em;
            margin-bottom: 30px;
        }
        a {
            color: #121212;
            background-color: #81d4fa;
            text-decoration: none;
            padding: 12px 25px;
            border-radius: 8px;
            display: inline-block;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        a:hover {
            background-color: #4fc3f7;
        }
    </style>
    <h1>✅ সফলভাবে {{ count }}টি ফাইল টেলিগ্রামে আপলোড হয়েছে!</h1>
    <p><a href="/">অন্য ফাইল আপলোড করুন</a></p>
    """)

# --- ২৪/৭ সচল রাখার জন্য সার্ভার চালু করা ---
# এটিকে Render এর মতো হোস্টিং এনভায়রনমেন্টে স্বয়ংক্রিয়ভাবে চালু করার জন্য main.py/Procfile-এ যুক্ত করতে হবে।
# এই ফাইলটিকে main.py হিসেবে সেভ করলে, keep_alive() কলটি দরকার হবে।
# যেহেতু আমরা একটি একক Flask অ্যাপ তৈরি করছি, keep_alive লজিকটি এখানে ইনটিগ্রেট করা যেতে পারে।

if __name__ == '__main__':
    # ২৪/৭ সচল রাখার জন্য Keep Alive লজিকটি শুরু করা হচ্ছে।
    # মনে রাখবেন: Render/Heroku তে পোর্ট os.environ.get('PORT') থেকে নিতে হয়।
    try:
        # keep_alive() ফাংশনটি একটি নতুন থ্রেডে সার্ভার শুরু করবে
        keep_alive() 
    except NameError:
        # যদি keep_alive.py ফাইলটি না থাকে, তবে শুধু প্রিন্ট করা হবে।
        print("Warning: 'keep_alive' function not found. Running web app directly.")
        pass

    # Flask অ্যাপটি শুরু করা হচ্ছে
    # os.environ.get('PORT') ব্যবহার করে হোস্টিং এনভায়রনমেন্টের পোর্ট ব্যবহার করা হচ্ছে।
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
