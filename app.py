import os
import requests
import json
from flask import Flask, request, jsonify, render_template_string

# --- Global Configuration (Canvas Variables) ---
try:
    # Render Dashboard (Environment Variables) থেকে সিক্রেট ডেটা লোড করা হচ্ছে।
    BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    # সতর্কীকরণ: যদি Render-এ এনভায়রনমেন্ট ভেরিয়েবল সেট না করা থাকে তবে নিচের ডিফল্ট মানগুলো ব্যবহার হবে।
    # ইউজার প্রদত্ত মানগুলি এখানে যুক্ত করা হয়েছে।
    BOT_TOKEN = "8370128447:AAGQ320GgSw0louz69GLe6vAlgrrnLkz8Eg" 
    CHAT_ID = "6361822194"   

APP_ID = os.getenv('__app_id', 'default-app-id')
USER_ID_PLACEHOLDER = "user-id-if-authenticated"

app = Flask(__name__)

TELEGRAM_UPLOAD_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
MAX_ALLOWED_SIZE_MB = 100 

# ত্রুটিমুক্ত এবং পরিষ্কার আপলোড ফাংশন
def upload_stream_to_telegram(bot_token, chat_id, file_stream, filename, file_size):
    """ফাইল স্ট্রিমকে টেলিগ্রাম API ব্যবহার করে আপলোড করে"""
    
    if file_size > MAX_ALLOWED_SIZE_MB * 1024 * 1024:
        return jsonify({
            "success": False, 
            "message": f"ফাইল সাইজ খুব বড়। অনুমোদিত সর্বোচ্চ সাইজ {MAX_ALLOWED_SIZE_MB} MB। আপনার ফাইলের সাইজ {file_size / (1024 * 1024):.2f} MB।"
        }), 400

    payload = {
        'chat_id': chat_id,
        'caption': f"Uploaded file: {filename}",
    }
    
    files = {
        'document': (filename, file_stream)
    }

    try:
        response = requests.post(TELEGRAM_UPLOAD_URL, data=payload, files=files)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('ok'):
            file_id = response_data['result']['document']['file_id']
            return jsonify({
                "success": True, 
                "message": f"'{filename}' ফাইলটি সফলভাবে টেলিগ্রাম ক্লাউডে আপলোড হয়েছে।",
                "file_id": file_id
            }), 200
        else:
            error_message = response_data.get('description', 'অজানা টেলিগ্রাম API ত্রুটি।')
            return jsonify({"success": False, "message": f"আপলোড ব্যর্থ হয়েছে: {error_message}"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"নেটওয়ার্ক বা অনুরোধ ত্রুটি: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"একটি অপ্রত্যাশিত ত্রুটি ঘটেছে: {str(e)}"}), 500


@app.route('/', methods=['GET'])
def index():
    # সম্পূর্ণ HTML, CSS (Tailwind) এবং JavaScript এখানে রেন্ডার করা হয়েছে
    
    html_content = f"""
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Cloud Uploader</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #0c1017; /* Very Dark Blue/Black */
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .card-bg {{
            background-color: #1a1f26; /* Darker Card Background */
            border: 1px solid #2d333b;
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
            animation: fadeIn 0.8s ease-out;
        }}
        .accent-color {{
            background-color: #8b5cf6; /* Vibrant Purple */
        }}
        .accent-text {{
            color: #a78bfa;
        }}
        /* Drag and Drop Area Styling */
        .file-input-wrapper {{
            cursor: pointer;
            border: 3px dashed #374151; /* Darker dashed border */
            transition: border-color 0.3s, background-color 0.3s;
        }}
        .file-input-wrapper:hover {{
            border-color: #8b5cf6;
            background-color: #1f2a37; /* Slight hover dark */
        }}
        .progress-bar {{
            transition: width 0.4s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body class="min-h-screen p-4">
    <div class="w-full max-w-xl">
        <div class="card-bg p-8 rounded-2xl shadow-2xl">
            <h1 class="text-3xl font-extrabold text-white mb-2 text-center">Telegram Uploader</h1>
            <p class="text-gray-400 mb-8 text-center text-sm">টেলিগ্রাম ক্লাউডে ফাইল আপলোড করুন। (সর্বোচ্চ সাইজ: {MAX_ALLOWED_SIZE_MB} MB)</p>
            
            <!-- System Status -->
            <div class="flex justify-center text-xs text-gray-500 mb-6 border-b border-gray-700 pb-3">
                <span class="mr-4">App ID: <span class="font-mono text-gray-400">{APP_ID}</span></span>
                <span>User: <span class="font-mono text-gray-400">{USER_ID_PLACEHOLDER}</span></span>
            </div>

            <!-- Upload Form -->
            <form id="uploadForm" class="space-y-6">
                
                <!-- File Input Area (Drag & Drop) -->
                <div class="file-input-wrapper p-10 rounded-xl text-center">
                    <input type="file" id="fileInput" name="file" class="hidden" required>
                    <label for="fileInput" id="fileLabel" class="flex flex-col items-center justify-center text-gray-400">
                        <!-- Upload Icon -->
                        <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="accent-text mb-3"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                        
                        <span class="text-white font-bold text-lg">ফাইল নির্বাচন করুন বা এখানে টেনে আনুন</span>
                        <span class="text-sm text-gray-500 mt-1">সর্বোচ্চ {MAX_ALLOWED_SIZE_MB} MB পর্যন্ত সমর্থিত।</span>
                    </label>
                </div>

                <!-- Status/Progress Area -->
                <div id="statusArea" class="hidden">
                    <p class="text-sm accent-text mb-2 font-semibold flex justify-between">
                        <span>আপলোড স্ট্যাটাস</span>
                        <span id="progressPercentage">0%</span>
                    </p>
                    <div class="w-full bg-gray-700 rounded-full h-2.5">
                        <div id="progressBar" class="accent-color h-2.5 rounded-full progress-bar" style="width: 0%"></div>
                    </div>
                    <p id="statusMessage" class="mt-2 text-sm text-gray-400"></p>
                </div>

                <!-- Submit Button -->
                <button type="submit" id="submitButton" class="w-full accent-color text-white font-bold py-3 rounded-xl hover:bg-violet-700 transition duration-300 shadow-xl shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed">
                    আপলোড শুরু করুন
                </button>
            </form>

            <!-- Success/Error Alert -->
            <div id="alertBox" class="mt-6 p-4 rounded-xl hidden" role="alert">
                <p id="alertText" class="font-medium flex items-center"></p>
            </div>
            
        </div>
    </div>

    <script>
        const form = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        const fileLabel = document.getElementById('fileLabel');
        const submitButton = document.getElementById('submitButton');
        const statusArea = document.getElementById('statusArea');
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const statusMessage = document.getElementById('statusMessage');
        const alertBox = document.getElementById('alertBox');
        const alertText = document.getElementById('alertText');
        const fileInputWrapper = document.querySelector('.file-input-wrapper');
        const MAX_SIZE_BYTES = {MAX_ALLOWED_SIZE_MB} * 1024 * 1024;

        // --- Drag and Drop Logic ---
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {{
            fileInputWrapper.addEventListener(eventName, preventDefaults, false);
        }});

        function preventDefaults (e) {{
            e.preventDefault();
            e.stopPropagation();
        }}

        ['dragenter', 'dragover'].forEach(eventName => {{
            fileInputWrapper.addEventListener(eventName, () => fileInputWrapper.classList.add('border-purple-400', 'bg-violet-900/10'), false);
        }});

        ['dragleave', 'drop'].forEach(eventName => {{
            fileInputWrapper.addEventListener(eventName, () => fileInputWrapper.classList.remove('border-purple-400', 'bg-violet-900/10'), false);
        }});

        fileInputWrapper.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {{
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {{
                fileInput.files = files;
                updateFileLabel(files[0]);
            }}
        }}

        // --- File Selection Logic ---
        fileInput.addEventListener('change', (e) => {{
            const file = e.target.files[0];
            if (file) {{
                updateFileLabel(file);
            }} else {{
                resetFileLabel();
            }}
        }});

        function updateFileLabel(file) {{
            fileLabel.innerHTML = \`
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="accent-text mb-3"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="12" x2="12" y1="18" y2="12"/><line x1="9" x2="15" y1="15" y2="15"/></svg>
                <span class="text-white font-bold text-lg">\${{file.name}}</span>
                <span class="text-sm text-gray-400 mt-1">সাইজ: \${{(file.size / 1024 / 1024).toFixed(2)}} MB - \${{file.size > MAX_SIZE_BYTES ? '⚠️ খুব বড়!' : '✅ প্রস্তুত'}}</span>
            \`;
        }}

        function resetFileLabel() {{
            fileLabel.innerHTML = \`
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="accent-text mb-3"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                <span class="text-white font-bold text-lg">ফাইল নির্বাচন করুন বা এখানে টেনে আনুন</span>
                <span class="text-sm text-gray-500 mt-1">সর্বোচ্চ {MAX_ALLOWED_SIZE_MB} MB পর্যন্ত সমর্থিত।</span>
            \`;
        }}

        // --- Form Submission Logic ---
        form.addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const file = fileInput.files[0];
            if (!file) {{
                showAlert('অনুগ্রহ করে একটি ফাইল নির্বাচন করুন।', 'bg-red-900/50 border border-red-500 text-red-300', '⚠️');
                return;
            }}

            if (file.size > MAX_SIZE_BYTES) {{
                showAlert(\`ফাইলটি {MAX_ALLOWED_SIZE_MB} MB-এর বেশি, আপলোড ব্যর্থ হতে পারে।\`, 'bg-yellow-900/50 border border-yellow-500 text-yellow-300', '⚠️');
                return;
            }}

            // UI আপডেট করুন
            submitButton.disabled = true;
            submitButton.textContent = 'আপলোড হচ্ছে... সার্ভারে অপেক্ষা করুন';
            statusArea.classList.remove('hidden');
            progressBar.style.width = '10%';
            progressPercentage.textContent = '10%';
            statusMessage.textContent = 'ফাইল সার্ভারে পাঠানো হচ্ছে... (এটি বড় ফাইলের জন্য সময় নিতে পারে)';
            alertBox.classList.add('hidden');

            const formData = new FormData();
            formData.append('file', file);

            try {{
                // ফেইক প্রোগ্রেস (কারণ সার্ভার থেকে সরাসরি প্রোগ্রেস ডেটা পাওয়া কঠিন)
                const tempProgress = setInterval(() => {{
                    const currentWidth = parseInt(progressBar.style.width);
                    if (currentWidth < 90) {{
                        const newWidth = currentWidth + 5;
                        progressBar.style.width = \`\${{newWidth}}%\`;
                        progressPercentage.textContent = \`\${{newWidth}}%\`;
                    }} else {{
                        clearInterval(tempProgress);
                    }}
                }}, 1500); 

                const response = await fetch('/upload', {{
                    method: 'POST',
                    body: formData,
                }});

                clearInterval(tempProgress); 

                const result = await response.json();
                
                if (response.ok && result.success) {{
                    progressBar.style.width = '100%';
                    progressPercentage.textContent = '100%';
                    statusMessage.textContent = 'আপলোড সফল হয়েছে! ফাইল আইডি পাওয়া গেছে।';
                    showAlert(\`আপলোড সফল: \${{result.message}}\`, 'bg-green-900/50 border border-green-500 text-green-300', '🎉');
                }} else {{
                    progressBar.style.width = '100%';
                    progressPercentage.textContent = '100%';
                    statusMessage.textContent = 'আপলোড ব্যর্থ হয়েছে।';
                    showAlert(\`আপলোড ব্যর্থ: \${{result.message}}\`, 'bg-red-900/50 border border-red-500 text-red-300', '❌');
                }}
                
            }} catch (error) {{
                console.error('Fetch error:', error);
                progressBar.style.width = '100%';
                progressPercentage.textContent = 'ত্রুটি';
                statusMessage.textContent = 'নেটওয়ার্ক ত্রুটি বা সার্ভার সংযোগ বিচ্ছিন্ন।';
                showAlert('নেটওয়ার্ক ত্রুটি। বিস্তারিত জানতে কনসোল চেক করুন।', 'bg-red-900/50 border border-red-500 text-red-300', '🚨');
            }} finally {{
                submitButton.disabled = false;
                submitButton.textContent = 'আপলোড শুরু করুন';
            }}
        }});
        
        function showAlert(message, className, icon) {{
            alertBox.className = \`mt-6 p-4 rounded-xl \${{className}}\`;
            alertText.innerHTML = \`<span class="mr-2">\${{icon}}</span> \${{message}}\`;
            alertBox.classList.remove('hidden');
        }}

        resetFileLabel();
    </script>
</body>
</html>
    """
    return render_template_string(html_content)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "অনুরোধে কোনো ফাইল অংশ পাওয়া যায়নি।"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"success": False, "message": "কোনো ফাইল নির্বাচন করা হয়নি।"}), 400

    if file:
        filename = file.filename
        file_stream = file.stream
        # কন্টেন্ট লেন্থ ব্যবহার করা হচ্ছে ফাইল সাইজের জন্য (Render/Gunicorn দ্বারা সরবরাহকৃত)
        file_size = request.content_length or 0 
        
        return upload_stream_to_telegram(BOT_TOKEN, CHAT_ID, file_stream, filename, file_size)
    
    return jsonify({"success": False, "message": "ফাইল প্রসেসিং এর সময় অজানা ত্রুটি।"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
