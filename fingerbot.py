from flask import Flask, jsonify, request
import requests
import time
import hashlib
import hmac
import json
import uuid

app = Flask(__name__)

# Tuya credentials
CLIENT_ID = "4upgk93g77348pvmcgu9"
CLIENT_SECRET = "dc7a33cce91a48d8bebb85fa74332eac"
DEVICE_ID = "bfbd4ashj4z74h5n"

BASE_URL = "https://openapi.tuyaeu.com"

# Global token storage
access_token = None
token_expiry = 0

def generate_nonce():
    """Generate UUID for nonce"""
    return str(uuid.uuid4())

def calculate_content_sha256(body):
    """Calculate SHA256 of request body"""
    if body is None or body == "":
        # Empty body SHA256
        return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    if isinstance(body, dict):
        body = json.dumps(body)
    
    return hashlib.sha256(body.encode('utf-8')).hexdigest()

def build_url(path, params=None):
    """Build URL with sorted parameters"""
    if not params:
        return path
    
    # Sort parameters alphabetically
    sorted_params = sorted(params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    return f"{path}?{query_string}"

def generate_signature(method, url, body, access_token=None, custom_headers=None):
    """Generate signature according to Tuya documentation"""
    
    # Timestamp
    t = str(int(time.time() * 1000))
    
    # Nonce
    nonce = generate_nonce()
    
    # Content SHA256
    content_sha256 = calculate_content_sha256(body)
    
    # Build stringToSign
    string_to_sign_parts = [
        method.upper(),
        content_sha256,
        "",  # Empty headers for now (no custom signature headers)
        url
    ]
    string_to_sign = "\n".join(string_to_sign_parts)
    
    # Build the string for HMAC
    if access_token:
        # General business API
        str_for_hmac = CLIENT_ID + access_token + t + nonce + string_to_sign
    else:
        # Token management API
        str_for_hmac = CLIENT_ID + t + nonce + string_to_sign
    
    # Generate signature
    signature = hmac.new(
        CLIENT_SECRET.encode('utf-8'),
        str_for_hmac.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    
    return signature, t, nonce

def get_access_token():
    """Get access token with correct signature"""
    global access_token, token_expiry
    
    # Check if token is still valid
    if access_token and time.time() < token_expiry - 300:
        return access_token
    
    try:
        # Token management API parameters
        params = {"grant_type": "1"}
        url = build_url("/v1.0/token", params)
        
        # Generate signature for token request
        signature, t, nonce = generate_signature("GET", url, None)
        
        headers = {
            "client_id": CLIENT_ID,
            "sign": signature,
            "t": t,
            "nonce": nonce,
            "sign_method": "HMAC-SHA256"
        }
        
        print(f"🔐 Получение токена...")
        print(f"   URL: {BASE_URL}{url}")
        print(f"   Timestamp: {t}")
        print(f"   Nonce: {nonce}")
        print(f"   Signature: {signature[:20]}...")
        
        # GET request for token
        response = requests.get(
            f"{BASE_URL}{url}",
            headers=headers,
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Data: {json.dumps(data, indent=2)}")
            
            if data.get("success"):
                access_token = data["result"]["access_token"]
                token_expiry = time.time() + data["result"]["expire_time"]
                print(f"✅ Токен получен успешно!")
                print(f"   Access Token: {access_token[:20]}...")
                print(f"   Expires in: {data['result']['expire_time']} секунд")
                return access_token
            else:
                error_msg = data.get("msg", "Unknown error")
                print(f"❌ Ошибка получения токена: {error_msg}")
                return None
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при получении токена: {e}")
        return None

def call_tuya_api_v2(endpoint, method="GET", payload=None, params=None):
    """Make API call to Tuya IoT Core API v2.0 with correct signature"""
    token = get_access_token()
    if not token:
        return {"success": False, "error": "Failed to get access token"}
    
    try:
        # Build URL with parameters
        url = build_url(endpoint, params)
        
        # Generate signature for API call
        signature, t, nonce = generate_signature(method, url, payload, token)
        
        headers = {
            "client_id": CLIENT_ID,
            "access_token": token,
            "sign": signature,
            "t": t,
            "nonce": nonce,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json"
        }
        
        print(f"🌐 API v2.0 Call: {method} {BASE_URL}{url}")
        print(f"   Timestamp: {t}")
        print(f"   Nonce: {nonce}")
        print(f"   Signature: {signature[:20]}...")
        
        if payload:
            print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        full_url = f"{BASE_URL}{url}"
        
        if method == "GET":
            response = requests.get(full_url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, headers=headers, json=payload, timeout=10)
        elif method == "PUT":
            response = requests.put(full_url, headers=headers, json=payload, timeout=10)
        elif method == "DELETE":
            response = requests.delete(full_url, headers=headers, timeout=10)
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Data: {json.dumps(data, indent=2)}")
            return data
        else:
            error_response = {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "response": response.text[:200]
            }
            print(f"   API Error: {error_response}")
            return error_response
            
    except Exception as e:
        error_response = {"success": False, "error": str(e)}
        print(f"   API Exception: {error_response}")
        return error_response

@app.route("/")
def home():
    return jsonify({
        "status": "FingerBot API - Complete Control System",
        "api_version": "Tuya IoT Core API v2.0",
        "signature_method": "HMAC-SHA256 with nonce and proper stringToSign",
        "credentials": {
            "client_id": CLIENT_ID,
            "device_id": DEVICE_ID,
            "data_center": "Central Europe Data Center"
        },
        "endpoints": [
            "/test - Test connection",
            "/device_info - Device information",
            "/device_status - Current device status",
            "/device_functions - Available functions",
            "/get_desired_properties - Get desired properties",
            "/set_press - Press command (lower arm)",
            "/set_release - Release command (raise arm)",
            "/set_click - Click command (press & release)",
            "/set_custom_position - Set custom arm position",
            "/set_hold_time - Set click hold time (0-10s)",
            "/toggle_switch - Toggle device on/off",
            "/clear_commands - Clear all commands",
            "/signature_test - Test signature generation"
        ]
    })

@app.route("/test")
def test_connection():
    """Test connection with correct signature"""
    token = get_access_token()
    
    if token:
        return jsonify({
            "success": True,
            "message": "✅ Подключение успешно! Токен получен с правильной подписью.",
            "token_expires_in": f"{int(token_expiry - time.time())} секунд",
            "signature_method": "HMAC-SHA256 with nonce"
        })
    else:
        return jsonify({
            "success": False,
            "message": "❌ Ошибка подключения",
            "check": "Проверьте credentials и IP whitelist"
        })

@app.route("/device_info")
def device_info():
    """Get device information"""
    result = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}")
    return jsonify(result)

@app.route("/device_status")
def device_status():
    """Get current device status"""
    result = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}/status")
    return jsonify(result)

@app.route("/device_functions")
def device_functions():
    """Get device functions and specifications"""
    result = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}/functions")
    return jsonify(result)

@app.route("/get_desired_properties")
def get_desired_properties():
    """Query desired properties of the device"""
    result = call_tuya_api_v2(f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired")
    return jsonify(result)

@app.route("/set_press")
def set_press():
    """Set press command - lower the arm completely"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 100,  # Полностью опустить
            "arm_up_percent": 0,      # Поднять на 0%
            "switch": True            # Включить устройство
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "press",
        "command": "Lower arm completely (press)",
        "parameters": {
            "arm_down_percent": 100,
            "arm_up_percent": 0, 
            "switch": True
        },
        "result": result
    })

@app.route("/set_release")  
def set_release():
    """Set release command - raise the arm completely"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 0,    # Опустить на 0%
            "arm_up_percent": 100,    # Полностью поднять
            "switch": True            # Включить устройство
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "release", 
        "command": "Raise arm completely (release)",
        "parameters": {
            "arm_down_percent": 0,
            "arm_up_percent": 100,
            "switch": True
        },
        "result": result
    })

@app.route("/set_click")
def set_click():
    """Set click command - press and release (full cycle)"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 100,  # Опустить
            "arm_up_percent": 100,    # Затем поднять
            "switch": True,           # Включить устройство
            "mode": "click"           # Режим клика
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "click",
        "command": "Press and release (click cycle)",
        "parameters": {
            "arm_down_percent": 100,
            "arm_up_percent": 100,
            "switch": True,
            "mode": "click"
        },
        "result": result
    })

@app.route("/set_custom_position")
def set_custom_position():
    """Set custom arm position with parameters"""
    # Get parameters from query string
    down_percent = request.args.get('down', type=int, default=50)
    up_percent = request.args.get('up', type=int, default=50)
    hold_time = request.args.get('hold', type=int, default=2)
    
    # Validate parameters
    down_percent = max(0, min(100, down_percent))
    up_percent = max(0, min(100, up_percent))
    hold_time = max(0, min(10, hold_time))
    
    payload = {
        "properties": json.dumps({
            "arm_down_percent": down_percent,
            "arm_up_percent": up_percent,
            "click_sustain_time": hold_time,
            "switch": True,
            "mode": "click"
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "custom_position",
        "command": f"Set custom position: down={down_percent}%, up={up_percent}%, hold={hold_time}s",
        "parameters": {
            "arm_down_percent": down_percent,
            "arm_up_percent": up_percent,
            "click_sustain_time": hold_time,
            "switch": True,
            "mode": "click"
        },
        "result": result
    })

@app.route("/set_hold_time")
def set_hold_time():
    """Set click hold time (0-10 seconds)"""
    hold_time = request.args.get('time', type=int, default=2)
    hold_time = max(0, min(10, hold_time))
    
    payload = {
        "properties": json.dumps({
            "click_sustain_time": hold_time,
            "switch": True
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "set_hold_time",
        "command": f"Set click hold time to {hold_time} seconds",
        "parameters": {
            "click_sustain_time": hold_time,
            "switch": True
        },
        "result": result
    })

@app.route("/toggle_switch")
def toggle_switch():
    """Toggle device on/off"""
    switch_state = request.args.get('state', type=str, default='toggle')
    
    # Get current status to determine toggle
    current_status = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}/status")
    
    current_switch = True  # Default to on
    if current_status.get("success") and "result" in current_status:
        for status in current_status["result"]:
            if status["code"] == "switch":
                current_switch = status["value"]
                break
    
    # Determine new state
    if switch_state.lower() == 'on':
        new_switch = True
    elif switch_state.lower() == 'off':
        new_switch = False
    else:  # toggle
        new_switch = not current_switch
    
    payload = {
        "properties": json.dumps({
            "switch": new_switch
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "toggle_switch",
        "command": f"Set switch to {'ON' if new_switch else 'OFF'}",
        "previous_state": current_switch,
        "new_state": new_switch,
        "parameters": {
            "switch": new_switch
        },
        "result": result
    })

@app.route("/clear_commands")
def clear_commands():
    """Clear all desired properties"""
    payload = {
        "properties": json.dumps({}),
        "duration": 1,  # Very short duration
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "clear_commands",
        "command": "Clear all desired properties",
        "result": result
    })

@app.route("/signature_test")
def signature_test():
    """Test signature generation"""
    
    # Test token signature
    token_params = {"grant_type": "1"}
    token_url = build_url("/v1.0/token", token_params)
    token_signature, token_t, token_nonce = generate_signature("GET", token_url, None)
    
    # Test API signature
    api_url = build_url(f"/v1.0/devices/{DEVICE_ID}")
    api_signature, api_t, api_nonce = generate_signature("GET", api_url, None, "test_token")
    
    # Test POST signature with payload
    post_payload = {"test": "data"}
    post_url = build_url(f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired")
    post_signature, post_t, post_nonce = generate_signature("POST", post_url, post_payload, "test_token")
    
    return jsonify({
        "token_signature_test": {
            "url": token_url,
            "timestamp": token_t,
            "nonce": token_nonce,
            "signature": token_signature,
            "method": "GET",
            "body": "empty"
        },
        "api_signature_test": {
            "url": api_url,
            "timestamp": api_t,
            "nonce": api_nonce,
            "signature": api_signature,
            "method": "GET",
            "body": "empty"
        },
        "post_signature_test": {
            "url": post_url,
            "timestamp": post_t,
            "nonce": post_nonce,
            "signature": post_signature,
            "method": "POST",
            "body": post_payload
        },
        "signature_algorithm": "HMAC-SHA256 with nonce and proper stringToSign",
        "explanation": {
            "stringToSign_format": "METHOD\\nCONTENT-SHA256\\nHEADERS\\nURL",
            "hmac_input": "CLIENT_ID + ACCESS_TOKEN + TIMESTAMP + NONCE + stringToSign",
            "content_sha256": "SHA256 of request body (empty string for GET)"
        }
    })

@app.route("/device_commands")
def device_commands():
    """Get all available commands for the device"""
    return jsonify({
        "device": "CUBETOUCH II (FingerBot)",
        "available_commands": [
            {
                "name": "Basic Actions",
                "commands": [
                    {"endpoint": "/set_press", "description": "Press - lower arm completely", "method": "GET"},
                    {"endpoint": "/set_release", "description": "Release - raise arm completely", "method": "GET"},
                    {"endpoint": "/set_click", "description": "Click - press and release cycle", "method": "GET"}
                ]
            },
            {
                "name": "Advanced Control",
                "commands": [
                    {"endpoint": "/set_custom_position?down=50&up=50&hold=2", "description": "Set custom arm position", "method": "GET", "parameters": {"down": "0-100%", "up": "0-100%", "hold": "0-10s"}},
                    {"endpoint": "/set_hold_time?time=3", "description": "Set click hold duration", "method": "GET", "parameters": {"time": "0-10 seconds"}},
                    {"endpoint": "/toggle_switch?state=on", "description": "Toggle device power", "method": "GET", "parameters": {"state": "on/off/toggle"}}
                ]
            },
            {
                "name": "Status & Info",
                "commands": [
                    {"endpoint": "/device_info", "description": "Get device information", "method": "GET"},
                    {"endpoint": "/device_status", "description": "Get current device status", "method": "GET"},
                    {"endpoint": "/device_functions", "description": "Get available functions", "method": "GET"},
                    {"endpoint": "/get_desired_properties", "description": "Get pending commands", "method": "GET"}
                ]
            },
            {
                "name": "Management",
                "commands": [
                    {"endpoint": "/clear_commands", "description": "Clear all pending commands", "method": "GET"},
                    {"endpoint": "/test", "description": "Test API connection", "method": "GET"},
                    {"endpoint": "/signature_test", "description": "Test signature generation", "method": "GET"}
                ]
            }
        ],
        "usage_examples": [
            "http://192.168.1.35/set_click - Single click",
            "http://192.168.1.35/set_custom_position?down=75&up=25&hold=5 - Custom position",
            "http://192.168.1.35/set_hold_time?time=1 - Quick click",
            "http://192.168.1.35/toggle_switch?state=off - Turn off device"
        ]
    })

@app.route("/quick_click")
def quick_click():
    """Quick click with minimal hold time"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 100,
            "arm_up_percent": 100,
            "click_sustain_time": 1,  # 1 second hold
            "switch": True,
            "mode": "click"
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "quick_click",
        "command": "Quick press and release (1s hold)",
        "parameters": {
            "arm_down_percent": 100,
            "arm_up_percent": 100,
            "click_sustain_time": 1,
            "switch": True,
            "mode": "click"
        },
        "result": result
    })

@app.route("/long_press")
def long_press():
    """Long press with maximum hold time"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 100,
            "arm_up_percent": 100,
            "click_sustain_time": 10,  # 10 seconds hold (maximum)
            "switch": True,
            "mode": "click"
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "long_press",
        "command": "Long press and release (10s hold)",
        "parameters": {
            "arm_down_percent": 100,
            "arm_up_percent": 100,
            "click_sustain_time": 10,
            "switch": True,
            "mode": "click"
        },
        "result": result
    })

@app.route("/half_press")
def half_press():
    """Half press - arm at 50% position"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 50,   # Half down
            "arm_up_percent": 50,     # Half up
            "switch": True
        }),
        "duration": 3600,
        "type": 1
    }
    
    result = call_tuya_api_v2(
        f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties/desired", 
        "POST", 
        payload
    )
    
    return jsonify({
        "action": "half_press",
        "command": "Set arm to 50% position",
        "parameters": {
            "arm_down_percent": 50,
            "arm_up_percent": 50,
            "switch": True
        },
        "result": result
    })

@app.route("/battery_status")
def battery_status():
    """Get battery status and charging information"""
    result = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}/status")
    
    battery_info = {}
    if result.get("success") and "result" in result:
        for status in result["result"]:
            if status["code"] == "battery_percentage":
                battery_info["battery_level"] = f"{status['value']}%"
            elif status["code"] == "charge_status":
                battery_info["charging_status"] = status["value"]
    
    return jsonify({
        "device": "CUBETOUCH II",
        "battery_info": battery_info if battery_info else "Battery info not available",
        "full_status": result
    })

if __name__ == "__main__":
    print("🚀 Запуск FingerBot API - Полная система управления...")
    print(f"🔧 Client ID: {CLIENT_ID}")
    print(f"🔧 Device ID: {DEVICE_ID}")
    print(f"🌐 Data Center: Central Europe")
    print("")
    print("🔐 СИСТЕМА ПОДПИСИ:")
    print("   • HMAC-SHA256 с nonce")
    print("   • Правильный stringToSign")
    print("   • Content-SHA256 для тела запроса")
    print("   • Сортировка параметров URL")
    print("")
    print("🎯 ДОСТУПНЫЕ КОМАНДЫ:")
    print("   Основные действия:")
    print("   • /set_press - Нажать")
    print("   • /set_release - Отпустить")
    print("   • /set_click - Клик")
    print("   • /quick_click - Быстрый клик")
    print("   • /long_press - Долгое нажатие")
    print("")
    print("   Расширенное управление:")
    print("   • /set_custom_position - Кастомная позиция")
    print("   • /set_hold_time - Время удержания")
    print("   • /toggle_switch - Включить/выключить")
    print("   • /half_press - Половина нажатия")
    print("")
    print("   Информация:")
    print("   • /device_info - Инфо устройства")
    print("   • /device_status - Текущий статус")
    print("   • /battery_status - Батарея")
    print("   • /device_commands - Все команды")
    print("")
    print("   Управление:")
    print("   • /clear_commands - Очистить команды")
    print("   • /test - Тест подключения")
    print("")
    
    # Test connection on startup
    test_token = get_access_token()
    if test_token:
        print("🎉 Токен получен с правильной подписью! API готов к работе!")
        print("📱 Доступно по: http://192.168.1.35")
    else:
        print("⚠️  Проблемы с получением токена")
    
    app.run(host="0.0.0.0", port=80, debug=True)
