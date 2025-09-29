from flask import Flask, request, jsonify
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)

# Manual CORS handling
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/', methods=['OPTIONS'])
@app.route('/ask', methods=['OPTIONS'])
def handle_options():
    return '', 200

print("=" * 50)
print("🚀 Flask App Starting...")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"🔑 API Key loaded: {'✅ Yes' if gemini_api_key else '❌ No'}")
print("=" * 50)

# Load FAQ database
faq_db = {}
try:
    if os.path.exists("faq.json"):
        with open("faq.json", "r") as f:
            faq_db = json.load(f)
        print(f"📋 FAQ database loaded: {len(faq_db)} entries")
        for key in faq_db.keys():
            print(f"  - {key}")
    else:
        print("⚠️  faq.json not found - creating empty database")
except Exception as e:
    print(f"❌ Error loading FAQ: {e}")

# Root route - serves HTML interface
@app.route("/", methods=["GET"])
def home():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 24px;
            border-bottom: none;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .avatar {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: white;
            backdrop-filter: blur(10px);
        }
        
        .header-info h1 {
            font-size: 18px;
            font-weight: 600;
            color: white;
            margin-bottom: 2px;
        }
        
        .header-info p {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.8);
        }
        
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .message {
            display: flex;
            gap: 12px;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        
        .bot-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .user-avatar {
            background: linear-gradient(135deg, #48CAE4 0%, #0096C7 100%);
            color: white;
        }
        
        .message-content {
            max-width: 70%;
            background: #f8f9fa;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.4;
            color: #333;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #48CAE4 0%, #0096C7 100%);
            color: white;
        }
        
        .typing {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 18px;
            width: fit-content;
        }
        
        .dot {
            width: 6px;
            height: 6px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.4;
            }
            30% {
                transform: translateY(-8px);
                opacity: 1;
            }
        }
        
        .input-area {
            padding: 20px 24px;
            border-top: 1px solid #e5e5e5;
            background: white;
        }
        
        .suggestions {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        
        .suggestion {
            background: linear-gradient(135deg, #f8f9ff 0%, #e9f0ff 100%);
            border: 1px solid rgba(102, 126, 234, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            color: #667eea;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
        }
        
        .suggestion:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .input-container {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        
        .input-field {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 12px 16px;
            font-size: 15px;
            outline: none;
            resize: none;
            max-height: 100px;
            min-height: 44px;
            font-family: inherit;
        }
        
        .input-field:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-btn {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: all 0.3s;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        }
        
        .send-btn:hover:not(:disabled) {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a42a0 100%);
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        }
        
        .send-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .chat-area::-webkit-scrollbar {
            width: 4px;
        }
        
        .chat-area::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        
        @media (max-width: 768px) {
            .container {
                height: 100vh;
                border-radius: 0;
                margin: 0;
            }
            
            .message-content {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="avatar">🤖</div>
            <div class="header-info">
                <h1>AI Assistant</h1>
                <p>Online</p>
            </div>
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message">
                <div class="message-avatar bot-avatar">🤖</div>
                <div class="message-content">
                    Hi! I'm your AI assistant. Ask me anything about carbon credits, climate change, or any topic you're curious about.
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="suggestions">
                <button class="suggestion" onclick="askSample('what is a carbon credit')">Carbon credits</button>
                <button class="suggestion" onclick="askSample('what is mrv')">MRV</button>
                <button class="suggestion" onclick="askSample('what is blue carbon')">Blue carbon</button>
                <button class="suggestion" onclick="askSample('carbon price')">Carbon price</button>
            </div>
            <div class="input-container">
                <textarea class="input-field" id="messageInput" placeholder="Type your message..." rows="1"></textarea>
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">→</button>
            </div>
        </div>
    </div>

    <script>
        let isWaiting = false;
        
        function askSample(question) {
            document.getElementById('messageInput').value = question;
            sendMessage();
        }
        
        function addMessage(content, isUser = false) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : ''}`;
            
            messageDiv.innerHTML = `
                <div class="message-avatar ${isUser ? 'user-avatar' : 'bot-avatar'}">
                    ${isUser ? '👤' : '🤖'}
                </div>
                <div class="message-content">${content}</div>
            `;
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function showTyping() {
            const chatArea = document.getElementById('chatArea');
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message';
            typingDiv.id = 'typing';
            
            typingDiv.innerHTML = `
                <div class="message-avatar bot-avatar">🤖</div>
                <div class="typing">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            `;
            
            chatArea.appendChild(typingDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
        
        async function sendMessage() {
            if (isWaiting) return;
            
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, true);
            input.value = '';
            input.style.height = 'auto';
            
            isWaiting = true;
            sendBtn.disabled = true;
            showTyping();
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: message })
                });
                
                const data = await response.json();
                hideTyping();
                
                if (response.ok) {
                    addMessage(data.answer);
                } else {
                    addMessage(`Error: ${data.error || 'Something went wrong'}`, false);
                }
            } catch (error) {
                hideTyping();
                addMessage(`Network error: ${error.message}`, false);
            } finally {
                isWaiting = false;
                sendBtn.disabled = false;
                input.focus();
            }
        }
        
        // Auto resize textarea
        document.getElementById('messageInput').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
        
        // Send on Enter
        document.getElementById('messageInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
    '''

# Function to get answer from Gemini API
def get_gemini_answer(query):
    if not gemini_api_key:
        return "❌ Error: Gemini API key not found. Please check your .env file."
    
    print(f"🤖 Calling Gemini API for: {query}")
    
    # Correct Gemini API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Answer in maximum 50 words: {query}"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Correct way to extract text from Gemini response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        answer = parts[0]['text']
                        print(f"✅ Got answer from Gemini: {answer[:100]}...")
                        return answer
            
            print("⚠️  No valid content found in API response")
            return "No answer returned from Gemini API."
        
        else:
            error_msg = f"❌ API Error: {response.status_code} - {response.text}"
            print(error_msg)
            return error_msg
            
    except requests.exceptions.Timeout:
        return "❌ Timeout error: API request took too long"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {str(e)}"
    except json.JSONDecodeError as e:
        return f"❌ Error parsing API response: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# Flask route for asking questions
@app.route("/ask", methods=["POST"])
def ask():
    print("\n" + "="*30)
    print("📨 Received /ask request")
    
    try:
        # Check if request has JSON data
        if not request.json:
            print("❌ No JSON data in request")
            return jsonify({"error": "No JSON data provided"}), 400
        
        print(f"📝 Request data: {request.json}")
        
        query = request.json.get("question", "").strip()
        
        if not query:
            print("❌ No question provided")
            return jsonify({"error": "No question provided"}), 400
        
        print(f"❓ Question: {query}")
        query_lower = query.lower()
        
        # 1️⃣ Check FAQ (case-insensitive)
        print("🔍 Checking FAQ database...")
        for faq_key, faq_answer in faq_db.items():
            if faq_key.lower() in query_lower:
                print(f"✅ Found FAQ match: {faq_key}")
                return jsonify({"answer": faq_answer})
        
        print("📝 No FAQ match found")
        
        # 2️⃣ Live queries example
        if "carbon price" in query_lower:
            print("💰 Found carbon price query")
            return jsonify({"answer": "Current carbon price is $8.5 USD per tCO2e."})
        
        # 3️⃣ Fallback to Gemini API
        print("🤖 Using Gemini API fallback...")
        gemini_answer = get_gemini_answer(query)
        return jsonify({"answer": gemini_answer})
    
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

if __name__ == "__main__":
    print("🏃 Starting Flask server...")
    print("🌐 Access the app at: http://localhost:5000")
    
    try:
        app.run(debug=True, host='127.0.0.1', port=5000)
    except OSError as e:
        if "Address already in use" in str(e):
            print("⚠️  Port 5000 is busy, trying port 5001...")
            app.run(debug=True, host='127.0.0.1', port=5001)
        else:
            raise e