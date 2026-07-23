import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Подставь свои данные с my.telegram.org
API_ID = 1234567 
API_HASH = "your_api_hash"

async def main() -> None:
    print("Initialize Telethon session...")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    # Игнорируем ложноположительную ошибку Pylance о том, что метод не awaitable
    await client.start()  # type: ignore
    
    # Добавляем Type Guard, чтобы Pylance знал, что session не None
    if client.session is not None:
        print("\n--- COPY THIS STRING TO YOUR .env AS TELEGRAM_SESSION_STRING ---")
        print(client.session.save())
        print("--------------------------------------------------------------\n")
    
    await client.disconnect()  # type: ignore

if __name__ == "__main__":
    asyncio.run(main())