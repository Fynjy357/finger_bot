from flask import Flask, jsonify, request
import json
from tuya_client import call_tuya_api_v2, get_access_token
from config import DEVICE_ID

app = Flask(__name__)

def get_battery_info():
    """Получить информацию о батарее устройства"""
    result = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}/status")
    
    battery_data = {
        "battery_level": "Неизвестно",
        "battery_percentage": None,
        "charging_status": "Неизвестно",
        "is_charging": False,
        "battery_health": "Неизвестно"
    }
    
    if result.get("success") and "result" in result:
        for status in result["result"]:
            if status["code"] == "battery_percentage":
                battery_percentage = status["value"]
                battery_data["battery_percentage"] = battery_percentage
                battery_data["battery_level"] = f"{battery_percentage}%"
                
                # Определяем состояние батареи
                if battery_percentage >= 80:
                    battery_data["battery_health"] = "🔋 Отлично"
                elif battery_percentage >= 50:
                    battery_data["battery_health"] = "🔋 Хорошо"
                elif battery_percentage >= 20:
                    battery_data["battery_health"] = "🔋 Средне"
                else:
                    battery_data["battery_health"] = "🔋 Низкий заряд"
                    
            elif status["code"] in ["charge_state", "charge_status"]:
                charge_state = status["value"]
                battery_data["charging_status"] = charge_state
                
                # Улучшенная обработка статусов зарядки
                if charge_state == "charging" or charge_state == "1":
                    battery_data["charging_status"] = "⚡ Заряжается"
                    battery_data["is_charging"] = True
                elif charge_state == "not_charging" or charge_state == "0":
                    battery_data["charging_status"] = "🔌 Не заряжается"
                    battery_data["is_charging"] = False
                elif charge_state == "charge_done":
                    battery_data["charging_status"] = "✅ Зарядка завершена"
                    battery_data["is_charging"] = False
                else:
                    battery_data["charging_status"] = f"❓ {charge_state}"
                    battery_data["is_charging"] = False
    
    return battery_data

@app.route("/")
def home():
    return jsonify({
        "status": "FingerBot API - Complete Control System",
        "device": "CUBETOUCH II",
        "endpoints": [
            "/test - Проверка подключения",
            "/quick_click - Быстрый клик",
            "/device_status - Статус устройства",
            "/battery_status - Проверить заряд батареи",
            "/check_battery - Проверить заряд (для бота)"
        ]
    })

@app.route("/test")
def test():
    """Тест подключения к Tuya"""
    token = get_access_token()
    return jsonify({
        "token_available": bool(token),
        "device_id": DEVICE_ID,
        "message": "✅ Подключение успешно!" if token else "❌ Ошибка подключения"
    })

@app.route("/quick_click")
def quick_click():
    """Быстрый клик - основная функция"""
    payload = {
        "properties": json.dumps({
            "arm_down_percent": 100,
            "arm_up_percent": 100,
            "click_sustain_time": 1,
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
        "success": result.get("success", False),
        "result": result
    })

@app.route("/device_status")
def device_status():
    """Статус устройства"""
    result = call_tuya_api_v2(f"/v1.0/devices/{DEVICE_ID}/status")
    return jsonify(result)

@app.route("/battery_status")
def battery_status():
    """Проверить заряд батареи - детальная информация"""
    battery_data = get_battery_info()
    
    return jsonify({
        "device": "CUBETOUCH II",
        "battery_info": battery_data
    })

@app.route("/check_battery")
def check_battery():
    """Проверить заряд - оптимизировано для Telegram бота"""
    battery_data = get_battery_info()
    
    # Форматируем сообщение для Telegram
    if battery_data["battery_percentage"] is not None:
        message = f"🔋 *Состояние батареи:*\n\n"
        message += f"• Уровень заряда: {battery_data['battery_level']}\n"
        message += f"• Статус зарядки: {battery_data['charging_status']}\n"
        message += f"• Состояние: {battery_data['battery_health']}\n"
        
        # Добавляем рекомендации
        if battery_data["battery_percentage"] <= 20:
            message += "\n⚠️ *Рекомендуется зарядить устройство*"
        elif battery_data["battery_percentage"] <= 10:
            message += "\n🔴 *НИЗКИЙ ЗАРЯД! Срочно зарядите устройство*"
        elif battery_data["is_charging"]:
            message += "\n⚡ *Устройство заряжается*"
    else:
        message = "❓ *Информация о батарее недоступна*\n\nПроверьте подключение устройства"
    
    return jsonify({
        "success": True,
        "message": message,
        "battery_data": battery_data
    })

if __name__ == "__main__":
    print("🚀 Запуск FingerBot API - Обновленная система...")
    print(f"📱 Устройство: {DEVICE_ID}")
    print("")
    print("🎯 Доступные эндпоинты:")
    print("   • /test - Проверка подключения")
    print("   • /quick_click - Быстрый клик")
    print("   • /device_status - Статус устройства")
    print("   • /battery_status - Проверить заряд (детально)")
    print("   • /check_battery - Проверить заряд (для бота)")
    print("")
    
    # Тестируем подключение при запуске
    token = get_access_token()
    if token:
        print("✅ Подключение к Tuya Cloud: УСПЕШНО")
        
        # Проверяем батарею при запуске
        print("🔋 Проверка состояния батареи...")
        battery_info = get_battery_info()
        if battery_info["battery_percentage"] is not None:
            print(f"   Уровень заряда: {battery_info['battery_level']}")
            print(f"   Статус зарядки: {battery_info['charging_status']}")
        else:
            print("   ❓ Информация о батарее недоступна")
    else:
        print("❌ Подключение к Tuya Cloud: ОШИБКА")
    
    print(f"\n🌐 API доступно по: http://192.168.1.35:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
