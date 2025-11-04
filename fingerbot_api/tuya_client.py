import json
import requests
import hashlib
import hmac
import time
import uuid
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET, TUYA_REGION

# Базовые URL для разных регионов
REGION_URLS = {
    "eu": "https://openapi.tuyaeu.com",
    "us": "https://openapi.tuyaus.com", 
    "cn": "https://openapi.tuyacn.com"
}

def get_base_url():
    """Получить базовый URL для региона"""
    return REGION_URLS.get(TUYA_REGION, "https://openapi.tuyaeu.com")

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
    
    # Проверяем, что обязательные переменные установлены
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID или CLIENT_SECRET не установлены в .env файле")
    
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
    
    # Build the string for HMAC - безопасная конкатенация
    client_id_str = CLIENT_ID or ""
    access_token_str = access_token or ""
    
    if access_token:
        # General business API
        str_for_hmac = client_id_str + access_token_str + t + nonce + string_to_sign
    else:
        # Token management API
        str_for_hmac = client_id_str + t + nonce + string_to_sign
    
    # Generate signature - безопасное кодирование
    client_secret_bytes = (CLIENT_SECRET or "").encode('utf-8')
    str_for_hmac_bytes = str_for_hmac.encode('utf-8')
    
    signature = hmac.new(
        client_secret_bytes,
        str_for_hmac_bytes,
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
            "client_id": CLIENT_ID or "",
            "sign": signature,
            "t": t,
            "nonce": nonce,
            "sign_method": "HMAC-SHA256"
        }
        
        base_url = get_base_url()
        
        print(f"🔐 Получение токена...")
        print(f"   URL: {base_url}{url}")
        
        # GET request for token
        response = requests.get(
            f"{base_url}{url}",
            headers=headers,
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                access_token = data["result"]["access_token"]
                token_expiry = time.time() + data["result"]["expire_time"]
                print(f"✅ Токен получен успешно!")
                print(f"   Expires in: {data['result']['expire_time']} секунд")
                return access_token
            else:
                error_msg = data.get("msg", "Unknown error")
                print(f"❌ Ошибка получения токена: {error_msg}")
                return None
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
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
            "client_id": CLIENT_ID or "",
            "access_token": token,
            "sign": signature,
            "t": t,
            "nonce": nonce,
            "sign_method": "HMAC-SHA256",
            "Content-Type": "application/json"
        }
        
        base_url = get_base_url()
        full_url = f"{base_url}{url}"
        
        print(f"🌐 API v2.0 Call: {method} {full_url}")
        
        # Выполняем запрос и сразу обрабатываем ответ
        if method == "GET":
            response = requests.get(full_url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(full_url, headers=headers, json=payload, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            error_response = {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "response": response.text[:200] if hasattr(response, 'text') else "No response text"
            }
            return error_response
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Request exception: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
