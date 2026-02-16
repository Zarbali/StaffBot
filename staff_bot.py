import discord
from discord.ui import Button, View, Select, Modal, TextInput
from discord import app_commands
from datetime import datetime
import json
import os
import asyncio

# Загрузка .env (токен не храним в коде!)
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip("'\""))
_load_env()

# ========== НАСТРОЙКИ ==========
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

# ID каналов
BUTTON_CHANNEL_ID = 1472757436271165441
STAFF_CHANNEL_ID = 1472757445041459300
LOG_CHANNEL_ID = 1472757455510573146

# ID подразделений
SUBDIVISION_ROLES = {
    "24th STS": 1467302068552339579
}

# Список должностей (для бойцов без взвода)
POSITIONS = [
    "Commander",
    "Deputy Commander",
    "Automatic rifleman",
    "Machine gunner",
    "Marksman",
    "Grenadier",
    "Rifleman",
    "Pilot",
    "CCT",
    "PJ",
]

# Взводы (подразделение -> взвод -> слоты с ролью и званием)
# При вписывании выбирается взвод и свободный слот — роль и звание назначаются автоматически
SQUADS = {
    "24th STS": {
        "Командование роты [Echo-1]": [
            {"role": "Командир роты", "rank": "| Captain | Cpt"},
            {"role": "Зам. командира роты", "rank": "| First Lieutenant | 1st Lt"},
            {"role": "Командир группы логистики", "rank": "| Second Lieutenant | 2nd Lt"},
        ],
        "Ground Forces Group [Alpha -1]": [
            {"role": "Commander", "rank": "| Master Sergeant | MSgt"},
            {"role": "Deputy Commander", "rank": "| Staff Sergeant | SSgt"},
            {"role": "Automatic rifleman", "rank": "| Airman First Class | A1C"},
            {"role": "Marksman", "rank": "| Senior Airman | SrA"},
            {"role": "Rifleman", "rank": "| Airman First Class | A1C"},
            {"role": "Rifleman", "rank": "| Airman First Class | A1C"},
            {"role": "Radioman", "rank": "| Senior Airman | SrA"},
        ],
        "Ground Forces Group [Alpha -2]": [
            {"role": "Commander", "rank": "| Master Sergeant | MSgt"},
            {"role": "Deputy Commander", "rank": "| Staff Sergeant | SSgt"},
            {"role": "Machine gunner", "rank": "| Airman First Class | A1C"},
            {"role": "Marksman", "rank": "| Senior Airman | SrA"},
            {"role": "Rifleman", "rank": "| Airman First Class | A1C"},
            {"role": "Rifleman", "rank": "| Airman First Class | A1C"},
            {"role": "Radioman", "rank": "| Senior Airman | SrA"},
        ],
        "CCT Team [Bravo-1]": [
            {"role": "Deputy Commander", "rank": "| Staff Sergeant | SSgt"},
            {"role": "CCT", "rank": "| Senior Airman | SrA"},
            {"role": "CCT", "rank": "| Senior Airman | SrA"},
            {"role": "CCT", "rank": "| Senior Airman | SrA"},
        ],
        "PJ Team [Charlie-1]": [
            {"role": "Deputy Commander", "rank": "| Staff Sergeant | SSgt"},
            {"role": "PJ", "rank": "| Senior Airman | SrA"},
            {"role": "PJ", "rank": "| Senior Airman | SrA"},
            {"role": "PJ", "rank": "| Senior Airman | SrA"},
        ],
        "Heli Pilot squad [Delta-1]": [
            {"role": "Pilot", "rank": "| Chief Master Sergeant | CMSgt"},
            {"role": "Pilot", "rank": "| Chief Master Sergeant | CMSgt"},
            {"role": "Pilot", "rank": "| Technical Sergeant | TSgt"},
            {"role": "Pilot", "rank": "| Technical Sergeant | TSgt"},
        ],
    },
}

# ID званий
RANK_ROLES = {
    "| Airman | Amn": 1467302068501872680,
    "| Airman First Class | A1C": 1467302068501872681,
    "| Senior Airman | SrA": 1467302068501872682,
    "| Staff Sergeant | SSgt": 1467302068501872683,
    "| Technical Sergeant | TSgt": 1467302068501872684,
    "| Master Sergeant | MSgt": 1467302068501872686,
    "| Senior Master Sergeant | SMSgt": 1467302068501872687,
    "| Chief Master Sergeant | CMSgt": 1467302068501872685,
    "| Second Lieutenant | 2nd Lt": 1467302068501872688,
    "| First Lieutenant | 1st Lt": 1467302068518916272,
    "| Captain | Cpt": 1467302068518916273
}

# ID ролей по должностям (выдаются автоматически при выборе позиции)
POSITION_ROLE_IDS = {
    "Commander": 1467302068531495146,
    "Deputy Commander": 1467302068518916276,
    "Automatic rifleman": 1467302068531495143,
    "Machine gunner": 1467302068531495139,
    "Marksman": 1467302068531495141,
    "Grenadier": 1471215740106576097,
    "Rifleman": 1467302068531495140,
    "Pilot": 1467302068531495145,
    "CCT": 1467302068531495144,
    "PJ": 1467302068531495142,
    # Роли из взвода Командование роты [Echo-1]
    "Командир роты": 1467302068531495146,
    "Зам. командира роты": 1467302068518916276,
}
# ===============================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# Файлы для хранения данных
DATA_FILE = "staff_data.json"
CONTROL_PANEL_MESSAGE_FILE = "control_panel_message.json"

# Глобальные переменные
user_sessions = {}  # Временное хранилище данных пользователя

# Утилиты для работы с файлами
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_control_panel_message():
    if os.path.exists(CONTROL_PANEL_MESSAGE_FILE):
        with open(CONTROL_PANEL_MESSAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_control_panel_message(message_info):
    with open(CONTROL_PANEL_MESSAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(message_info, f, ensure_ascii=False, indent=2)

def cleanup_user_session(user_id):
    """Очищает сессию пользователя"""
    if user_id in user_sessions:
        del user_sessions[user_id]

def get_soldier_display(soldier: dict) -> str:
    """Возвращает отображаемое имя бойца (для dropdown и т.д.)"""
    name = soldier.get("name", "").strip()
    surname = soldier.get("surname", "").strip()
    if name or surname:
        return f"{name} {surname}".strip()
    return f"ID: {soldier.get('discord_id', '?')}"

def get_soldier_mention(soldier: dict) -> str:
    """Возвращает пинг бойца по Discord ID"""
    return f"<@{soldier['discord_id']}>"

def get_position_role_id(position: str):
    """Возвращает ID роли должности или None если не задана"""
    return POSITION_ROLE_IDS.get(position)

# ========== КОМПОНЕНТЫ ИНТЕРФЕЙСА ==========
class MainControlView(View):
    """Главное меню управления"""
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="📝 Вписать бойца", style=discord.ButtonStyle.primary, custom_id="enlist_button")
    async def enlist_button(self, interaction: discord.Interaction, button: Button):
        await show_subdivision_selection(interaction, "enlist")
    
    @discord.ui.button(label="🗑️ Выписать бойца", style=discord.ButtonStyle.danger, custom_id="discharge_button")
    async def discharge_button(self, interaction: discord.Interaction, button: Button):
        await show_soldier_selection(interaction, "discharge")
    
    @discord.ui.button(label="✏️ Изменить данные", style=discord.ButtonStyle.secondary, custom_id="edit_button")
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        await show_soldier_selection(interaction, "edit")

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
async def show_subdivision_selection(interaction: discord.Interaction, action_type: str):
    """Показывает меню выбора подразделения"""
    options = [
        discord.SelectOption(label="24th STS'", value="24th STS", emoji="⚔"),
    ]
    
    select = Select(
        placeholder="Выберите подразделение...",
        options=options,
        custom_id=f"{action_type}_subdivision"
    )
    
    async def callback(interaction_select: discord.Interaction):
        selected = select.values[0]
        user_id = interaction_select.user.id
        
        # Сохраняем выбор пользователя
        user_sessions[user_id] = {
            "action": action_type,
            "subdivision": selected
        }
        
        if action_type == "enlist":
            await show_squad_selection(interaction_select)
        else:
            # Для discharge/edit сразу переходим к выбору бойца
            await interaction_select.response.defer()
            await show_soldier_selection(interaction_select, action_type)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.send_message(
        "**Шаг 1 из 4**\nВыберите подразделение:",
        view=view,
        ephemeral=True
    )

async def show_squad_selection(interaction: discord.Interaction):
    """Показывает меню выбора взвода"""
    user_id = interaction.user.id
    session = user_sessions.get(user_id)
    
    if not session or "subdivision" not in session:
        await interaction.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
        return
    
    subdivision = session["subdivision"]
    squads_for_sub = SQUADS.get(subdivision, {})
    
    if not squads_for_sub:
        # Нет взводов — используем старый поток (звание + должность)
        await show_rank_selection(interaction)
        return
    
    options = [discord.SelectOption(label=name, value=name) for name in squads_for_sub.keys()]
    
    select = Select(
        placeholder="Выберите взвод...",
        options=options,
        custom_id="squad_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        selected = select.values[0]
        user_id = interaction_select.user.id
        
        if user_id in user_sessions:
            user_sessions[user_id]["squad"] = selected
            await show_slot_selection(interaction_select)
        else:
            await interaction_select.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content="**Шаг 2 из 4**\nВыберите взвод:",
        view=view
    )

def get_occupied_slots(data: dict, subdivision: str, squad: str) -> set:
    """Возвращает множество занятых слотов (индексы) во взводе"""
    occupied = set()
    for soldier in data.values():
        if soldier.get("subdivision") == subdivision and soldier.get("squad") == squad:
            slot = soldier.get("slot_index")
            if slot is not None:
                occupied.add(int(slot))
    return occupied

async def show_slot_selection(interaction: discord.Interaction):
    """Показывает меню выбора свободного слота во взводе"""
    user_id = interaction.user.id
    session = user_sessions.get(user_id)
    
    if not session or "squad" not in session:
        await interaction.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
        return
    
    subdivision = session["subdivision"]
    squad = session["squad"]
    slots = SQUADS.get(subdivision, {}).get(squad, [])
    
    if not slots:
        await interaction.response.send_message("❌ Взвод не найден.", ephemeral=True)
        return
    
    data = load_data()
    occupied = get_occupied_slots(data, subdivision, squad)
    
    options = []
    for i, slot in enumerate(slots):
        if i in occupied:
            continue
        rank_short = slot["rank"].split("|")[-1].strip().rstrip(")")  # A1C, MSgt и т.д.
        label = f"{i + 1}. {slot['role']} ({rank_short})"
        options.append(discord.SelectOption(label=label[:100], value=str(i)))
    
    if not options:
        await interaction.response.edit_message(
            content=f"❌ Во взводе **{squad}** нет свободных слотов!",
            view=None
        )
        return
    
    select = Select(
        placeholder="Выберите позицию во взводе...",
        options=options,
        custom_id="slot_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        slot_idx = int(select.values[0])
        user_id = interaction_select.user.id
        
        if user_id in user_sessions:
            user_sessions[user_id]["slot_index"] = slot_idx
            slot_data = slots[slot_idx]
            user_sessions[user_id]["rank"] = slot_data["rank"]
            user_sessions[user_id]["position"] = slot_data["role"]
            await show_enlist_form(interaction_select)
        else:
            await interaction_select.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content=f"**Шаг 3 из 4**\nВыберите свободную позицию во взводе **{squad}**:",
        view=view
    )

async def show_rank_selection(interaction: discord.Interaction):
    """Показывает меню выбора звания (если нет взводов)"""
    options = [discord.SelectOption(label=rank, value=rank) for rank in RANK_ROLES.keys()]
    
    select = Select(
        placeholder="Выберите звание...",
        options=options,
        custom_id="rank_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        selected = select.values[0]
        user_id = interaction_select.user.id
        
        if user_id in user_sessions:
            user_sessions[user_id]["rank"] = selected
            await show_position_selection(interaction_select)
        else:
            await interaction_select.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content="**Шаг 2 из 4**\nВыберите звание:",
        view=view
    )

async def show_position_selection(interaction: discord.Interaction):
    """Показывает меню выбора должности (если нет взводов)"""
    options = [discord.SelectOption(label=pos, value=pos) for pos in POSITIONS]
    
    select = Select(
        placeholder="Выберите должность...",
        options=options,
        custom_id="position_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        selected = select.values[0]
        user_id = interaction_select.user.id
        
        if user_id in user_sessions:
            user_sessions[user_id]["position"] = selected
            await show_enlist_form(interaction_select)
        else:
            await interaction_select.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content="**Шаг 3 из 4**\nВыберите должность:",
        view=view
    )

async def show_enlist_form(interaction: discord.Interaction):
    """Показывает форму для ввода данных бойца"""
    user_id = interaction.user.id
    session = user_sessions.get(user_id)
    
    if not session:
        await interaction.response.send_message("❌ Сессия истекла. Начните заново.", ephemeral=True)
        return
    
    class EnlistModal(Modal, title="📝 Заполните данные бойца"):
        discord_id = TextInput(
            label="Discord ID бойца",
            placeholder="123456789012345678",
            required=True,
            max_length=20
        )
        
        async def on_submit(self, interaction_modal: discord.Interaction):
            data = load_data()
            user_session = user_sessions.get(interaction_modal.user.id)
            
            if not user_session:
                await interaction_modal.response.send_message("❌ Сессия истекла.", ephemeral=True)
                return
            
            subdivision = user_session["subdivision"]
            rank = user_session["rank"]
            position = user_session.get("position", "")
            squad = user_session.get("squad")
            slot_index = user_session.get("slot_index")
            soldier_id = f"{subdivision}_{self.discord_id.value}"
            
            # Проверка на существование бойца
            if soldier_id in data:
                await interaction_modal.response.send_message(
                    f"❌ Боец с ID {self.discord_id.value} уже существует в {subdivision}!",
                    ephemeral=True
                )
                return
            
            # Получаем имя из Discord по ID
            display_name = str(self.discord_id.value)
            try:
                guild = interaction_modal.guild
                if guild:
                    member = await guild.fetch_member(int(self.discord_id.value))
                    display_name = member.display_name
            except Exception:
                pass
            
            position_role_id = get_position_role_id(position)
            
            # Сохранение данных
            soldier_data = {
                "subdivision": subdivision,
                "subdivision_role_id": SUBDIVISION_ROLES[subdivision],
                "rank": rank,
                "rank_role_id": RANK_ROLES[rank],
                "discord_id": self.discord_id.value,
                "name": display_name,
                "surname": "",
                "position": position,
                "enlisted_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "enlisted_by": str(interaction_modal.user)
            }
            if position_role_id:
                soldier_data["position_role_id"] = position_role_id
            if squad is not None:
                soldier_data["squad"] = squad
            if slot_index is not None:
                soldier_data["slot_index"] = slot_index
            data[soldier_id] = soldier_data
            
            save_data(data)
            
            # Выдача ролей
            try:
                await assign_roles(
                    int(self.discord_id.value),
                    SUBDIVISION_ROLES[subdivision],
                    RANK_ROLES[rank],
                    interaction_modal,
                    position_role_id
                )
                role_status = "✅ Роли успешно выданы"
            except Exception as e:
                role_status = f"⚠️ Не удалось выдать роли: {str(e)}"
            
            mention = f"<@{self.discord_id.value}>"
            squad_info = f"\n**Взвод:** {squad}" if squad else ""
            # Отправка подтверждения
            await interaction_modal.response.send_message(
                f"✅ Боец {mention} успешно вписан!\n"
                f"**Подразделение:** {subdivision}\n"
                f"**Звание:** {rank}\n"
                f"**Должность:** {position}"
                f"{squad_info}\n"
                f"{role_status}",
                ephemeral=True
            )
            
            # Очистка сессии и обновление
            cleanup_user_session(interaction_modal.user.id)
            await update_staff_display()
            await log_action(interaction_modal.user, 
                           f"Вписал бойца: {mention} ({rank}) в {subdivision}")
    
    modal = EnlistModal()
    await interaction.response.send_modal(modal)

async def show_soldier_selection(interaction: discord.Interaction, action_type: str):
    """Показывает список бойцов для выбора"""
    data = load_data()
    
    if not data:
        await interaction.response.send_message("❌ В штате пока нет бойцев!", ephemeral=True)
        return
    
    # Фильтрация по подразделению, если выбрано
    user_id = interaction.user.id
    session = user_sessions.get(user_id)
    
    if session and "subdivision" in session:
        filtered_data = {k: v for k, v in data.items() if v["subdivision"] == session["subdivision"]}
    else:
        filtered_data = data
    
    if not filtered_data:
        await interaction.response.send_message("❌ В этом подразделении нет бойцев!", ephemeral=True)
        cleanup_user_session(user_id)
        return
    
    options = []
    for soldier_id, soldier in filtered_data.items():
        label = f"{get_soldier_display(soldier)} - {soldier['rank']}"
        squad_info = f" • {soldier['squad']}" if soldier.get('squad') else ""
        description = f"{soldier['subdivision']}{squad_info} • {soldier['position']}"
        options.append(discord.SelectOption(
            label=label[:100],
            value=soldier_id,
            description=description[:100]
        ))
    
    select = Select(
        placeholder="Выберите бойца...",
        options=options,
        custom_id=f"{action_type}_soldier"
    )
    
    async def callback(interaction_select: discord.Interaction):
        soldier_id = select.values[0]
        soldier_data = data[soldier_id]
        
        user_id = interaction_select.user.id
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        
        user_sessions[user_id]["selected_soldier"] = soldier_id
        user_sessions[user_id]["soldier_data"] = soldier_data
        
        if action_type == "discharge":
            await confirm_discharge(interaction_select, soldier_data)
        elif action_type == "edit":
            await show_edit_menu(interaction_select, soldier_data)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.send_message(
        f"**Выберите бойца для {'выписки' if action_type == 'discharge' else 'редактирования'}:**",
        view=view,
        ephemeral=True
    )

async def confirm_discharge(interaction: discord.Interaction, soldier_data: dict):
    """Подтверждение выписки бойца"""
    view = View(timeout=60)
    
    async def confirm_callback(interaction_confirm: discord.Interaction):
        data = load_data()
        soldier_id = f"{soldier_data['subdivision']}_{soldier_data['discord_id']}"
        
        if soldier_id not in data:
            await interaction_confirm.response.send_message("❌ Боец уже был удален!", ephemeral=True)
            return
        
        # Снятие ролей
        position_role_id = soldier_data.get("position_role_id")
        removal_result = await remove_roles(
            int(soldier_data["discord_id"]),
            soldier_data["subdivision_role_id"],
            soldier_data["rank_role_id"],
            interaction_confirm,
            position_role_id
        )
        
        # Удаление из базы
        del data[soldier_id]
        save_data(data)
        
        # Ответ пользователю
        response_msg = (
            f"✅ Боец {get_soldier_mention(soldier_data)} выписан из {soldier_data['subdivision']}!\n"
            f"{removal_result}"
        )
        
        await interaction_confirm.response.send_message(response_msg, ephemeral=True)
        
        # Очистка и обновление
        cleanup_user_session(interaction_confirm.user.id)
        await update_staff_display()
        await log_action(interaction_confirm.user,
                        f"Выписал бойца: {get_soldier_mention(soldier_data)} из {soldier_data['subdivision']}")
    
    async def cancel_callback(interaction_cancel: discord.Interaction):
        cleanup_user_session(interaction_cancel.user.id)
        await interaction_cancel.response.send_message("❌ Выписка отменена.", ephemeral=True)
    
    # Кнопки
    confirm_btn = Button(label="✅ Подтвердить", style=discord.ButtonStyle.danger)
    cancel_btn = Button(label="❌ Отмена", style=discord.ButtonStyle.secondary)
    
    confirm_btn.callback = confirm_callback
    cancel_btn.callback = cancel_callback
    
    view.add_item(confirm_btn)
    view.add_item(cancel_btn)
    
    await interaction.response.send_message(
        f"⚠️ **Подтверждение выписки**\n\n"
        f"**Боец:** {get_soldier_mention(soldier_data)}\n"
        f"**Подразделение:** {soldier_data['subdivision']}\n"
        f"**Звание:** {soldier_data['rank']}\n"
        f"**Должность:** {soldier_data['position']}\n\n"
        f"*Это действие нельзя отменить!*",
        view=view,
        ephemeral=True
    )

async def show_edit_menu(interaction: discord.Interaction, soldier_data: dict):
    """Меню редактирования бойца"""
    view = View(timeout=60)
    
    async def edit_rank_callback(interaction_btn: discord.Interaction):
        await show_rank_edit(interaction_btn)
    
    async def edit_position_callback(interaction_btn: discord.Interaction):
        await show_position_edit(interaction_btn)
    
    async def edit_squad_callback(interaction_btn: discord.Interaction):
        await show_squad_slot_edit(interaction_btn)
    
    async def cancel_callback(interaction_btn: discord.Interaction):
        cleanup_user_session(interaction_btn.user.id)
        await interaction_btn.response.edit_message(content="❌ Редактирование отменено.", view=None)
    
    # Кнопки
    rank_btn = Button(label="Изменить звание", style=discord.ButtonStyle.primary)
    position_btn = Button(label="Изменить должность", style=discord.ButtonStyle.primary)
    cancel_btn = Button(label="❌ Отмена", style=discord.ButtonStyle.secondary)
    
    rank_btn.callback = edit_rank_callback
    position_btn.callback = edit_position_callback
    cancel_btn.callback = cancel_callback
    
    view.add_item(rank_btn)
    view.add_item(position_btn)
    
    # Кнопка "Изменить взвод" — только если есть взводы в подразделении
    squads_available = bool(SQUADS.get(soldier_data["subdivision"], {}))
    if squads_available:
        squad_btn = Button(label="Изменить взвод/позицию", style=discord.ButtonStyle.primary)
        squad_btn.callback = edit_squad_callback
        view.add_item(squad_btn)
    
    view.add_item(cancel_btn)
    
    squad_info = ""
    if soldier_data.get('squad'):
        slot_num = soldier_data.get('slot_index')
        squad_info = f"\n• Взвод: {soldier_data['squad']}" + (f" (поз. {slot_num + 1})" if slot_num is not None else "")
    await interaction.response.edit_message(
        content=f"**Редактирование бойца:**\n\n"
                f"**Текущие данные:**\n"
                f"• Боец: {get_soldier_mention(soldier_data)}\n"
                f"• Звание: {soldier_data['rank']}\n"
                f"• Должность: {soldier_data['position']}"
                f"{squad_info}\n\n"
                f"Выберите что изменить:",
        view=view
    )

async def show_rank_edit(interaction: discord.Interaction):
    """Изменение звания бойца"""
    options = [discord.SelectOption(label=rank, value=rank) for rank in RANK_ROLES.keys()]
    
    select = Select(
        placeholder="Выберите новое звание...",
        options=options,
        custom_id="edit_rank_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        new_rank = select.values[0]
        user_id = interaction_select.user.id
        
        if user_id not in user_sessions or "selected_soldier" not in user_sessions[user_id]:
            await interaction_select.response.send_message("❌ Данные не найдены.", ephemeral=True)
            return
        
        soldier_id = user_sessions[user_id]["selected_soldier"]
        data = load_data()
        
        if soldier_id not in data:
            await interaction_select.response.send_message("❌ Боец не найден.", ephemeral=True)
            cleanup_user_session(user_id)
            return
        
        soldier = data[soldier_id]
        old_rank = soldier["rank"]
        
        # Проверка на изменение
        if old_rank == new_rank:
            await interaction_select.response.send_message(
                f"❌ Звание не изменилось! Боец уже имеет звание: {old_rank}",
                ephemeral=True
            )
            return
        
        # Обновление данных
        soldier["rank"] = new_rank
        soldier["rank_role_id"] = RANK_ROLES[new_rank]
        soldier["last_edited"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        soldier["edited_by"] = str(interaction_select.user)
        
        save_data(data)
        
        # Смена ролей в Discord
        try:
            await update_rank_roles(
                int(soldier["discord_id"]),
                soldier["rank_role_id"],
                RANK_ROLES[old_rank],
                interaction_select
            )
            role_status = "✅ Роли успешно обновлены"
        except Exception as e:
            role_status = f"⚠️ Ошибка обновления ролей: {str(e)}"
        
        await interaction_select.response.send_message(
            f"✅ Звание изменено!\n"
            f"**Было:** {old_rank}\n"
            f"**Стало:** {new_rank}\n"
            f"{role_status}",
            ephemeral=True
        )
        
        await update_staff_display()
        await log_action(interaction_select.user, f"Изменил звание: {old_rank} → {new_rank}")
        cleanup_user_session(user_id)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content="**Выберите новое звание:**",
        view=view
    )

async def show_position_edit(interaction: discord.Interaction):
    """Изменение должности — выбор из списка"""
    user_id = interaction.user.id
    session = user_sessions.get(user_id)
    
    if not session or "selected_soldier" not in session:
        await interaction.response.send_message("❌ Данные не найдены.", ephemeral=True)
        return
    
    # Добавляем текущую должность, если её нет в списке
    soldier = session["soldier_data"]
    positions_list = list(POSITIONS)
    if soldier["position"] not in positions_list:
        positions_list.insert(0, soldier["position"])
    
    options = [discord.SelectOption(label=pos, value=pos) for pos in positions_list]
    
    select = Select(
        placeholder="Выберите новую должность...",
        options=options,
        custom_id="edit_position_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        new_position = select.values[0]
        user_id = interaction_select.user.id
        
        if user_id not in user_sessions or "selected_soldier" not in user_sessions[user_id]:
            await interaction_select.response.send_message("❌ Данные не найдены.", ephemeral=True)
            return
        
        soldier_id = user_sessions[user_id]["selected_soldier"]
        data = load_data()
        
        if soldier_id not in data:
            await interaction_select.response.send_message("❌ Боец не найден.", ephemeral=True)
            cleanup_user_session(user_id)
            return
        
        old_position = data[soldier_id]["position"]
        old_position_role_id = data[soldier_id].get("position_role_id")
        
        if old_position == new_position:
            await interaction_select.response.send_message(
                f"❌ Должность не изменилась! Уже установлено: {old_position}",
                ephemeral=True
            )
            return
        
        new_position_role_id = get_position_role_id(new_position)
        data[soldier_id]["position"] = new_position
        if new_position_role_id:
            data[soldier_id]["position_role_id"] = new_position_role_id
        elif "position_role_id" in data[soldier_id]:
            del data[soldier_id]["position_role_id"]
        data[soldier_id]["last_edited"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        data[soldier_id]["edited_by"] = str(interaction_select.user)
        
        save_data(data)
        
        # Обновить роль должности в Discord
        try:
            await update_position_role(
                int(data[soldier_id]["discord_id"]),
                new_position,
                old_position_role_id,
                interaction_select
            )
        except Exception:
            pass
        
        await interaction_select.response.send_message(
            f"✅ Должность изменена!\n"
            f"**Было:** {old_position}\n"
            f"**Стало:** {new_position}",
            ephemeral=True
        )
        
        await update_staff_display()
        await log_action(interaction_select.user, f"Изменил должность: {old_position} → {new_position}")
        cleanup_user_session(user_id)
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content=f"**Редактирование бойца:**\n\n"
                f"**Текущие данные:**\n"
                f"• Боец: {get_soldier_mention(session['soldier_data'])}\n"
                f"• Звание: {session['soldier_data']['rank']}\n"
                f"• Должность: {session['soldier_data']['position']}\n\n"
                f"Выберите новую должность:",
        view=view
    )

async def show_squad_slot_edit(interaction: discord.Interaction):
    """Изменение взвода и позиции бойца"""
    user_id = interaction.user.id
    session = user_sessions.get(user_id)
    
    if not session or "selected_soldier" not in session:
        await interaction.response.send_message("❌ Данные не найдены.", ephemeral=True)
        return
    
    soldier_data = session["soldier_data"]
    subdivision = soldier_data["subdivision"]
    squads_for_sub = SQUADS.get(subdivision, {})
    
    if not squads_for_sub:
        await interaction.response.send_message("❌ Нет взводов для этого подразделения.", ephemeral=True)
        return
    
    options = [discord.SelectOption(label=name, value=name) for name in squads_for_sub.keys()]
    
    select = Select(
        placeholder="Выберите взвод...",
        options=options,
        custom_id="edit_squad_select"
    )
    
    async def callback(interaction_select: discord.Interaction):
        squad = select.values[0]
        user_id = interaction_select.user.id
        session = user_sessions.get(user_id)
        
        if not session or "selected_soldier" not in session:
            await interaction_select.response.send_message("❌ Данные не найдены.", ephemeral=True)
            return
        
        soldier_id = session["selected_soldier"]
        current_discord_id = session["soldier_data"]["discord_id"]
        slots = squads_for_sub.get(squad, [])
        data = load_data()
        
        # Занятые слоты, но текущий боец освобождает свой слот при переводе
        occupied = get_occupied_slots(data, subdivision, squad)
        if soldier_data.get("squad") == squad and soldier_data.get("slot_index") is not None:
            occupied.discard(soldier_data["slot_index"])  # его слот теперь свободен
        
        options = []
        for i, slot in enumerate(slots):
            if i in occupied:
                continue
            rank_short = slot["rank"].split("|")[-1].strip()
            options.append(discord.SelectOption(label=f"{i + 1}. {slot['role']} ({rank_short})", value=str(i)))
        
        if not options:
            await interaction_select.response.send_message(f"❌ Во взводе **{squad}** нет свободных слотов!", ephemeral=True)
            return
        
        slot_select = Select(placeholder="Выберите позицию...", options=options, custom_id="edit_slot_select")
        
        async def slot_callback(interaction_slot: discord.Interaction):
            slot_idx = int(slot_select.values[0])
            user_id = interaction_slot.user.id
            session = user_sessions.get(user_id)
            
            if not session or "selected_soldier" not in session:
                await interaction_slot.response.send_message("❌ Данные не найдены.", ephemeral=True)
                return
            
            soldier_id = session["selected_soldier"]
            data = load_data()
            if soldier_id not in data:
                await interaction_slot.response.send_message("❌ Боец не найден.", ephemeral=True)
                cleanup_user_session(user_id)
                return
            
            soldier = data[soldier_id]
            slot_data = slots[slot_idx]
            old_squad = soldier.get("squad", "—")
            old_slot = soldier.get("slot_index")
            old_rank_role_id = soldier.get("rank_role_id")
            new_rank_role_id = RANK_ROLES[slot_data["rank"]]
            
            old_position_role_id = soldier.get("position_role_id")
            new_position_role_id = get_position_role_id(slot_data["role"])
            
            soldier["squad"] = squad
            soldier["slot_index"] = slot_idx
            soldier["position"] = slot_data["role"]
            soldier["rank"] = slot_data["rank"]
            soldier["rank_role_id"] = new_rank_role_id
            if new_position_role_id:
                soldier["position_role_id"] = new_position_role_id
            elif "position_role_id" in soldier:
                del soldier["position_role_id"]
            soldier["last_edited"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            soldier["edited_by"] = str(interaction_slot.user)
            
            save_data(data)
            
            # Обновить роль должности в Discord
            try:
                await update_position_role(
                    int(soldier["discord_id"]),
                    slot_data["role"],
                    old_position_role_id,
                    interaction_slot
                )
            except Exception:
                pass
            
            # Обновить роль звания в Discord
            try:
                await update_rank_roles(
                    int(soldier["discord_id"]),
                    new_rank_role_id,
                    old_rank_role_id or new_rank_role_id,
                    interaction_slot
                )
            except Exception:
                pass
            
            old_pos = f"{old_squad} (поз. {old_slot + 1})" if old_slot is not None else "—"
            await interaction_slot.response.send_message(
                f"✅ Взвод изменён!\n"
                f"**Было:** {old_pos}\n"
                f"**Стало:** {squad} (поз. {slot_idx + 1})\n"
                f"**Роль:** {slot_data['role']} ({slot_data['rank']})",
                ephemeral=True
            )
            
            await update_staff_display()
            await log_action(interaction_slot.user, f"Изменил взвод: {old_pos} → {squad} (поз. {slot_idx + 1})")
            cleanup_user_session(user_id)
        
        slot_select.callback = slot_callback
        slot_view = View(timeout=60)
        slot_view.add_item(slot_select)
        
        await interaction_select.response.edit_message(
            content=f"**Выберите позицию во взводе {squad}:**",
            view=slot_view
        )
    
    select.callback = callback
    view = View(timeout=60)
    view.add_item(select)
    
    await interaction.response.edit_message(
        content=f"**Редактирование взвода:**\n\n"
                f"Боец: {get_soldier_mention(soldier_data)}\n"
                f"Текущий взвод: {soldier_data.get('squad', '—')}\n\n"
                f"Выберите новый взвод:",
        view=view
    )

# ========== РАБОТА С РОЛЯМИ ==========
def get_all_position_role_ids():
    """Возвращает уникальные ID всех ролей должностей"""
    return list(set(POSITION_ROLE_IDS.values()))

async def remove_all_position_roles_from_member(member, guild):
    """Удаляет все роли должностей у участника (для замены при смене должности)"""
    position_role_ids = get_all_position_role_ids()
    roles_to_remove = []
    for role_id in position_role_ids:
        role = guild.get_role(role_id)
        if role and role in member.roles:
            roles_to_remove.append(role)
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Замена должности")

def get_all_rank_role_ids():
    """Возвращает уникальные ID всех ролей званий"""
    return list(set(RANK_ROLES.values()))

async def remove_all_rank_roles_from_member(member, guild):
    """Удаляет все роли званий у участника (для замены при смене звания)"""
    rank_role_ids = get_all_rank_role_ids()
    roles_to_remove = []
    for role_id in rank_role_ids:
        role = guild.get_role(role_id)
        if role and role in member.roles:
            roles_to_remove.append(role)
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Замена звания")

async def assign_roles(discord_id: int, subdivision_role_id: int, rank_role_id: int, interaction: discord.Interaction,
                      position_role_id: int = None):
    """Выдает роли бойцу: подразделение, звание и должность. При смене должности старые роли должностей удаляются."""
    guild = interaction.guild
    if not guild:
        raise Exception("Сервер не найден")
    
    member = await guild.fetch_member(discord_id)
    if not member:
        raise Exception(f"Пользователь {discord_id} не найден на сервере")
    
    subdivision_role = guild.get_role(subdivision_role_id)
    rank_role = guild.get_role(rank_role_id)
    
    if not subdivision_role:
        raise Exception(f"Роль подразделения не найдена: {subdivision_role_id}")
    
    if not rank_role:
        raise Exception(f"Роль звания не найдена: {rank_role_id}")
    
    # Удаляем старые роли званий (A1C, MSgt и т.д.) перед выдачей новой
    await remove_all_rank_roles_from_member(member, guild)
    
    # Удаляем старые роли должностей (Rifleman, Marksman и т.д.) перед выдачей новой
    if position_role_id:
        await remove_all_position_roles_from_member(member, guild)
    
    roles_to_add = [subdivision_role, rank_role]
    if position_role_id:
        position_role = guild.get_role(position_role_id)
        if position_role:
            roles_to_add.append(position_role)
    
    await member.add_roles(*roles_to_add, reason="Вписан в штатную структуру")
    return "Роли успешно выданы"

async def remove_roles(discord_id: int, subdivision_role_id: int, rank_role_id: int, interaction: discord.Interaction,
                      position_role_id: int = None):
    """Снимает роли с бойца"""
    guild = interaction.guild
    if not guild:
        return "Ошибка: сервер не найден"
    
    try:
        member = await guild.fetch_member(discord_id)
    except:
        return "Пользователь не найден на сервере"
    
    roles_to_remove = []
    role_ids = [subdivision_role_id, rank_role_id]
    if position_role_id:
        role_ids.append(position_role_id)
    
    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role and role in member.roles:
            roles_to_remove.append(role)
    
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Выписан из штатной структуры")
        return f"Сняты роли: {', '.join([r.name for r in roles_to_remove])}"
    
    return "Роли не найдены у пользователя"

async def update_rank_roles(discord_id: int, new_rank_role_id: int, old_rank_role_id: int, interaction: discord.Interaction):
    """Обновляет роли звания: удаляет ВСЕ старые роли званий, выдает новую (замена A1C→MSgt и т.д.)."""
    guild = interaction.guild
    if not guild:
        raise Exception("Сервер не найден")
    
    member = await guild.fetch_member(discord_id)
    if not member:
        raise Exception("Пользователь не найден")
    
    new_role = guild.get_role(new_rank_role_id)
    if not new_role:
        raise Exception("Новая роль не найдена")
    
    # Удаляем все роли званий (A1C, MSgt, Cpt и т.д.)
    await remove_all_rank_roles_from_member(member, guild)
    
    await member.add_roles(new_role, reason="Изменение звания")

async def update_position_role(discord_id: int, new_position: str, old_position_role_id: int, 
                               interaction: discord.Interaction) -> bool:
    """Обновляет роль должности: удаляет ВСЕ старые роли должностей, выдает новую (замена Rifleman→Marksman и т.д.)."""
    guild = interaction.guild
    if not guild:
        return False
    try:
        member = await guild.fetch_member(discord_id)
        if not member:
            return False
        
        # Удаляем все роли должностей (Rifleman, Marksman, Pilot и т.д.)
        await remove_all_position_roles_from_member(member, guild)
        
        # Выдаем новую роль должности
        new_role_id = get_position_role_id(new_position)
        if new_role_id:
            new_role = guild.get_role(new_role_id)
            if new_role:
                await member.add_roles(new_role, reason="Изменение должности")
        return True
    except Exception:
        return False

# ========== ОБНОВЛЕНИЕ ИНФОРМАЦИИ ==========
def get_soldier_by_slot(data: dict, subdivision: str, squad: str, slot_index: int):
    """Находит бойца по подразделению, взводу и слоту"""
    for soldier in data.values():
        if (soldier.get("subdivision") == subdivision and
            soldier.get("squad") == squad and
            soldier.get("slot_index") == slot_index):
            return soldier
    return None

# Цвета для embeds (военная тематика)
EMBED_COLOR_HEADER = 0x1e3a5f      # Тёмно-синий
EMBED_COLOR_SQUAD = 0x2c5282       # Синий
EMBED_COLOR_EMPTY = 0x4a5568       # Серый

async def update_staff_display():
    """Обновляет отображение штата в канале — профессиональный формат"""
    channel = bot.get_channel(STAFF_CHANNEL_ID)
    if not channel:
        print(f"❌ Канал штата не найден: {STAFF_CHANNEL_ID}")
        return
    
    # Очистка старых сообщений
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                await message.delete()
                await asyncio.sleep(0.5)
    except:
        pass
    
    data = load_data()
    sent_any = False
    total_soldiers = len(data)
    
    # Заголовок — отправляем первым
    if data or any(SQUADS.get(sub, {}) for sub in SUBDIVISION_ROLES.keys()):
        header_embed = discord.Embed(
            title="📋 Штатная структура Роты А 24th STS",
            description="*Актуальный состав подразделения*",
            color=EMBED_COLOR_HEADER,
            timestamp=datetime.now()
        )
        header_embed.set_footer(text=f"Всего в штате: {total_soldiers} бойцов")
        await channel.send(embed=header_embed)
        sent_any = True
    
    for subdivision in SUBDIVISION_ROLES.keys():
        squads_for_sub = SQUADS.get(subdivision, {})
        
        if squads_for_sub:
            # Отображение по взводам — крупный масштаб через поля embed
            for squad_name, slots in squads_for_sub.items():
                filled = 0
                embed = discord.Embed(
                    title=f"▸ {squad_name}",
                    color=EMBED_COLOR_SQUAD,
                    timestamp=datetime.now()
                )
                
                for i, slot in enumerate(slots):
                    rank_short = slot["rank"].split("|")[-1].strip()
                    soldier = get_soldier_by_slot(data, subdivision, squad_name, i)
                    field_name = f"{i + 1}. {slot['role']} ({rank_short})"
                    if soldier:
                        field_value = get_soldier_mention(soldier)
                        filled += 1
                    else:
                        field_value = "*Вакансия*"
                    embed.add_field(name=field_name, value=field_value, inline=False)
                
                embed.set_footer(text=f"Заполнено: {filled}/{len(slots)} позиций")
                await channel.send(embed=embed)
                sent_any = True
        
        # Бойцы без взвода
        soldiers_without_squad = [s for s in data.values() 
                                 if s["subdivision"] == subdivision and s.get("squad") is None]
        if soldiers_without_squad:
            rank_order = list(RANK_ROLES.keys())
            soldiers_without_squad.sort(key=lambda x: rank_order.index(x["rank"]) if x["rank"] in rank_order else 999)
            
            embed = discord.Embed(
                title="▸ Резерв (вне взводов)",
                color=EMBED_COLOR_EMPTY,
                timestamp=datetime.now()
            )
            for i, soldier in enumerate(soldiers_without_squad, 1):
                rank_short = soldier['rank'].split("|")[-1].strip() if "|" in soldier.get('rank', '') else soldier['rank']
                field_name = f"{i}. {soldier['position']} ({rank_short})"
                field_value = get_soldier_mention(soldier)
                embed.add_field(name=field_name, value=field_value, inline=False)
            embed.set_footer(text=f"Всего: {len(soldiers_without_squad)} бойцов")
            await channel.send(embed=embed)
            sent_any = True
    
    # Пустой штат
    if not sent_any:
        embed = discord.Embed(
            title="📋 ШТАТНАЯ СТРУКТУРА",
            description="*В штате пока нет бойцев*\n\nИспользуйте панель управления для добавления.",
            color=EMBED_COLOR_HEADER,
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)
    
    print("✅ Штатная структура обновлена")

# ========== ПАНЕЛЬ УПРАВЛЕНИЯ ==========
async def create_control_panel():
    """Создает панель управления"""
    channel = bot.get_channel(BUTTON_CHANNEL_ID)
    if not channel:
        print(f"❌ Канал управления не найден: {BUTTON_CHANNEL_ID}")
        return
    
    # Удаление старого сообщения
    message_info = load_control_panel_message()
    if "message_id" in message_info:
        try:
            old_msg = await channel.fetch_message(message_info["message_id"])
            await old_msg.delete()
        except:
            pass
    
    # Создание нового сообщения
    embed = discord.Embed(
        title="👥 УПРАВЛЕНИЕ ШТАТНОЙ СТРУКТУРОЙ",
        description="Используйте кнопки ниже для управления штатом подразделений.",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="📝 Вписать бойца", value="Добавить нового бойца в штат", inline=False)
    embed.add_field(name="🗑️ Выписать бойца", value="Удалить бойца из штата", inline=False)
    embed.add_field(name="✏️ Изменить данные", value="Редактировать данные бойца", inline=False)
    embed.add_field(name="📊 Подразделения", value="• 24th STS'\n", inline=False)
    
    view = MainControlView()
    
    try:
        message = await channel.send(embed=embed, view=view)
        save_control_panel_message({"message_id": message.id, "channel_id": channel.id})
        print(f"✅ Панель управления создана в {channel.name}")
    except Exception as e:
        print(f"❌ Ошибка создания панели: {e}")

# ========== ЛОГИРОВАНИЕ ==========
async def log_action(user: discord.User, action: str):
    """Логирует действие в канал логов"""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📝 ЛОГ ДЕЙСТВИЙ",
            description=f"**Пользователь:** {user.mention}\n**Действие:** {action}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)

# ========== ОБРАБОТЧИКИ СОБЫТИЙ ==========
@bot.event
async def on_ready():
    """Запуск бота"""
    await tree.sync()
    
    print("=" * 60)
    print(f"✅ Бот {bot.user} запущен!")
    print("=" * 60)
    
    await create_control_panel()
    await update_staff_display()
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="штатную структуру"
        )
    )

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Глобальный обработчик взаимодействий"""
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        
        # Обработка выпадающих списков подразделений
        if custom_id.endswith("_subdivision"):
            action_type = custom_id.replace("_subdivision", "")
            selected = interaction.data["values"][0]
            
            user_sessions[interaction.user.id] = {
                "action": action_type,
                "subdivision": selected
            }
            
            if action_type == "enlist":
                await show_squad_selection(interaction)
            else:
                await interaction.response.defer()
                await show_soldier_selection(interaction, action_type)
        
        # Обработка выбора взвода
        elif custom_id == "squad_select":
            selected = interaction.data["values"][0]
            user_id = interaction.user.id
            if user_id in user_sessions:
                user_sessions[user_id]["squad"] = selected
                await show_slot_selection(interaction)
        
        # Обработка выбора слота во взводе
        elif custom_id == "slot_select":
            selected = int(interaction.data["values"][0])
            user_id = interaction.user.id
            if user_id in user_sessions:
                session = user_sessions[user_id]
                subdivision = session.get("subdivision")
                squad = session.get("squad")
                slots = SQUADS.get(subdivision, {}).get(squad, [])
                if 0 <= selected < len(slots):
                    slot_data = slots[selected]
                    user_sessions[user_id]["slot_index"] = selected
                    user_sessions[user_id]["rank"] = slot_data["rank"]
                    user_sessions[user_id]["position"] = slot_data["role"]
                    await show_enlist_form(interaction)
        
        # Обработка выпадающих списков званий
        elif custom_id == "rank_select":
            selected = interaction.data["values"][0]
            
            user_id = interaction.user.id
            if user_id in user_sessions:
                user_sessions[user_id]["rank"] = selected
                await show_position_selection(interaction)
        
        # Обработка выпадающих списков должностей
        elif custom_id == "position_select":
            selected = interaction.data["values"][0]
            
            user_id = interaction.user.id
            if user_id in user_sessions:
                user_sessions[user_id]["position"] = selected
                await show_enlist_form(interaction)

# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Токен не найден! Создайте файл .env с DISCORD_BOT_TOKEN=ваш_токен")
        print("   Скопируйте .env.example в .env и заполните токен.")
        exit(1)
    
    # Инициализация файлов
    if not os.path.exists(DATA_FILE):
        save_data({})
    
    if not os.path.exists(CONTROL_PANEL_MESSAGE_FILE):
        save_control_panel_message({})
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
