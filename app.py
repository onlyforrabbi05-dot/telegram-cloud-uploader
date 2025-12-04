from flask import Flask, request, redirect, url_for, render_template_string
import requests
import os

app = Flask(__name__)

# --- কনফিগারেশন (আপনার দেওয়া তথ্য) ---
BOT_TOKEN = '8370128447:AAGQ320GgSw0louz69GLe6vAlgrrnLkz8Eg' 
CHAT_ID = '6361822194'

# HTML ফর্ম কোড (আধুনিক ডার্ক UI এবং সেন্টারে টেক্সট সহ)
HTML_FORM = """
<!doctype html>
<title>টেলিগ্রাম ক্লাউড আপলোডার</title>
<style>
    /* ডার্ক থিম স্টাইল */
    body {
        font-family: 'Arial', sans-serif;
        background-color: #1a1a2e; /* Dark Blue-Purple Background */
        color: #ffffff; /* White Text */
        text-align: center;
        padding-top: 50px;
        margin: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 100vh;
    }
    
    /* কন্টেইনার স্টাইল */
    .container {
        background-color: #2c2c54; /* Slightly lighter container background */
        padding: 40px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        max-width: 500px;
        width: 90%;
    }
    
    /* হেডিং স্টাইল */
    h1 {
        color: #e5f7ff; /* Light Cyan Color for Heading */
        font-size: 1.8em;
        margin-bottom: 5px;
        border-bottom: 2px solid #5d5d81;
        padding-bottom: 10px;
    }
    
    p {
        color: #cccccc;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    
    /* ফাইল ইনপুট স্টাইল */
    input[type=file] {
        display: block;
        width: 100%;
        padding: 10px;
        margin-bottom: 20px;
        border: 2px dashed #5d5d81; /* Dashed Border */
        border-radius: 8px;
        background-color: #3b3b6b;
        color: #ffffff;
        cursor: pointer;
    }

    /* সাবমিট বাটন স্টাইল */
    input[type=submit] {
        background-color: #4CAF50; /* Green Button */
        color: white;
        padding: 12px 20px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1em;
        width: 100%;
        transition: background-color 0.3s ease;
    }
    
    input[type=submit]:hover {
        background-color: #45a049; /* Darker Green on Hover */
    }
    
    /* মোবাইল রেসপন্সিভনেস */
    @media (max-width: 600px) {
        .container {
            padding: 20px;
            max-width: 100%;
            border-radius: 0;
        }
    }
</style>
<body>
    <div class="container">
        <h1>☁️ Backup Your Photos and Files</h1>
        <p>একসাথে একাধিক ছবি বা ফাইল নির্বাচন করুন। প্রতিটি ফাইল ২ GB এর নিচে হতে হবে।</p>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file[] multiple required>
          <input type=submit value=আপলোড শুরু করুন>
        </form>
    </div>
</body>
</html>
"""

def upload_to_telegram(file_stream, filename, file_type='document'):
    """ফাইল স্ট্রিমকে টেলিগ্রাম API ব্যবহার করে আপলোড করে"""
    
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
        uploaded_files = request.files.getlist('file[]') 
        
        if not uploaded_files or uploaded_files[0].filename == '':
            return 'কোনো ফাইল পাওয়া যায়নি', 400
        
        successful_uploads = 0
        
        for file in uploaded_files:
            if file.filename:
                filename = file.filename
                file_extension = os.path.splitext(filename)[1].lower()
                
                file_type = 'document'
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    file_type = 'photo'
                elif file_extension in ['.mp4', '.mov', '.avi']:
                    file_type = 'video'
                
                success, response_data = upload_to_telegram(file.stream, filename, file_type)

                if success:
                    successful_uploads += 1
                else:
                    print(f"Failed to upload {filename}: {response_data}")
        
        if successful_uploads > 0:
            return redirect(url_for('upload_success_multi', count=successful_uploads))
        else:
            return 'কোনো ফাইলই সফলভাবে আপলোড হয়নি।', 500

    return render_template_string(HTML_FORM)

# সফলতা পেজ (কটি ফাইল আপলোড হলো তা দেখায়)
@app.route('/success')
def upload_success_multi():
    count = request.args.get('count', 'কিছু')
    return f"""
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background-color: #1a1a2e;
            color: #ffffff;
            text-align: center;
            padding-top: 100px;
        }}
        h1 {{
            color: #4CAF50;
        }}
        a {{
            color: #79d0f7;
            text-decoration: none;
            padding: 10px 15px;
            border: 1px solid #79d0f7;
            border-radius: 5px;
            margin-top: 20px;
            display: inline-block;
        }}
        a:hover {{
            background-color: #79d0f7;
            color: #1a1a2e;
        }}
    </style>
    <h1>✅ সফলভাবে {count}টি ফাইল টেলিগ্রামে আপলোড হয়েছে!</h1>
    <p><a href="/">অন্য ফাইল আপলোড করুন</a></p>
    """
