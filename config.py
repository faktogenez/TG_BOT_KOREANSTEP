# config.py
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# --- БЛОК 1: СИСТЕМНЫЕ НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
TIMEZONE_OFFSET = 3   # Московское время (UTC+3)
KOREA_TIMEZONE = "Asia/Seoul"  # Корейское время (UTC+9)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@koreanstepTG")
# CHANNEL_ID_INTERNAL = -1003773480771 # Внутренний ID для некоторых методов, если @username не сработает
PINNED_MESSAGE_ID = 244 # ID поста с правилами для редактирования
BRAND_NAME = ""

# --- БЛОК 4: ШАБЛОНЫ ПРИВЕТСТВИЯ ---
MSG_WELCOME_TITLE = "🎉 <b>ДОБРО ПОЖАЛОВАТЬ В KOREAN STEP!</b> 🇰🇷"
MSG_WELCOME_BODY = """Рады видеть тебя в наших рядах. Здесь ты начнешь свой путь к вершинам корейского языка.

🏆 Прямо сейчас наш лидер — <b>{leader_name}</b> со счетом <b>{leader_score} ⭐</b>.
Сможешь его обогнать?

<i>Все правила и навигация — в закрепленном сообщении канала.</i>"""
BTN_WELCOME_START = "🚀 НАЧАТЬ ОБУЧЕНИЕ!"
WELCOME_IMAGE_PATH = "img/welcome.jpg"
WELCOME_FIREWORK_EFFECT = "5104841245755180586"

# --- БЛОК 2: НАСТРОЙКИ РЕЙТИНГА ---
EXCLUDE_IDS = [ADMIN_ID] # Список тех, кто не участвует в рейтинге
UPDATE_INTERVAL_HOURS = 1 # Частота обновления закрепа
LIVE_LEADERBOARD_COUNT = 5 # Количество лидеров в закрепе (ТОП-3, ТОП-5 и т.д.)

RANK_RULES = { 
    0: ("✈️", "Турист"), 
    500: ("🍿", "Фанат дорам"), 
    1500: ("🎤", "Стажёр"), 
    5000: ("👑", "Мастер"), 
    15000: ("🐉", "Наследник Седжона"),
    25000: ("🌟", "Эксперт"),
    40000: ("🔥", "Мастер Йи"),
    60000: ("⚡", "Грандмастер"),
    80000: ("🌀", "Легенда"),
    100000: ("🧙", "Верховный мудрец")
}
# Для обратной совместимости с существующим кодом (get_rank)
RANKS = sorted(
    [(k, f"{v[0]} {v[1]}") for k, v in RANK_RULES.items()],
    key=lambda x: x[0], reverse=True
)

def generate_rank_text():
    lines = ["<b>📈 ТВОЙ РАНГ</b>\n"]
    for i, (threshold, (emoji, name)) in enumerate(sorted(RANK_RULES.items()), 1):
        formatted_threshold = f"{threshold:,}"
        lines.append(f"{i}. <b>{emoji} {name}</b> ({formatted_threshold}+)")
    return "\n".join(lines)

# --- БЛОК 3: ШАБЛОНЫ ТЕКСТА (ДЛЯ РЕДАКТИРОВАНИЯ) ---
PINNED_POST_TEMPLATE = """<b>🏆 ТОП ЛИДЕРОВ</b>
(Обновление 1 раз/час. След. обновление: {next_update} по корейскому времени)
{leaderboard}
{rules}
{footer}"""

RULES_BASE_TEXT = """
<b>💎 НАГРАДЫ</b>

• <b>+5..20 ⭐️</b> — за карточки и тесты.
• <b>x2 ЗВЁЗДЫ</b> — суббота и воскресенье! ⚡️
\n
<b>🔥 БОНУСЫ (СТРАЙКИ)</b>

• <b>5 верных подряд</b> = +5 ⭐️ к счету.
• Ошибка сбрасывает серию, но не прогресс.
\n
{rank_text}
"""

# --- ШАБЛОНЫ ПОДПИСИ (ФУТЕР) ---
POST_FOOTER = """
ᅠ ᅠ
 <a href="https://t.me/koreanstepTG">KOREAN STEP 🇰🇷</a>
ᅠ ᅠ"""

# --- НАСТРОЙКИ ПЛАНИРОВЩИКА ---
SCHEDULER_MODE = "fixed"  # "fixed" или "interval"
FIXED_TIMES = ["09:31", "13:31", "18:31"]
INTERVAL_MINUTES = 15
QUIZ_TIME = "21:30"
WEEKLY_TOP_TIME = "09:30"
WEEKEND_PROMO_TIME = "09:30"

# --- СООБЩЕНИЯ И УВЕДОМЛЕНИЯ ---
MSG_SUBSCRIBE_REQUIRED = "⚠️ Что бы продолжить подпишитесь на канал!"
MSG_ALREADY_ANSWERED = "⚠️ Вы уже ответили\n\"{status}\" на этот вопрос\n\nСтрайк: 🔥  {streak} | Баланс:  ⭐ {score}"
MSG_ANSWER_CORRECT = "ПРАВИЛЬНО ✅"
MSG_ANSWER_WRONG = "НЕВЕРНО ❌"
MSG_TEST_SENT = "✅ Новый тест отправлен в канал!"
MSG_TOP_EMPTY = "🏆 Список лидеров пока пуст!"
MSG_TOP_HEADER = "🏆 ТОП ИГРОКОВ НЕДЕЛИ\n\n"

TOP5_IMAGE_PATH = "img/top5.jpg"
WEEKEND_IMAGE_PATH = "img/weekends.jpg"
TITLE_IMAGE_PATH = "img/title.jpg"

WEEKLY_POST_TEXT = """🏆 ИТОГИ НЕДЕЛИ: ТОП-5 ГЕРОЕВ

Пора узнать, кто доминировал в обучении на этой неделе! 🥇

⭐ Лидеры по звездам:
{top_score_text} 

🔥 Короли страйков:
{top_streak_text} 

ᅠ ᅠ
🔄 НОВАЯ НЕДЕЛЯ — НОВЫЙ ШАНС!

Все страйки 💔 обнулены.
Это твой момент, чтобы ворваться в таблицу лидеров и занять первое место!

⏰ Через МИНУТУ начинаем первый урок!"""

WEEKEND_POST_TEXT = """⚡️ ДВОЙНОЙ ФАРМ ВКЛЮЧЕН!

Только в эти выходные ты получаешь в 2 раза больше звезд за каждое выученное слово и верный ответ! 🌟

🚀 Твои бонусы:
• Обычная карточка: x2 ⭐
• Викторина: x2 ⭐
• Страйк-бонусы: x2 ⭐

Не упусти шанс взлететь в ТОПе и забрать новый ранг!

⏰ Через МИНУТУ начинаем!"""
BTN_MY_RANK_TEXT = "Мой рейтинг 📈"

ALERT_CORRECT = "✅ Верно! +{points} ⭐{bonus_icon}\n\nСтрайк: 🔥  {streak} | Баланс:  ⭐ {score}"
ALERT_BONUS = "✅ Верно! +{points} ⭐{bonus_icon}\n\nПоздравляю!\nЗа каждые 5 🔥 Страйков плюс 5 ⭐!\n\nСтрайк: 🔥  {streak} | Баланс:  ⭐ {score}"
ALERT_QUIZ_CORRECT = "✅ Верно! +{points} ⭐ (Страйк: {streak} 🔥)\n\n{explanation}"
ALERT_QUIZ_WRONG = "❌ Ошибка!\nСтрайк 💔 сброшен!\n\n{explanation}"
ALERT_WRONG = "❌ Ошибка!\n{info}\n\nСтрайк 💔 сброшен!"

# Настройки бонусных выходных
WEEKEND_MULTIPLIER = 2
WEEKEND_ICON = " (БОНУС X2)"
POST_WEEKEND_INFO = "\n(БОНУС X2 - выходные!)"
WEEKEND_POST_HEADER_TEMPLATE = "Уровень: {lvl} | Награда: {stars} ⭐ {info}"
LEVEL_EMOJIS = {"1": "🟢", "2": "🟡", "3": "🔴"}

# Пояснения для ошибок
MSG_ERROR_INFO_RU = "\"{word}\" на корейском - {translation}"
MSG_ERROR_INFO_KR = "\"{word}\" — переводится как {translation}"

# Настройки кнопок и вовлечения
BTN_LIKE_TEXT = "😎 — Я гений корейского!"
BTN_NEW_WORD_TEXT = "🤯 — Моя твоя не понимать"

# Шаблоны текста поста
POST_HEADER_TEMPLATE = "{label}"
POST_QUESTION_KR_RU = "Как переводится слово {word}?"
POST_QUESTION_RU_KR = "Как будет '{word}' по-корейски?"

QUIZ_POST_TEMPLATE = """{header}

<b>Утверждение:</b> {fact}

Это ПРАВДА или ЛОЖЬ? 👇"""

POST_TEMPLATE = """{question}

{header}

{btn_like}
{btn_new}"""

# Награды за уровни
LEVEL_REWARDS = {
    "1": {"stars": 5, "label": "Уровень: 1 | Награда: +5 ⭐"},
    "2": {"stars": 10, "label": "Уровень: 2 | Награда: +10 ⭐"},
    "3": {"stars": 20, "label": "Уровень: 3 | Награда: +20 ⭐"}
}

FONT_RU_REGULAR = "fonts/Roboto-Regular.ttf"
FONT_RU_BOLD = "fonts/Roboto-Bold.ttf"
FONT_KR = "fonts/MaruBuri-SemiBold.ttf"

IMG_SIZE = (800, 450)

LEVEL_COLORS = {"1": (46, 204, 113), "2": (241, 196, 15), "3": (231, 76, 60)}

# Масштабирование блоков (1.0 = 100%)
UI_SCALES = {
    "topic": 1.4,      # Тема (category)
    "level": 1.5,      # Уровень (круг, цифра, надпись)
    "content": 2.0,    # Слово и транскрипция
    "hint": 1.9        # "ВЫБЕРИТЕ ПРАВИЛЬНЫЙ ОТВЕТ НИЖЕ"
}

# Настройки UI в процентах (0.0 - 1.0) от размера изображения
UI_SETTINGS = {
    "category": {"pos": (0.1, 0.13), "size": 0.05, "color": (105, 105, 105), "weight": "regular"},
    "level_circle": {"pos": (0.83, 0.17), "radius": 0.065},
    "level_num": {"pos": (0.83, 0.17), "size": 0.14, "color": (255, 255, 255), "weight": "bold"},
    "level_label": {"pos": (0.83, 0.32), "size": 0.04, "color": (105, 105, 105), "weight": "regular"},
    
    "main_text_ru": {"pos": (0.5, 0.56), "size": 0.095, "color": (0, 0, 0), "weight": "bold", "max_width": 0.9, "line_spacing": 3},
    "main_text_kr": {"pos": (0.5, 0.56), "size": 0.13, "color": (0, 0, 0), "weight": "bold", "max_width": 0.9, "line_spacing": 3},
    "transcription": {"pos": (0.5, 0.67), "size": 0.03, "color": (105, 105, 105), "weight": "regular"},
    
    "footer_line": {"y": 0.80, "margin": 0.1, "width": 0.004, "color": (128, 128, 128)},
    "footer_brand": {"pos": (0.5, 0.79), "size": 0.032, "color": (128, 128, 128), "weight": "regular"},
    "footer_hint": {"pos": (0.5, 0.86), "size": 0.03, "color": (105, 105, 105), "weight": "regular"},
    "footer_arrow": {"pos": (0.5, 0.96), "size": 0.06, "char": "↓", "color": (105, 105, 105)} 
}

# --- НАСТРОЙКИ ГРУППЫ (ОБСУЖДЕНИЯ) ---
MSG_WELCOME_GROUP = "Рады видеть тебя в обсуждениях! Учись и побеждай! 🐉"
ADMIN_NOTIFY_KEYWORDS = ["Вопрос", "вопрос", "Question"] # Тег бота проверяется отдельно
SPAM_LINKS_RE = r"(https?://\S+|t\.me/\S+)" # Регулярка для поиска ссылок

# --- НАСТРОЙКИ ДИЗАЙНА ВИКТОРИНЫ (True/False) --- 
QUIZ_DESIGN = { 
    "bg_colors": ['#4B0082', '#1e3a8a', '#1e4d2b', '#800000', '#4c1d95'], # Случайные фоны 
    "title_text": "ПРАВДА или ЛОЖЬ", #ПРАВДА или ЛОЖЬ
    "title_size": 50, 
    "title_color": "white", 
     
    # Центральная карточка 
    "card_bg": "white", 
    "card_outline": "#6366f1", 
    "card_outline_width": 0, 
    "card_radius": 25, 
    "card_height": 280, # Увеличил высоту белой плашки 
     
    # Текст вопроса 
    "question_size": 45, # Увеличил шрифт вопроса
    "question_color": "#1a1a1a", 
    "question_max_width": 26, # Чуть меньше символов в строке для более крупного шрифта
     
    # Кнопки (визуальные) 
    "show_buttons": False, # Флаг для отображения кнопок на картинке
    "btn_width": 230, 
    "btn_height": 65, 
    "btn_radius": 15, 
    "btn_true_bg": "#8cc63f",  # Зеленый 
    "btn_false_bg": "#ea4335", # Красный 
    "btn_text_size": 30, 
     
    # Декор 
    "show_bg_question": True,  # Показывать ли "!" на фоне 
    "bg_question_config": {
        "count": (15, 25),      # Увеличил количество знаков
        "size": (50, 300),      # Увеличил максимальный размер
        "angle": (-45, 45),     
        "opacity": (120, 190),    # Значительно увеличил прозрачность (теперь точно будет видно)
        "char": "!"             # Заменили "?" на "!"
    }
} 
