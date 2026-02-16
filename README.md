# StaffBot — Бот управления штатной структурой Discord

## Локальная установка

1. Клонируйте репозиторий
2. Создайте файл `.env`:
   ```
   copy .env.example .env
   ```
3. Откройте `.env` и вставьте ваш токен бота
4. Запустите `staff_start.bat` или:
   ```
   pip install -r requirements.txt
   python staff_bot.py
   ```

## Развёртывание на Railway

1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo** → выберите ваш StaffBot
3. После импорта откройте проект → **Variables** → **+ New Variable**
4. Добавьте переменную:
   - **Name:** `DISCORD_BOT_TOKEN`
   - **Value:** ваш токен бота из Discord Developer Portal
5. Railway автоматически обнаружит `requirements.txt` и `Procfile`
6. Нажмите **Deploy** — бот запустится

### Настройки на Railway

- **Start Command:** `python staff_bot.py` (если автоматически не подхватилось)
- **Plan:** Hobby (бесплатный) — даёт 500 часов в месяц

## Получение токена

1. [Discord Developer Portal](https://discord.com/developers/applications)
2. Ваше приложение → Bot → Reset Token → скопируйте
3. Сохраните в `.env` (локально) или в Variables (Railway)

**⚠️ Никогда не загружайте `.env` в Git!** Файл уже в .gitignore.
