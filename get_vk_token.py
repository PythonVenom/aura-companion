#!/usr/bin/env python3
"""
Получение VK токена для Ауры
"""

from vkpymusic import Service, TokenReceiver
import time

def get_vk_token():
    print("\n🔐 ПОЛУЧЕНИЕ ТОКЕНА VK ДЛЯ АУРЫ")
    print("="*50)
    
    # Вводим данные
    login = input("📱 Введите номер телефона или email: ")
    password = input("🔑 Введите пароль от ВК: ")
    
    print("\n⏳ Подключаюсь к VK...")
    
    try:
        # СОЗДАЕМ ОБЪЕКТ
        token_receiver = TokenReceiver(login, password)
        
        # ВАЖНО: вызываем метод auth() ПЕРЕД get_token()!
        print("🔄 Авторизация...")
        token_receiver.auth()
        
        # Теперь получаем токен
        print("🔑 Получение токена...")
        token = token_receiver.get_token()
        
        if token:
            print(f"\n✅ ТОКЕН ПОЛУЧЕН: {token[:20]}...")
            
            # Сохраняем в файл
            with open("vk_token.txt", "w") as f:
                f.write(token)
            print("✅ Токен сохранен в vk_token.txt")
            
            # Сохраняем в config.ini для библиотеки
            token_receiver.save_to_config()
            print("✅ Токен сохранен в config.ini")
            
            return token
        else:
            print("❌ Не удалось получить токен. Проверьте логин/пароль.")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n🔧 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("1. Неправильный логин или пароль")
        print("2. Двухфакторная аутентификация (нужен код из СМС)")
        print("3. Проблемы с сетью")
        return None

if __name__ == "__main__":
    token = get_vk_token()
    if token:
        print("\n🎉 ТОКЕН ГОТОВ! Аура теперь может работать с VK")
    else:
        print("\n❌ Не удалось получить токен")
