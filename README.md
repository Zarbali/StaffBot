# StaffBot — Бот управления штатной структурой Discord

## Установка

1. Клонируйте репозиторий
2. Создайте файл `.env`:
   ```
   copy .env.example .env
   ```
3. Откройте `.env` и вставьте ваш токен бота:
   ```
   DISCORD_BOT_TOKEN=ваш_токен_здесь
   ```
4. Запустите `staff_start.bat` или:
   ```
   pip install discord.py
   python staff_bot.py
   ```

## Получение токена

1. Перейдите на [Discord Developer Portal](https://discord.com/developers/applications)
2. Создайте приложение → Bot → Reset Token (скопируйте)
3. Вставьте в `.env`

**⚠️ Никогда не загружайте `.env` в Git!** Файл уже в .gitignore.
