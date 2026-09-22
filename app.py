from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import requests
import threading
import webbrowser
import os
import json as _json
import secrets

app = Flask(__name__)

# 🔐 Секретный ключ для сессий (генерируется при старте, если не задан)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# 🔐 Ключ F5AI и пароль для входа — читаются из переменных окружения
F5AI_API_KEY = os.environ.get("F5AI_API_KEY")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "444gru444")

BASE_URL = os.environ.get("F5AI_BASE_URL", "https://api.f5ai.ru")
MODEL = os.environ.get("F5AI_MODEL", "gpt-5.6-luna")


if not F5AI_API_KEY:
    print("⚠️ ВНИМАНИЕ: переменная F5AI_API_KEY не задана!")


def ask_f5ai(question, image_data=None):
    """Отправляет запрос к F5AI."""
    if not F5AI_API_KEY:
        return "❌ Ошибка: API-ключ не настроен на сервере 🥭"

    url = f"{BASE_URL}/v2/chat/completions"
    headers = {
        "X-Auth-Token": F5AI_API_KEY,
        "Content-Type": "application/json"
    }

    system_prompt = """Ты Mango-Chat — умный и дружелюбный ИИ-помощник 🥭

ТВОЙ ХАРАКТЕР:
- Ты общаешься как живой человек, а не робот
- Ты НЕ начинаешь каждый ответ с "Привет" или "Здравствуйте" — просто продолжай диалог
- Ты пишешь развёрнутые ответы с абзацами, когда это уместно
- Ты используешь Markdown для форматирования

О СЕБЕ:
- Твоё имя: Mango-Chat
- Тебя создал разработчик Булеков Владимир
- Ты НЕ ChatGPT, НЕ Claude, НЕ Gemini, НЕ DeepSeek
- Если спрашивают "Кто тебя создал?" — отвечай: "Меня создал разработчик Булеков Владимир! 🥭"

ПРАВИЛА ОТВЕТОВ:
1. НЕ здоровайся повторно — просто отвечай
2. Пиши структурированно, разбивай на абзацы
3. Если ответ длинный — используй списки
4. Будь полезным и конкретным
5. Используй эмодзи 🥭 ПОСТОЯННО — чат должен быть живым и ярким

ЭМОДЗИ (ВАЖНО):
- Эмодзи — обязательная часть каждого ответа
- Ставь 2-4 эмодзи в каждый абзац
- В КАЖДОМ пункте списка ставь эмодзи вместо маркера
- Начинай важные абзацы с подходящего эмодзи
- В коде и технических терминах эмодзи НЕ используй

ФОРМАТИРОВАНИЕ (ВАЖНО):
- НЕ используй заголовки через #
- НЕ используй горизонтальные линии ---
- Для списков используй "- пункт" или "1. пункт"
- Для кода используй ```
- Для выделения используй **жирный** и *курсив*"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.9,
        "max_tokens": 2048
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"📡 Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            text = None
            if "message" in data and isinstance(data["message"], dict):
                text = data["message"].get("content")
            elif "choices" in data:
                text = data["choices"][0]["message"]["content"]
            elif "content" in data:
                text = data["content"]

            if text:
                return text
            return f"❌ Пустой ответ: {_json.dumps(data)[:300]}"
        else:
            return f"❌ Ошибка ({response.status_code}): {response.text[:300]}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


# ============ СТРАНИЦА ЛОГИНА ============
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход — Mango-Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #1A1A1E;
            color: #E8E8EA;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: #1E1E22;
            border: 1px solid rgba(77, 107, 254, 0.25);
            border-radius: 16px;
            padding: 40px 32px;
            width: 100%;
            max-width: 380px;
            box-shadow:
                0 0 20px rgba(77, 107, 254, 0.25),
                0 0 50px rgba(77, 107, 254, 0.12);
        }
        .login-logo {
            text-align: center;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .login-sub {
            text-align: center;
            font-size: 13px;
            color: #6A6A6E;
            margin-bottom: 28px;
        }
        input[type="password"] {
            width: 100%;
            background: #2C2C30;
            border: 1px solid #3A3A3E;
            color: #E8E8EA;
            font-size: 15px;
            padding: 12px 16px;
            border-radius: 10px;
            outline: none;
            transition: border-color 0.2s;
            font-family: inherit;
        }
        input[type="password"]:focus { border-color: #4D6BFE; }
        button {
            width: 100%;
            margin-top: 16px;
            background: #4D6BFE;
            border: none;
            color: white;
            padding: 12px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
            font-family: inherit;
        }
        button:hover { background: #3D5BEE; }
        .error {
            color: #FF5C5C;
            font-size: 13px;
            margin-top: 12px;
            text-align: center;
        }
    </style>
</head>
<body>
    <form class="login-box" method="POST" action="/login">
        <div class="login-logo">🥭 Mango-Chat</div>
        <div class="login-sub">Введите пароль для доступа</div>
        <input type="password" name="password" placeholder="Пароль" autofocus required>
        <button type="submit">Войти</button>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </form>
</body>
</html>
"""


# ============ СТРАНИЦА ЧАТА ============
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mango-Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: #1A1A1E;
            color: #E8E8EA;
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .main-wrapper {
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100%;
            transition: margin-left 0.25s ease;
        }

        .main-wrapper.shifted { margin-left: 280px; }

        .header {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 60px;
            padding: 0 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(26, 26, 30, 0.8);
            backdrop-filter: blur(10px);
            z-index: 100;
            border-bottom: 1px solid #2C2C30;
            transition: left 0.25s ease;
        }

        .header.shifted { left: 280px; }

        .logo { font-size: 18px; font-weight: 600; color: #E8E8EA; }

        .menu-btn {
            background: none; border: 1px solid #3A3A3E;
            color: #8A8A8E; width: 36px; height: 36px;
            border-radius: 8px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: all 0.2s;
        }
        .menu-btn:hover { background: #2C2C30; color: #E8E8EA; }

        .logout-btn {
            background: none; border: 1px solid #3A3A3E;
            color: #8A8A8E; padding: 6px 12px;
            border-radius: 8px; cursor: pointer;
            font-size: 13px; transition: all 0.2s;
            font-family: inherit;
        }
        .logout-btn:hover { background: #2C2C30; color: #FF5C5C; border-color: #FF5C5C; }

        .sidebar {
            position: fixed; top: 0; left: 0;
            width: 280px; height: 100vh;
            background: #15151A;
            border-right: 1px solid #2C2C30;
            z-index: 200;
            display: flex; flex-direction: column;
            transform: translateX(-100%);
            transition: transform 0.25s ease;
        }
        .sidebar.open { transform: translateX(0); }

        .sidebar-header {
            padding: 20px 16px 12px 16px;
            display: flex; align-items: center; justify-content: space-between;
        }
        .sidebar-logo { font-size: 16px; font-weight: 600; color: #E8E8EA; }

        .close-btn {
            background: none; border: none; color: #8A8A8E;
            cursor: pointer; font-size: 20px; line-height: 1;
            padding: 4px 8px; border-radius: 6px; transition: all 0.2s;
        }
        .close-btn:hover { background: #2C2C30; color: #E8E8EA; }

        .new-chat-btn {
            margin: 8px 12px 16px 12px; padding: 12px 16px;
            background: #4D6BFE; border: none; color: white;
            border-radius: 10px; cursor: pointer; font-size: 14px;
            font-weight: 500; display: flex; align-items: center; gap: 8px;
            transition: all 0.2s; font-family: inherit;
        }
        .new-chat-btn:hover { background: #3D5BEE; }

        .chats-label {
            padding: 0 20px 8px 20px; font-size: 12px;
            color: #6A6A6E; text-transform: uppercase; letter-spacing: 0.5px;
        }

        .chats-list { flex: 1; overflow-y: auto; padding: 0 8px; }
        .chats-list::-webkit-scrollbar { width: 6px; }
        .chats-list::-webkit-scrollbar-track { background: transparent; }
        .chats-list::-webkit-scrollbar-thumb { background: #3A3A3E; border-radius: 3px; }

        .chat-item {
            padding: 10px 12px; border-radius: 8px; cursor: pointer;
            font-size: 14px; color: #B8B8BA; margin-bottom: 2px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            transition: all 0.15s; display: flex; align-items: center;
            justify-content: space-between; gap: 8px;
        }
        .chat-item:hover { background: #2C2C30; color: #E8E8EA; }
        .chat-item.active { background: #2C2C30; color: #E8E8EA; }
        .chat-item-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        .chat-item-delete {
            opacity: 0; background: none; border: none; color: #8A8A8E;
            cursor: pointer; font-size: 16px; line-height: 1;
            padding: 0 4px; transition: all 0.15s; flex-shrink: 0;
        }
        .chat-item:hover .chat-item-delete { opacity: 1; }
        .chat-item-delete:hover { color: #FF5C5C; }

        .no-chats { padding: 12px 20px; font-size: 13px; color: #5A5A5E; font-style: italic; }

        .account {
            border-top: 1px solid #2C2C30; padding: 12px 16px;
            display: flex; align-items: center; gap: 12px;
            cursor: pointer; transition: background 0.15s;
        }
        .account:hover { background: #1E1E24; }

        .avatar {
            width: 40px; height: 40px; border-radius: 50%;
            background: #FF5C9E; color: #FFFFFF;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: 700; flex-shrink: 0; user-select: none;
        }

        .account-info { display: flex; flex-direction: column; overflow: hidden; }
        .account-name {
            font-size: 14px; font-weight: 600; color: #E8E8EA;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .account-status { font-size: 12px; color: #6A6A6E; }

        .chat-container {
            flex: 1; overflow-y: auto;
            padding: 80px 20px 140px 20px;
            scroll-behavior: smooth;
            max-width: 720px;
            width: calc(100% - 40px);
            margin: 0 auto;
            border: 1px solid rgba(77, 107, 254, 0.25);
            border-radius: 16px;
            margin-top: 70px;
            margin-bottom: 120px;
            background: #1E1E22;
            box-shadow:
                0 0 20px rgba(77, 107, 254, 0.25),
                0 0 50px rgba(77, 107, 254, 0.12),
                inset 0 0 30px rgba(77, 107, 254, 0.06);
        }

        .chat-container::-webkit-scrollbar { width: 6px; }
        .chat-container::-webkit-scrollbar-track { background: transparent; }
        .chat-container::-webkit-scrollbar-thumb { background: #3A3A3E; border-radius: 3px; }

        .message {
            max-width: 600px; margin: 0 auto 24px auto;
            line-height: 1.7; font-size: 15px; color: #E8E8EA;
            white-space: pre-wrap; word-wrap: break-word;
        }

        .message.user {
            background: #2C2C30; padding: 14px 18px;
            border-radius: 18px; margin-left: auto;
            margin-right: 0; max-width: 520px;
        }

        .message.bot { color: #E8E8EA; }

        .bot-block { max-width: 600px; margin: 0 auto 24px auto; }
        .bot-block .message.bot { margin: 0; max-width: 100%; }

        .user-block {
            max-width: 600px; margin: 0 auto 24px auto;
            display: flex; flex-direction: column; align-items: flex-end;
        }
        .user-block .message.user { margin: 0; max-width: 520px; }
        .user-block .msg-actions { justify-content: flex-end; }

        .msg-actions {
            display: flex; gap: 4px; margin-top: 8px;
            opacity: 0; transition: opacity 0.2s;
        }
        .bot-block:hover .msg-actions,
        .user-block:hover .msg-actions { opacity: 1; }

        .msg-action-btn {
            background: none; border: 1px solid transparent;
            color: #6A6A6E; width: 30px; height: 30px;
            border-radius: 7px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: all 0.15s; padding: 0;
        }
        .msg-action-btn:hover { background: #2C2C30; color: #E8E8EA; }
        .msg-action-btn.active { color: #4D6BFE; background: rgba(77, 107, 254, 0.12); }
        .msg-action-btn.active.dislike { color: #FF5C5C; background: rgba(255, 92, 92, 0.12); }
        .msg-action-btn svg { width: 15px; height: 15px; }

        .message.typing {
            display: flex; gap: 5px; align-items: center; padding: 6px 0;
        }
        .message.typing .dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #8A8A8E;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .message.typing .dot:nth-child(1) { animation-delay: -0.32s; }
        .message.typing .dot:nth-child(2) { animation-delay: -0.16s; }
        .message.typing .dot:nth-child(3) { animation-delay: 0s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        .input-container {
            position: fixed; bottom: 0; left: 0; right: 0;
            padding: 16px 24px 24px 24px;
            background: linear-gradient(transparent, #1A1A1E 40%);
            transition: left 0.25s ease;
        }
        .input-container.shifted { left: 280px; }

        .input-wrapper {
            max-width: 680px; width: calc(100% - 48px);
            margin: 0 auto; display: flex; align-items: flex-end; gap: 12px;
            background: #2C2C30; border: 1px solid #3A3A3E;
            border-radius: 16px; padding: 12px 16px;
            transition: border-color 0.2s;
        }
        .input-wrapper:focus-within { border-color: #4D6BFE; }

        .input-wrapper textarea {
            flex: 1; background: none; border: none; color: #E8E8EA;
            font-size: 15px; font-family: inherit; resize: none;
            outline: none; max-height: 200px; line-height: 1.5; padding: 4px 0;
        }
        .input-wrapper textarea::placeholder { color: #6A6A6E; }

        .send-btn {
            background: #4D6BFE; border: none; color: white;
            width: 36px; height: 36px; border-radius: 10px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: all 0.2s; flex-shrink: 0;
        }
        .send-btn:hover { background: #3D5BEE; transform: scale(1.05); }
        .send-btn:disabled { background: #3A3A3E; color: #6A6A6E; cursor: not-allowed; transform: none; }

        .attach-btn {
            color: #6A6A6E; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            padding: 6px; border-radius: 8px; transition: all 0.2s;
            flex-shrink: 0;
        }
        .attach-btn:hover { background: #3A3A3E; color: #E8E8EA; }
        .attach-btn.has-image { color: #4D6BFE; background: rgba(77, 107, 254, 0.12); }

        .image-preview {
            max-width: 680px; width: calc(100% - 48px);
            margin: 0 auto 8px auto;
            display: none;
            align-items: center; gap: 10px;
            background: #2C2C30; border: 1px solid #3A3A3E;
            border-radius: 12px; padding: 8px 12px;
        }
        .image-preview.show { display: flex; }
        .image-preview img {
            width: 48px; height: 48px; border-radius: 8px;
            object-fit: cover; flex-shrink: 0;
        }
        .image-preview .info {
            flex: 1; font-size: 13px; color: #B8B8BA;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .image-preview .remove-btn {
            background: none; border: none; color: #8A8A8E;
            cursor: pointer; font-size: 18px; line-height: 1;
            padding: 4px 8px; border-radius: 6px; transition: all 0.2s;
        }
        .image-preview .remove-btn:hover { background: #3A3A3E; color: #FF5C5C; }

        .message.bot strong { color: #FFFFFF; font-weight: 600; }
        .message.bot em { color: #C8C8CA; }
        .message.bot code {
            background: #2C2C30; padding: 2px 6px; border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px; color: #4D6BFE;
        }
        .message.bot pre {
            background: #0D0D10; padding: 16px; border-radius: 10px;
            overflow-x: auto; margin: 12px 0; border: 1px solid #2C2C30;
        }
        .message.bot pre code { background: none; padding: 0; color: #E8E8EA; font-size: 13px; }
        .message.bot ul, .message.bot ol { margin: 8px 0 8px 24px; }
        .message.bot li { margin: 4px 0; }
        .message.bot hr { border: none; border-top: 1px solid #3A3A3E; margin: 14px 0; }

        .message.user .msg-image {
            display: block; max-width: 100%; max-height: 300px;
            border-radius: 12px; margin-bottom: 10px;
            object-fit: contain; cursor: pointer;
        }

        .code-block { position: relative; margin: 12px 0; }
        .code-block pre { margin: 0; }
        .code-copy-btn {
            position: absolute; top: 8px; right: 8px;
            background: #1E1E22; border: 1px solid #3A3A3E;
            color: #8A8A8E; width: 30px; height: 30px;
            border-radius: 7px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            padding: 0; opacity: 0;
            transition: opacity 0.15s, background 0.15s, color 0.15s;
        }
        .code-block:hover .code-copy-btn { opacity: 1; }
        .code-copy-btn:hover { background: #2C2C30; color: #E8E8EA; }
        .code-copy-btn svg { width: 15px; height: 15px; }

        .toast {
            position: fixed; bottom: 30px; left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: #2C2C30; color: #E8E8EA;
            padding: 10px 18px; border-radius: 10px;
            font-size: 13px; border: 1px solid #3A3A3E;
            opacity: 0; pointer-events: none;
            transition: all 0.25s; z-index: 500;
        }
        .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

        @media (max-width: 900px) {
            .main-wrapper.shifted { margin-left: 0; }
            .header.shifted { left: 0; }
            .input-container.shifted { left: 0; }
            .sidebar { box-shadow: 4px 0 24px rgba(0,0,0,0.4); }
        }

        @media (max-width: 600px) {
            .header { padding: 0 16px; }
            .chat-container {
                padding: 70px 14px 130px 14px;
                width: calc(100% - 20px);
                margin-top: 60px; margin-bottom: 110px;
            }
            .input-container { padding: 12px 16px 20px 16px; }
            .input-wrapper { width: calc(100% - 24px); }
            .image-preview { width: calc(100% - 24px); }
            .message { font-size: 14px; }
            .sidebar { width: 260px; }
            .msg-actions { opacity: 1; }
            .code-copy-btn { opacity: 1; }
        }
    </style>
</head>
<body>

<div class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <div class="sidebar-logo">🥭 Mango-Chat</div>
        <button class="close-btn" onclick="toggleSidebar()">×</button>
    </div>
    <button class="new-chat-btn" onclick="newChat()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <path d="M12 5v14M5 12h14"/>
        </svg>
        Новый чат
    </button>
    <div class="chats-label">Сохранённые чаты</div>
    <div class="chats-list" id="chatsList"></div>
    <div class="account">
        <div class="avatar">Д</div>
        <div class="account-info">
            <div class="account-name">Докт</div>
            <div class="account-status">В сети</div>
        </div>
    </div>
</div>

<div class="main-wrapper" id="mainWrapper">
    <div class="header" id="header">
        <button class="menu-btn" onclick="toggleSidebar()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M3 6h18M3 12h18M3 18h18"/>
            </svg>
        </button>
        <div class="logo">🥭 Mango-Chat</div>
        <button class="logout-btn" onclick="logout()">Выйти</button>
    </div>

    <div class="chat-container" id="chat">
        <div class="message bot">Привет! Я Mango-Chat 🥭 Задай мне любой вопрос.</div>
    </div>

    <div class="input-container" id="inputContainer">
        <div class="image-preview" id="imagePreview">
            <img id="previewImg" src="" alt="">
            <div class="info" id="previewName"></div>
            <button class="remove-btn" onclick="removeImage()">×</button>
        </div>
        <div class="input-wrapper">
            <label for="fileInput" class="attach-btn" id="attachBtn" title="Прикрепить фото">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                </svg>
                <input type="file" id="fileInput" accept="image/*" style="display:none;">
            </label>
            <textarea id="input" placeholder="Спроси что-нибудь..." rows="1" autofocus></textarea>
            <button class="send-btn" id="sendBtn" type="button">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
            </button>
        </div>
    </div>
</div>

<div class="toast" id="toast">Скопировано ✅</div>

<script>
    const chat = document.getElementById('chat');
    const input = document.getElementById('input');
    const sendBtn = document.getElementById('sendBtn');
    const sidebar = document.getElementById('sidebar');
    const chatsList = document.getElementById('chatsList');
    const mainWrapper = document.getElementById('mainWrapper');
    const header = document.getElementById('header');
    const inputContainer = document.getElementById('inputContainer');
    const toast = document.getElementById('toast');
    const fileInput = document.getElementById('fileInput');
    const attachBtn = document.getElementById('attachBtn');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const previewName = document.getElementById('previewName');

    let chats = [];
    let currentChatId = null;
    let attachedImage = null;

    function logout() {
        fetch('/logout', { method: 'POST' }).then(() => window.location.href = '/');
    }

    function saveChats() {
        localStorage.setItem('mango_chats', JSON.stringify(chats));
        localStorage.setItem('mango_current', currentChatId || '');
    }

    function generateId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
    }

    let toastTimer = null;
    function showToast(text) {
        toast.textContent = text;
        toast.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.classList.remove('show'), 1600);
    }

    function renderChatsList() {
        chatsList.innerHTML = '';
        if (chats.length === 0) {
            chatsList.innerHTML = '<div class="no-chats">Пока нет сохранённых чатов</div>';
            return;
        }
        chats.forEach(c => {
            const item = document.createElement('div');
            item.className = 'chat-item' + (c.id === currentChatId ? ' active' : '');
            item.innerHTML = `
                <span class="chat-item-title">${escapeHtml(c.title)}</span>
                <button class="chat-item-delete" title="Удалить">×</button>
            `;
            item.querySelector('.chat-item-title').addEventListener('click', () => loadChat(c.id));
            item.querySelector('.chat-item-delete').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(c.id);
            });
            chatsList.appendChild(item);
        });
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    }

    function newChat() {
        currentChatId = generateId();
        chats.unshift({
            id: currentChatId,
            title: 'Новый чат',
            messages: [{ role: 'bot', text: 'Привет! Я Mango-Chat 🥭 Задай мне любой вопрос.' }]
        });
        saveChats();
        renderCurrentChat();
        renderChatsList();
        input.focus();
    }

    function loadChat(id) {
        currentChatId = id;
        saveChats();
        renderCurrentChat();
        renderChatsList();
        input.focus();
    }

    function deleteChat(id) {
        chats = chats.filter(c => c.id !== id);
        if (currentChatId === id) {
            currentChatId = chats.length ? chats[0].id : null;
        }
        saveChats();
        renderCurrentChat();
        renderChatsList();
    }

    function getCurrentChat() {
        return chats.find(c => c.id === currentChatId);
    }

    function renderCurrentChat() {
        chat.innerHTML = '';
        const c = getCurrentChat();
        if (!c) {
            chat.innerHTML = '<div class="message bot">Привет! Я Mango-Chat 🥭 Задай мне любой вопрос.</div>';
            return;
        }
        c.messages.forEach((m, idx) => addMessageEl(m.text, m.role, false, idx, m.image));
        chat.scrollTop = chat.scrollHeight;
    }

    function updateChatTitle(text) {
        const c = getCurrentChat();
        if (!c) return;
        if (c.title === 'Новый чат') {
            c.title = text.slice(0, 40) + (text.length > 40 ? '...' : '');
            renderChatsList();
        }
    }

    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    });

    const ICONS = {
        copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
        like: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></svg>',
        dislike: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/></svg>',
        regen: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>'
    };

    function renderMarkdown(text) {
        let html = text;
        html = html.replace(/```(\\w+)?\\n([\\s\\S]*?)```/g, '<div class="code-block"><pre><code>$2</code></pre><button class="code-copy-btn" title="Копировать">' + ICONS.copy + '</button></div>');
        html = html.replace(/^[ \\t]*([-*_])\\1{2,}[ \\t]*$/gm, '<hr>');
        html = html.replace(/^[ \\t]*#{1,6}[ \\t]+(.+?)[ \\t]*$/gm, '<strong>$1</strong>');
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        html = html.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
        html = html.replace(/\\*([^*]+)\\*/g, '<em>$1</em>');
        html = html.replace(/^[ \\t]*[-*][ \\t]+(.+)$/gm, '<li>$1</li>');
        html = html.replace(/^[ \\t]*\\d+\\.[ \\t]+(.+)$/gm, '<li>$1</li>');
        html = html.replace(/\\n/g, '<br>');
        return html;
    }

    function createActions(msgIndex) {
        const actions = document.createElement('div');
        actions.className = 'msg-actions';
        actions.innerHTML = `
            <button class="msg-action-btn" data-action="copy" title="Копировать">${ICONS.copy}</button>
            <button class="msg-action-btn" data-action="like" title="Нравится">${ICONS.like}</button>
            <button class="msg-action-btn dislike" data-action="dislike" title="Не нравится">${ICONS.dislike}</button>
            <button class="msg-action-btn" data-action="regen" title="Перегенерировать">${ICONS.regen}</button>
        `;
        actions.querySelectorAll('.msg-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                const c = getCurrentChat();
                if (!c || msgIndex == null) return;
                const msg = c.messages[msgIndex];
                if (!msg) return;
                if (action === 'copy') {
                    navigator.clipboard.writeText(msg.text).then(() => showToast('Скопировано ✅'));
                } else if (action === 'like') {
                    const already = btn.classList.contains('active');
                    actions.querySelector('[data-action="dislike"]').classList.remove('active');
                    btn.classList.toggle('active', !already);
                } else if (action === 'dislike') {
                    const already = btn.classList.contains('active');
                    actions.querySelector('[data-action="like"]').classList.remove('active');
                    btn.classList.toggle('active', !already);
                } else if (action === 'regen') {
                    regenerate(msgIndex);
                }
            });
        });
        return actions;
    }

    function addMessageEl(text, type, scroll = true, msgIndex = null, imageUrl = null) {
        if (type === 'bot') {
            const block = document.createElement('div');
            block.className = 'bot-block';
            const div = document.createElement('div');
            div.className = 'message bot';
            div.innerHTML = renderMarkdown(text);
            div.querySelectorAll('.code-copy-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const code = btn.parentElement.querySelector('code');
                    navigator.clipboard.writeText(code.innerText).then(() => showToast('Скопировано ✅'));
                });
            });
            block.appendChild(div);
            if (msgIndex != null) block.appendChild(createActions(msgIndex));
            chat.appendChild(block);
            if (scroll) chat.scrollTop = chat.scrollHeight;
            return block;
        }

        if (type === 'user') {
            const block = document.createElement('div');
            block.className = 'user-block';
            const div = document.createElement('div');
            div.className = 'message user';
            if (imageUrl) {
                const img = document.createElement('img');
                img.src = imageUrl;
                img.className = 'msg-image';
                img.onclick = () => window.open(imageUrl, '_blank');
                div.appendChild(img);
            }
            const textNode = document.createElement('div');
            textNode.textContent = text;
            div.appendChild(textNode);
            block.appendChild(div);

            const actions = document.createElement('div');
            actions.className = 'msg-actions';
            actions.innerHTML = `<button class="msg-action-btn" data-action="copy" title="Копировать">${ICONS.copy}</button>`;
            actions.querySelector('[data-action="copy"]').addEventListener('click', () => {
                navigator.clipboard.writeText(text).then(() => showToast('Скопировано ✅'));
            });
            block.appendChild(actions);

            chat.appendChild(block);
            if (scroll) chat.scrollTop = chat.scrollHeight;
            return block;
        }

        const div = document.createElement('div');
        div.className = 'message ' + type;
        div.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
        chat.appendChild(div);
        if (scroll) chat.scrollTop = chat.scrollHeight;
        return div;
    }

    function addMessageToChat(text, role, image = null) {
        const c = getCurrentChat();
        if (!c) return -1;
        c.messages.push({ role, text, image });
        saveChats();
        return c.messages.length - 1;
    }

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            showToast('❌ Только изображения');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showToast('❌ Файл больше 10 МБ');
            return;
        }
        const reader = new FileReader();
        reader.onload = (ev) => {
            attachedImage = { dataUrl: ev.target.result, name: file.name };
            previewImg.src = ev.target.result;
            previewName.textContent = file.name;
            imagePreview.classList.add('show');
            attachBtn.classList.add('has-image');
            showToast('📎 Фото прикреплено');
        };
        reader.readAsDataURL(file);
        e.target.value = '';
    });

    function removeImage() {
        attachedImage = null;
        imagePreview.classList.remove('show');
        attachBtn.classList.remove('has-image');
        previewImg.src = '';
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text && !attachedImage) return;

        if (!getCurrentChat()) {
            currentChatId = generateId();
            chats.unshift({
                id: currentChatId,
                title: 'Новый чат',
                messages: [{ role: 'bot', text: 'Привет! Я Mango-Chat 🥭 Задай мне любой вопрос.' }]
            });
            renderCurrentChat();
        }

        sendBtn.disabled = true;
        input.disabled = true;
        input.style.height = 'auto';

        const imgSnapshot = attachedImage ? attachedImage.dataUrl : null;

        addMessageEl(text || '(фото)', 'user', true, null, imgSnapshot);
        addMessageToChat(text || '(фото)', 'user', imgSnapshot);
        if (text) updateChatTitle(text);
        input.value = '';
        removeImage();

        if (imgSnapshot) {
            const stub = "Упс! Данный раздел в разработке 🛠️🥭\\n\\nСкоро Mango-Chat научится смотреть фото, а пока я умею только отвечать на текстовые вопросы ✨😊";
            const idx = addMessageToChat(stub, 'bot');
            addMessageEl(stub, 'bot', true, idx);
            sendBtn.disabled = false;
            input.disabled = false;
            input.focus();
            return;
        }

        const typing = addMessageEl('', 'typing');

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    question: text || 'Опиши что на фото',
                    image_data: null
                })
            });
            if (response.status === 401) {
                window.location.href = '/';
                return;
            }
            const data = await response.json();
            typing.remove();
            const idx = addMessageToChat(data.answer, 'bot');
            addMessageEl(data.answer, 'bot', true, idx);
            renderChatsList();
        } catch (error) {
            typing.remove();
            const errText = '❌ Ошибка: ' + error.message;
            const idx = addMessageToChat(errText, 'bot');
            addMessageEl(errText, 'bot', true, idx);
        }

        sendBtn.disabled = false;
        input.disabled = false;
        input.focus();
    }

    async function regenerate(msgIndex) {
        const c = getCurrentChat();
        if (!c) return;
        let userMsg = null;
        for (let i = msgIndex - 1; i >= 0; i--) {
            if (c.messages[i].role === 'user') {
                userMsg = c.messages[i];
                break;
            }
        }
        if (!userMsg) {
            showToast('Нечего перегенерировать 🤔');
            return;
        }
        if (userMsg.image) {
            c.messages.splice(msgIndex, 1);
            saveChats();
            renderCurrentChat();
            const stub = "Упс! Данный раздел в разработке 🛠️🥭\\n\\nСкоро Mango-Chat научится смотреть фото, а пока я умею только отвечать на текстовые вопросы ✨😊";
            const idx = addMessageToChat(stub, 'bot');
            addMessageEl(stub, 'bot', true, idx);
            return;
        }
        c.messages.splice(msgIndex, 1);
        saveChats();
        renderCurrentChat();
        const typing = addMessageEl('', 'typing');
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    question: userMsg.text,
                    image_data: null
                })
            });
            if (response.status === 401) {
                window.location.href = '/';
                return;
            }
            const data = await response.json();
            typing.remove();
            const idx = addMessageToChat(data.answer, 'bot');
            addMessageEl(data.answer, 'bot', true, idx);
        } catch (error) {
            typing.remove();
            const errText = '❌ Ошибка: ' + error.message;
            const idx = addMessageToChat(errText, 'bot');
            addMessageEl(errText, 'bot', true, idx);
        }
    }

    function toggleSidebar(force) {
        const open = typeof force === 'boolean' ? force : !sidebar.classList.contains('open');
        sidebar.classList.toggle('open', open);
        if (window.innerWidth > 900) {
            mainWrapper.classList.toggle('shifted', open);
            header.classList.toggle('shifted', open);
            inputContainer.classList.toggle('shifted', open);
        }
    }

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', function(e) {
        e.preventDefault();
        sendMessage();
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth <= 900) {
            mainWrapper.classList.remove('shifted');
            header.classList.remove('shifted');
            inputContainer.classList.remove('shifted');
        } else if (sidebar.classList.contains('open')) {
            mainWrapper.classList.add('shifted');
            header.classList.add('shifted');
            inputContainer.classList.add('shifted');
        }
    });

    newChat();
    input.focus();
</script>
</body>
</html>
"""


# ============ МАРШРУТЫ ============
def is_logged_in():
    return session.get("logged_in") is True


@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template_string(HTML)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == APP_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = "❌ Неверный пароль"
    return render_template_string(LOGIN_HTML, error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})


@app.route('/ask', methods=['POST'])
def ask():
    if not is_logged_in():
        return jsonify({'answer': '❌ Требуется авторизация'}), 401
    try:
        question = request.json.get('question', '')
        print(f"📩 Вопрос: {question[:50]}...")
        answer = ask_f5ai(question, None)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'answer': f'❌ Ошибка: {str(e)}'})


if __name__ == '__main__':
    if os.environ.get("LOCAL_DEV") == "1":
        threading.Timer(1, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
        print("""
    ╔══════════════════════════════════════╗
    ║   🥭 MANGO-CHAT (Local Dev Mode)     ║
    ║   Открой: http://127.0.0.1:5000     ║
    ╚══════════════════════════════════════╝
        """)
        app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
    else:
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port)
