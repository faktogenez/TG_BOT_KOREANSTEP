import asyncio, random, json, sys, time, sqlite3, os, re, logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import config
from image_generator import create_quiz_image, create_true_false_image

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_now():
    """Возвращает текущее время по корейскому времени (жесткое правило)"""
    import pytz
    seoul_tz = pytz.timezone(config.KOREA_TIMEZONE)
    return datetime.now(seoul_tz)


def format_number(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)

def get_next_leaderboard_update():
    """Следующее обновление ТОП-лидера по корейскому времени (каждый час)"""
    seoul_tz = pytz.timezone(config.KOREA_TIMEZONE)
    now = datetime.now(seoul_tz)
    future = now + timedelta(hours=config.UPDATE_INTERVAL_HOURS)
    return future.replace(second=0, microsecond=0)

# --- КЛАССЫ ДАННЫХ ---
class QuizCallback(CallbackData, prefix="q"):
    status: str  # "1" - верно, "0" - неверно
    lvl: str
    mode: Optional[str] = None
    w_kr: Optional[str] = None
    w_ru: Optional[str] = None
    q_id: Optional[int] = None # ID вопроса викторины

class PublishCallback(CallbackData, prefix="p"):
    type: str  # "top5" or "weekend"

# --- МИДЛВАРЬ ДЛЯ ПОДПИСКИ ---
class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        # Кэшируем проверку на 30 минут
        if user_id in USER_CACHE and (time.time() - USER_CACHE[user_id]) < 1800:
            return await handler(event, data)
        
        try:
            m = await bot.get_chat_member(config.CHANNEL_ID, user_id)
            if m.status in ['member', 'creator', 'administrator']:
                USER_CACHE[user_id] = time.time()
                return await handler(event, data)
        except:
            pass
        
        if isinstance(event, types.CallbackQuery):
            await event.answer(config.MSG_SUBSCRIBE_REQUIRED, show_alert=True)
        return

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.callback_query.outer_middleware(SubscriptionMiddleware())

# --- ОПТИМИЗИРОВАННАЯ БАЗА ДАННЫХ (Async Wrapper) ---
class AsyncDB:
    def __init__(self, db_path):
        self.db_path = db_path

    async def execute(self, query, params=(), commit=False):
        return await asyncio.to_thread(self._sync_execute, query, params, commit)

    def _sync_execute(self, query, params, commit):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute(query, params)
            if commit:
                conn.commit()
            return c.fetchall()
        finally:
            conn.close()

db = AsyncDB('gamification.db')

async def init_db():
    await db.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, max_streak INTEGER DEFAULT 0)''', commit=True)
    await db.execute('''CREATE TABLE IF NOT EXISTS user_answers 
                 (user_id INTEGER, message_id INTEGER, status TEXT, PRIMARY KEY (user_id, message_id))''', commit=True)
    await db.execute('''CREATE TABLE IF NOT EXISTS answer_events
                 (user_id INTEGER, message_id INTEGER, points INTEGER DEFAULT 0, is_correct INTEGER DEFAULT 0, ts INTEGER, PRIMARY KEY (user_id, message_id))''', commit=True)
    await db.execute('''CREATE TABLE IF NOT EXISTS global_used_quizzes 
                 (quiz_id INTEGER PRIMARY KEY)''', commit=True)
    await db.execute('''CREATE TABLE IF NOT EXISTS greeted_users 
                 (user_id INTEGER PRIMARY KEY)''', commit=True)
    
    # Миграции
    try: await db.execute("ALTER TABLE user_answers ADD COLUMN status TEXT", commit=True)
    except: pass
    try: await db.execute("ALTER TABLE users ADD COLUMN max_streak INTEGER DEFAULT 0", commit=True)
    except: pass

async def get_user(user_id):
    res = await db.execute("SELECT score, streak, max_streak FROM users WHERE user_id = ?", (user_id,))
    if not res:
        await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,), commit=True)
        return {"score": 0, "streak": 0, "max_streak": 0}
    return {"score": res[0][0], "streak": res[0][1], "max_streak": res[0][2]}

async def update_user(user_id, score_add, reset_streak=False):
    # Теперь админы тоже пишутся в БД (для личного рейтинга), но они отфильтрованы в ТОПах
    if reset_streak:
        await db.execute("UPDATE users SET score = score + ?, streak = 0 WHERE user_id = ?", (score_add, user_id), commit=True)
    else:
        await db.execute("UPDATE users SET score = score + ?, streak = streak + 1 WHERE user_id = ?", (score_add, user_id), commit=True)
        await db.execute("UPDATE users SET max_streak = streak WHERE streak > max_streak AND user_id = ?", (user_id,), commit=True)

async def get_answer_status(user_id, message_id):
    res = await db.execute("SELECT status FROM user_answers WHERE user_id = ? AND message_id = ?", (user_id, message_id))
    return res[0][0] if res else None

async def record_answer(user_id, message_id, status):
    await db.execute("INSERT OR REPLACE INTO user_answers (user_id, message_id, status) VALUES (?, ?, ?)", 
              (user_id, message_id, status), commit=True)

async def record_answer_event(user_id, message_id, points, is_correct):
    ts = int(get_now().timestamp())
    await db.execute(
        "INSERT OR IGNORE INTO answer_events (user_id, message_id, points, is_correct, ts) VALUES (?, ?, ?, ?, ?)",
        (user_id, message_id, points, 1 if is_correct else 0, ts),
        commit=True
    )

async def get_top_last_24h(limit=5):
    since_ts = int(get_now().timestamp()) - 86400
    placeholders = ','.join(['?'] * len(config.EXCLUDE_IDS))
    query = f"""
        SELECT user_id,
               COALESCE(SUM(points), 0) AS pts,
               COALESCE(SUM(is_correct), 0) AS correct_cnt,
               COUNT(*) AS total_cnt
        FROM answer_events
        WHERE ts >= ?
          AND user_id NOT IN ({placeholders})
        GROUP BY user_id
        ORDER BY pts DESC, correct_cnt DESC, total_cnt DESC
        LIMIT ?
    """
    return await db.execute(query, (since_ts, *config.EXCLUDE_IDS, limit))

def get_rank(score):
    for threshold, name in config.RANKS:
        if score >= threshold: return name
    return config.RANKS[-1][1]

async def get_top_players(limit=10):
    # Фильтруем EXCLUDE_IDS в SQL запросе
    placeholders = ','.join(['?'] * len(config.EXCLUDE_IDS))
    query = f"SELECT user_id, score FROM users WHERE user_id NOT IN ({placeholders}) ORDER BY score DESC LIMIT ?"
    return await db.execute(query, (*config.EXCLUDE_IDS, limit))

async def get_weekly_top():
    # Фильтруем EXCLUDE_IDS в SQL запросе
    placeholders = ','.join(['?'] * len(config.EXCLUDE_IDS))
    
    top_score_query = f"SELECT user_id, score FROM users WHERE user_id NOT IN ({placeholders}) ORDER BY score DESC LIMIT 5"
    top_score = await db.execute(top_score_query, (*config.EXCLUDE_IDS,))
    
    top_streak_query = f"SELECT user_id, max_streak FROM users WHERE user_id NOT IN ({placeholders}) ORDER BY max_streak DESC LIMIT 5"
    top_streak = await db.execute(top_streak_query, (*config.EXCLUDE_IDS,))
    
    return top_score, top_streak

async def reset_weekly_stats():
    await db.execute("UPDATE users SET streak = 0, max_streak = 0", commit=True)
    await db.execute("DELETE FROM user_answers", commit=True)

BOT_INFO = None

# --- ОБРАБОТКА ГРУППОВЫХ СООБЩЕНИЙ ---
@dp.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def handle_group_messages(m: types.Message):
    global BOT_INFO
    if not m.from_user: return
    content = m.text or m.caption or ""
    entities = m.entities or m.caption_entities or []
    
    # 1. Фильтр мата и спама (ссылки)
    if content and re.search(config.SPAM_LINKS_RE, content):
        # Проверяем, не админ ли это
        member = await bot.get_chat_member(m.chat.id, m.from_user.id)
        if member.status not in ['administrator', 'creator']:
            try:
                await m.delete()
                return # Прекращаем обработку удаленного сообщения
            except:
                pass

    # 2. Уведомление админа (Вопрос или Тег)
    is_question = any(word.lower() in content.lower() for word in config.ADMIN_NOTIFY_KEYWORDS)
    is_tagged = False
    
    if not BOT_INFO:
        BOT_INFO = await bot.get_me()
        
    for entity in entities:
        if entity.type == "mention":
            mention = content[entity.offset:entity.offset + entity.length]
            if mention == f"@{BOT_INFO.username}":
                is_tagged = True
                break

    if is_question or is_tagged:
        try:
            # Пересылаем сообщение админу
            await bot.forward_message(
                chat_id=config.ADMIN_ID,
                from_chat_id=m.chat.id,
                message_id=m.message_id
            )
            # Уведомляем админа о контексте
            reason = "тегнул бота" if is_tagged else "задал вопрос"
            username = m.from_user.username or m.from_user.first_name or str(m.from_user.id)
            await bot.send_message(
                config.ADMIN_ID, 
                f"💡 Пользователь @{username} {reason} в группе."
            )
        except Exception as e:
            print(f"Ошибка уведомления админа: {e}")

    # 3. Приветствие новых участников (одноразовое)
    user_id = m.from_user.id
    res = await db.execute("SELECT user_id FROM greeted_users WHERE user_id = ?", (user_id,))
    if not res:
        await db.execute("INSERT INTO greeted_users (user_id) VALUES (?)", (user_id,), commit=True)
        try:
            # Отвечаем на сообщение пользователя приветствием
            await m.reply(config.MSG_WELCOME_GROUP)
        except:
            pass

# --- ГЛОБАЛЬНЫЙ КЭШ ---
VOCAB = {}
USER_CACHE = {} # {user_id: last_check_time}
USED_WORDS = {} 
LAST_QUIZ_MODE = None # 0 - KR, 1 - RU
USER_INFO_CACHE = {} # {user_id: {"name": str, "time": float}}
ADMIN_PREVIEWS = {} # {admin_id: data_dict}

# --- УПРАВЛЕНИЕ СОСТОЯНИЕМ (Приветствия) ---
STATE_FILE = "bot_state.json"

def get_bot_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"welcome_enabled": True} # По умолчанию включено

def save_bot_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

async def get_cached_user_name(user_id):
    """Получает имя пользователя из Telegram с кэшированием на 24 часа"""
    now = time.time()
    if user_id in USER_INFO_CACHE and (now - USER_INFO_CACHE[user_id]["time"]) < 86400:
        return USER_INFO_CACHE[user_id]["name"]

    name = None

    # 1) Пробуем получить самою сущность пользователя
    try:
        user = await bot.get_chat(user_id)
        if hasattr(user, 'full_name') and user.full_name:
            name = user.full_name
        elif hasattr(user, 'username') and user.username:
            name = f"@{user.username}"
    except Exception:
        name = None

    # 2) Если не удалось, пробуем взять из участников канала/чата (если применимо)
    if not name:
        try:
            member = await bot.get_chat_member(config.CHANNEL_ID, user_id)
            u = member.user
            if u.full_name:
                name = u.full_name
            elif u.username:
                name = f"@{u.username}"
        except Exception:
            name = None

    # 3) Дефолтное имя, чтобы не было только ID
    if not name:
        name = f"Игрок {user_id}"

    USER_INFO_CACHE[user_id] = {"name": name, "time": now}
    return name

async def update_live_leaderboard():
    """Обновляет закрепленный пост с правилами и ТОП-лидерами"""
    try:
        state = get_bot_state()
        pinned_message_id = state.get("pinned_message_id") or config.PINNED_MESSAGE_ID

        async def resolve_pinned_message_id():
            try:
                chat = await bot.get_chat(config.CHANNEL_ID)
                pm = getattr(chat, "pinned_message", None)
                if pm and getattr(pm, "message_id", None):
                    return pm.message_id
            except Exception:
                return None
            return None

        async def resolve_channel_id():
            try:
                chat = await bot.get_chat(config.CHANNEL_ID)
                return chat.id
            except Exception:
                return config.CHANNEL_ID

        chat_id = await resolve_channel_id()

        top_players = await get_top_players(limit=3)
        
        # Группируем игроков с одинаковыми баллами
        score_groups = {}
        for uid, score in top_players:
            if score not in score_groups:
                score_groups[score] = []
            score_groups[score].append(uid)
        
        # Сортируем баллы по убыванию
        sorted_scores = sorted(score_groups.keys(), reverse=True)
        
        leaderboard_text = "<b>🏆 ТОП-3 ЛИДЕРОВ</b>\n\n"
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅", "🏅"] # Медали для ТОП-10
        
        for i, score in enumerate(sorted_scores):
            if i >= 3: break
            uids = score_groups[score]
            names = []
            total_streak = 0
            
            for uid in uids:
                name = await get_cached_user_name(uid)
                names.append(name)
                
                # Получаем страйк для каждого (берем макс. страйк для группы)
                u_res = await db.execute("SELECT streak FROM users WHERE user_id = ?", (uid,))
                total_streak = max(total_streak, u_res[0][0] if u_res else 0)
            
            rank = get_rank(score)
            combined_names = ", ".join(names)
            stats_line = f"Ранг:      {rank}\nЗвёзды: ⭐️ {score:,}\nСтрайк: 🔥 {total_streak:,}"
            
            medal = medals[i] if i < len(medals) else "🏅"
            leaderboard_text += f"<blockquote><b>{i+1} место:</b> {combined_names}\n{stats_line}</blockquote>\n\n"

        if not top_players:
            leaderboard_text = "<b>🏆 ТОП-3 ЛИДЕРОВ</b>\n\n<i>Список лидеров пока пуст. Стань первым!</i>\n\n"

        top_today = await get_top_last_24h(limit=5)
        leaderboard_text += "<b>⚡️ ТОП ЗА 24 ЧАСА</b>\n\n"
        if not top_today:
            leaderboard_text += "<i>Пока нет активности за последние 24 часа.</i>\n\n"
        else:
            for i, (uid, pts, correct_cnt, total_cnt) in enumerate(top_today, 1):
                name = await get_cached_user_name(uid)
                u_res = await db.execute("SELECT score, streak FROM users WHERE user_id = ?", (uid,))
                streak = u_res[0][1] if u_res else 0
                leaderboard_text += f"{i}. {name} — ⭐️ {format_number(pts)} (🔥 {format_number(streak)})\n"
            leaderboard_text += "\n"

        # Следующее обновление по корейскому времени
        next_update = get_next_leaderboard_update().strftime('%H:%M')

        # Формируем текст по шаблону из конфига
        final_text = config.PINNED_POST_TEMPLATE.format(
            leaderboard=leaderboard_text,
            rules=config.RULES_BASE_TEXT.format(rank_text=config.generate_rank_text()),
            footer=config.POST_FOOTER,
            next_update=next_update
        )
        
        # Кнопка "Мой рейтинг"
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🏆 МОЙ РЕЙТИНГ", callback_data="show_my_rank", style="success"))

        async def try_update(message_id: int) -> bool:
            text_err = None
            caption_err = None
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=final_text,
                    parse_mode="HTML",
                    reply_markup=kb.as_markup()
                )
                return True
            except TelegramBadRequest as e:
                text_err = str(e)

            try:
                await bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=final_text,
                    parse_mode="HTML",
                    reply_markup=kb.as_markup()
                )
                return True
            except TelegramBadRequest as e:
                caption_err = str(e)
                if "MEDIA_CAPTION_TOO_LONG" in str(e):
                    try:
                        await bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=message_id,
                            caption=final_text[:1024],
                            parse_mode="HTML",
                            reply_markup=kb.as_markup()
                        )
                        return True
                    except TelegramBadRequest:
                        return False
                print(f"⚠️ Не удалось обновить закреп (text_err={text_err}, caption_err={caption_err})")
                return False

        if await try_update(pinned_message_id):
            print(f"[{get_now()}] Закрепленный пост успешно обновлен.")
            return

        latest_pinned_id = await resolve_pinned_message_id()
        if latest_pinned_id and latest_pinned_id != pinned_message_id:
            pinned_message_id = latest_pinned_id
            state["pinned_message_id"] = pinned_message_id
            save_bot_state(state)
            if await try_update(pinned_message_id):
                print(f"[{get_now()}] Закрепленный пост успешно обновлен.")
                return

        print(f"⚠️ Не удалось обновить закреп: MESSAGE_ID_INVALID.")
    except Exception as e:
        print(f"Критическая ошибка update_live_leaderboard: {e}")

async def get_next_quiz_fact():
    """Возвращает следующий случайный факт из викторины без повторов (через БД)"""
    try:
        from info_data import TRUE_OR_FALSE_DATA
        if not TRUE_OR_FALSE_DATA: return None
        
        # Получаем список уже использованных ID из БД
        used_res = await db.execute("SELECT quiz_id FROM global_used_quizzes")
        used_ids = [r[0] for r in used_res]
        
        available = [q for q in TRUE_OR_FALSE_DATA if q["id"] not in used_ids]
        
        # Если всё закончилось — сбрасываем историю
        if not available:
            await db.execute("DELETE FROM global_used_quizzes", commit=True)
            available = TRUE_OR_FALSE_DATA
            
        q = random.choice(available)
        
        # Записываем ID как использованный СРАЗУ, чтобы избежать повторов при быстрых вызовах
        await db.execute("INSERT INTO global_used_quizzes (quiz_id) VALUES (?)", (q["id"],), commit=True)
        
        # ЖЕСТКОЕ ПРАВИЛО: Проверяем часовой пояс МСК (через get_now)
        now_moscow = get_now()
        is_weekend = now_moscow.weekday() >= 5
        base_reward = 15 if q.get("difficulty") == "hard" else 10
        stars = base_reward * config.WEEKEND_MULTIPLIER if is_weekend else base_reward
        
        header = f"ПРАВДА или ЛОЖЬ | Награда: +{stars} ⭐"
        if is_weekend: header += config.POST_WEEKEND_INFO
        
        return {
            "is_quiz": True,
            "q_id": q["id"],
            "main_text": q["text"],
            "is_true": q["is_true"],
            "explanation": q["explanation"],
            "header": header,
            "q": "Выберите правильный ответ: ПРАВДА или ЛОЖЬ?",
            "level": "quiz",
            "reward": base_reward
        }
    except Exception as e:
        print(f"Ошибка выбора факта: {e}")
        return None

async def get_quiz_data():
    global VOCAB, USED_WORDS, LAST_QUIZ_MODE
    
    # ЖЕСТКОЕ ПРАВИЛО: Викторина исключена из общего цикла.
    # Она отправляется только по расписанию в 21:30 через send_evening_quiz.
        
    if not VOCAB:
        with open('vocabulary.json', 'r', encoding='utf-8') as f: VOCAB = json.load(f)
    
    now = time.time()
    USED_WORDS = {w: t for w, t in USED_WORDS.items() if now - t < 86400}

    categories = list(VOCAB.keys())
    cat = random.choice(categories)
    levels = list(VOCAB[cat].keys())
    lvl = random.choice(levels)
    
    words_in_lvl = VOCAB[cat][lvl]
    available = [w for w in words_in_lvl if w["kr"] not in USED_WORDS]
    target = random.choice(available) if available else random.choice(words_in_lvl)
    
    USED_WORDS[target["kr"]] = now
    
    # Чередуем режим: 0 (KR->RU) и 1 (RU->KR)
    if LAST_QUIZ_MODE is None:
        mode = random.randint(0, 1)
    else:
        mode = 1 - LAST_QUIZ_MODE
    
    LAST_QUIZ_MODE = mode
    
    all_words = [w for l in VOCAB[cat].values() for w in l]

    if mode == 0:
        main, trans, correct = target["kr"], target.get("trans", ""), target["ru"]
        wrong_obj = random.choice([w for w in all_words if w["ru"] != correct])
        wrong = wrong_obj["ru"]
    else:
        main, trans, correct = target["ru"], "", target["kr"]
        wrong_obj = random.choice([w for w in all_words if w["kr"] != correct])
        wrong = wrong_obj["kr"]

    reward_info = config.LEVEL_REWARDS.get(lvl, {"label": "Бонус! ⭐️", "stars": 5})
    
    # ЖЕСТКОЕ ПРАВИЛО: Всегда используем время МСК (через get_now)
    now_moscow = get_now()
    is_weekend = now_moscow.weekday() >= 5
    
    if is_weekend:
        stars = reward_info["stars"] * config.WEEKEND_MULTIPLIER
        emoji = config.LEVEL_EMOJIS.get(lvl, "⭐️")
        header_text = config.WEEKEND_POST_HEADER_TEMPLATE.format(
            lvl=lvl, emoji=emoji, stars=stars, info=config.POST_WEEKEND_INFO
        )
    else:
        header_text = reward_info["label"]

    return {
        "category": cat.upper(), "level": lvl, "main_text": main, 
        "transcription": trans, "correct": correct, "wrong": wrong, "mode": mode,
        "wrong_word_kr": wrong_obj["kr"], "wrong_word_ru": wrong_obj["ru"],
        "header": config.POST_HEADER_TEMPLATE.format(label=header_text),
        "q": config.POST_QUESTION_KR_RU.format(word=main) if mode == 0 else config.POST_QUESTION_RU_KR.format(word=main)
    }

@dp.callback_query(QuizCallback.filter())
async def handle_click(c: types.CallbackQuery, callback_data: QuizCallback):
    user_id, message_id = c.from_user.id, c.message.message_id
    
    # ЖЕСТКОЕ ПРАВИЛО: Админы ПОЛУЧАЮТ баллы (для тестов), но ИСКЛЮЧЕНЫ из рейтингов (в get_top_players)
    # Удаляем запрет на начисление для EXCLUDE_IDS
    
    prev_status = await get_answer_status(user_id, message_id)
    if prev_status:
        u = await get_user(user_id)
        status_text = config.MSG_ANSWER_CORRECT if prev_status == "correct" else config.MSG_ANSWER_WRONG
        return await c.answer(config.MSG_ALREADY_ANSWERED.format(status=status_text, streak=u['streak'], score=u['score']), show_alert=True)

    is_quiz = callback_data.lvl == "quiz"
    
    # Получаем объяснение для викторины заранее, если нужно
    explanation = ""
    if is_quiz and callback_data.q_id:
        try:
            from info_data import TRUE_OR_FALSE_DATA
            q = next((item for item in TRUE_OR_FALSE_DATA if item["id"] == callback_data.q_id), None)
            explanation = q["explanation"] if q else ""
        except: pass

    if callback_data.status == "1":
        # МГНОВЕННАЯ ЗАПИСЬ ОТВЕТА для предотвращения двойного нажатия
        await record_answer(user_id, message_id, "correct")
        
        # Начисление звезд
        base_points = 10 if is_quiz else config.LEVEL_REWARDS.get(callback_data.lvl, {"stars": 5})["stars"]
        now_moscow = get_now()
        is_weekend = now_moscow.weekday() >= 5
        points = base_points * config.WEEKEND_MULTIPLIER if is_weekend else base_points
        
        u = await get_user(user_id)
        new_streak = u['streak'] + 1
        bonus = 5 if new_streak % 5 == 0 else 0
        
        await record_answer_event(user_id, message_id, points + bonus, True)
        await update_user(user_id, points + bonus)
        u = await get_user(user_id)
        
        if is_quiz:
            msg = config.ALERT_QUIZ_CORRECT.format(points=points, streak=u['streak'], explanation=explanation)
        else:
            msg = (config.ALERT_BONUS if bonus else config.ALERT_CORRECT).format(
                points=points, streak=u['streak'], score=u['score'], 
                bonus_icon=config.WEEKEND_ICON if is_weekend else ""
            )
    else:
        # МГНОВЕННАЯ ЗАПИСЬ ОТВЕТА для предотвращения двойного нажатия
        await record_answer(user_id, message_id, "wrong")
        await record_answer_event(user_id, message_id, 0, False)
        await update_user(user_id, 0, reset_streak=True)
        u = await get_user(user_id)
        
        if is_quiz:
            msg = config.ALERT_QUIZ_WRONG.format(explanation=explanation)
        else:
            info = config.MSG_ERROR_INFO_RU.format(word=callback_data.w_ru, translation=callback_data.w_kr) if callback_data.mode == "0" else \
                   config.MSG_ERROR_INFO_KR.format(word=callback_data.w_kr, translation=callback_data.w_ru)
            msg = config.ALERT_WRONG.format(info=info)
            
    # Добавляем информацию о месте в рейтинге (как просил юзер)
    placeholders = ','.join(['?'] * len(config.EXCLUDE_IDS))
    pos_res = await db.execute(
        f"SELECT COUNT(*) FROM users WHERE score > ? AND user_id NOT IN ({placeholders})", 
        (u['score'], *config.EXCLUDE_IDS)
    )
    pos = (pos_res[0][0] if pos_res else 0) + 1
    msg += f"\n\nМесто в рейтинге: 🏆 #{pos}\nНажми в закрепе, чтобы увидеть подробности"

    await c.answer(msg, show_alert=True)

@dp.callback_query(PublishCallback.filter())
async def handle_publish(c: types.CallbackQuery, callback_data: PublishCallback):
    if c.from_user.id != config.ADMIN_ID:
        return await c.answer("❌ Доступ запрещен.", show_alert=True)

    if callback_data.type == "top5":
        await send_weekly_report()
        await c.answer("✅ ТОП-5 опубликован в канал!")
    elif callback_data.type == "weekend":
        await send_weekend_promo()
        await c.answer("✅ Промо выходных опубликовано в канал!")

    # Удалить превью сообщение
    await c.message.delete()

async def send_new_post(data=None, chat_id=None, is_preview=False):
    try:
        if not data:
            data = await get_quiz_data()
        
        target_id = chat_id or config.CHANNEL_ID
        is_true_false = data.get('is_quiz', False)
        
        if is_true_false:
            path = await asyncio.to_thread(create_true_false_image, data)
            kb = InlineKeyboardBuilder()
            
            # ПРАВДА (слева) всегда зеленая, ЛОЖЬ (справа) всегда красная
            is_true = data.get('is_true', True)
            q_id = data.get('q_id')
            
            kb.row(
                InlineKeyboardButton(
                    text="ПРАВДА", 
                    callback_data=QuizCallback(status="1" if is_true else "0", lvl="quiz", q_id=q_id).pack(),
                    style="success"
                ),
                InlineKeyboardButton(
                    text="ЛОЖЬ", 
                    callback_data=QuizCallback(status="0" if is_true else "1", lvl="quiz", q_id=q_id).pack(),
                    style="danger"
                )
            )
        else:
            path = await asyncio.to_thread(create_quiz_image, data)
            kb = InlineKeyboardBuilder()
            # Варианты ответов синим цветом (primary)
            btn_correct = InlineKeyboardButton(text=data['correct'], callback_data=QuizCallback(status="1", lvl=data['level']).pack(), style="primary")
            btn_wrong = InlineKeyboardButton(text=data['wrong'], callback_data=QuizCallback(
                status="0", lvl=data['level'], mode=str(data['mode']), 
                w_kr=data['wrong_word_kr'][:15], w_ru=data['wrong_word_ru'][:15]
            ).pack(), style="primary")
            
            btns = [btn_correct, btn_wrong]
            random.shuffle(btns)
            kb.row(*btns)

        # Если это предпросмотр для админа - добавляем кнопку "ОПУБЛИКОВАТЬ"
        if is_preview:
            kb.row(InlineKeyboardButton(text="🚀 ОПУБЛИКОВАТЬ", callback_data="publish_preview"))
        
        caption_template = config.QUIZ_POST_TEMPLATE if is_true_false else config.POST_TEMPLATE
        
        caption_data = {
            "header": data['header'],
            "question": data.get('q', ""),
            "btn_like": config.BTN_LIKE_TEXT,
            "btn_new": config.BTN_NEW_WORD_TEXT
        }
        
        if is_true_false:
            caption_data["fact"] = data.get('main_text', '')

        # ЖЕСТКОЕ ПРАВИЛО: Добавляем POST_FOOTER абсолютно ко всем постам
        final_caption = caption_template.format(**caption_data) + config.POST_FOOTER

        await bot.send_photo(
            target_id, FSInputFile(path),
            caption=final_caption,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e: print(f"Критическая ошибка: {e}")

async def send_evening_quiz():
    """Ежедневная викторина в 21:30"""
    try:
        data = await get_next_quiz_fact()
        if data:
            await send_new_post(data)
    except Exception as e: print(f"Ошибка вечерней викторины: {e}")

@dp.message(F.text == "/test")
async def cmd_test(m: types.Message):
    # 1. Обычная карточка (СЛУЧАЙНОЕ СЛОВО)
    word_data = await get_quiz_data()
    # Если вдруг get_quiz_data вернула викторину (хотя мы это убрали из цикла, но на всякий случай)
    while word_data.get('is_quiz'):
        word_data = await get_quiz_data()
    await send_new_post(word_data, chat_id=m.chat.id)
    
    # 2. Викторина (СЛУЧАЙНЫЙ ФАКТ)
    quiz_data = await get_next_quiz_fact()
    if quiz_data:
        await send_new_post(quiz_data, chat_id=m.chat.id)
    
    # 3. ТОП-5 недели
    await send_weekly_report(chat_id=m.chat.id)
    
    # 4. Промо выходных
    await send_weekend_promo(chat_id=m.chat.id)
    
    await m.answer("✅ Все типы постов отправлены! Каждый раз они должны быть РАЗНЫМИ.")

async def send_weekly_report(chat_id=None, add_publish_button=False):
    top_score, top_streak = await get_weekly_top()
    target_id = chat_id or config.CHANNEL_ID
    
    async def format_list(data, unit):
        lines = []
        for i, (uid, val) in enumerate(data, 1):
            name = await get_cached_user_name(uid)
            lines.append(f"{i}. {name} — {val} {unit}")
        return "\n".join(lines) if lines else "Пока нет данных"

    report = config.WEEKLY_POST_TEXT.format(
        top_score_text=await format_list(top_score, "⭐"),
        top_streak_text=await format_list(top_streak, "🔥")
    ) + config.POST_FOOTER

    kb = None
    if add_publish_button:
        kb = InlineKeyboardBuilder()
        kb.button(text="🚀 ОПУБЛИКОВАТЬ", callback_data=PublishCallback(type="top5").pack())

    try:
        await bot.send_photo(target_id, FSInputFile(config.TOP5_IMAGE_PATH), caption=report, parse_mode="HTML", reply_markup=kb.as_markup() if kb else None)
    except:
        await bot.send_message(target_id, report, parse_mode="HTML", reply_markup=kb.as_markup() if kb else None)

    # Сброс страйков теперь делается отдельным cron-задачей в main() в понедельник 09:30
    # Поэтому здесь не обязательно делать reset_weekly_stats()

async def send_weekend_promo(chat_id=None, add_publish_button=False):
    """Промо выходных: Суббота и Воскресенье 09:00"""
    target_id = chat_id or config.CHANNEL_ID
    
    final_caption = config.WEEKEND_POST_TEXT + config.POST_FOOTER
    
    kb = None
    if add_publish_button:
        kb = InlineKeyboardBuilder()
        kb.button(text="🚀 ОПУБЛИКОВАТЬ", callback_data=PublishCallback(type="weekend").pack())
    
    try:
        await bot.send_photo(target_id, FSInputFile(config.WEEKEND_IMAGE_PATH), caption=final_caption, parse_mode="HTML", reply_markup=kb.as_markup() if kb else None)
    except Exception as e:
        print(f"Ошибка промо выходных: {e}")
        await bot.send_message(target_id, final_caption, parse_mode="HTML", reply_markup=kb.as_markup() if kb else None)

@dp.callback_query(F.data == "show_my_rank")
async def handle_show_rank(c: types.CallbackQuery):
    user_id = c.from_user.id
    u = await get_user(user_id)
    
    # Общее количество участников (без админов)
    placeholders = ','.join(['?'] * len(config.EXCLUDE_IDS))
    total_res = await db.execute(
        f"SELECT COUNT(*) FROM users WHERE user_id NOT IN ({placeholders})", 
        (*config.EXCLUDE_IDS,)
    )
    total_users = total_res[0][0] if total_res else 0

    # Место в рейтинге (без админов)
    # Даже если на кнопку нажал админ, мы считаем его место ТАК, КАК ЕСЛИ БЫ ОН БЫЛ ОБЫЧНЫМ ИГРОКОМ
    pos_res = await db.execute(
        f"SELECT COUNT(*) FROM users WHERE score > ? AND user_id NOT IN ({placeholders})", 
        (u['score'], *config.EXCLUDE_IDS)
    )
    pos = (pos_res[0][0] if pos_res else 0) + 1
    
    # Ранг и следующий порог
    current_score = u['score']
    rank_name = "Турист"
    next_rank_name = "НАСЛЕДНИК СЕДЖОНА"
    diff = 0
    
    sorted_thresholds = sorted(config.RANK_RULES.keys())
    rank_emoji = "✈️"
    next_rank_emoji = "🍿"
    
    for i, threshold in enumerate(sorted_thresholds):
        if current_score >= threshold:
            r_emoji, r_name  = config.RANK_RULES[threshold]
            rank_name = f"{r_name}"
            rank_emoji = f"{r_emoji}"
            if i + 1 < len(sorted_thresholds):
                next_threshold = sorted_thresholds[i+1]
                n_emoji, n_name = config.RANK_RULES[next_threshold]
                next_rank_name = n_name
                next_rank_emoji = n_emoji
                diff = next_threshold - current_score
            else:
                next_rank_name = "MAX"
    
    # Формируем лаконичный Alert (акцент на заглавные буквы)
    text = (
        f"👤 МОЙ РЕЙТИНГ\n"
        f"━━━━━━━━━━━━━━\n"
        f"{rank_emoji} Ранг: {rank_name}\n"
        f"🏆 Место: #{format_number(pos)} из {format_number(total_users)}\n"
        f"⭐️ Звёзды: {format_number(u['score'])}\n"
        f"🔥 Страйк: {format_number(u['streak'])}\n"
        f"━━━━━━━━━━━━━━\n"
    )

    if next_rank_name != "MAX":
        text += f"Осталось: {format_number(diff)} ⭐ до ранга: «{next_rank_name} {next_rank_emoji}»"
    else:
        text += "👑 ВЫ — НАСЛЕДНИК СЕДЖОНА!"
        
    await c.answer(text, show_alert=True)

async def scheduler():
    # Удаляем старую логику цикла и заменяем на APScheduler
    pass

@dp.message(F.text == "/top")
async def cmd_top(m: types.Message):
    top = await get_top_players()
    if not top: return await m.answer(config.MSG_TOP_EMPTY)

    text = config.MSG_TOP_HEADER
    for i, (uid, score) in enumerate(top, 1):
        name = await get_cached_user_name(uid)
        text += f"{i}. {name} — {format_number(score)} ⭐ ({get_rank(score)})\n"
    await m.answer(text, parse_mode="Markdown")

@dp.message(F.text == "/top5")
async def cmd_top5(m: types.Message):
    if m.from_user.id != config.ADMIN_ID:
        return await m.answer("❌ Доступ запрещен.")
    await send_weekly_report(chat_id=m.chat.id, add_publish_button=True)
    await m.answer("Превью ТОП-5 отправлено выше. Нажми '🚀 ОПУБЛИКОВАТЬ' для публикации в канал.")

@dp.message(F.text == "/weekend")
async def cmd_weekend(m: types.Message):
    if m.from_user.id != config.ADMIN_ID:
        return await m.answer("❌ Доступ запрещен.")
    await send_weekend_promo(chat_id=m.chat.id, add_publish_button=True)
    await m.answer("Превью промо выходных отправлено выше. Нажми '🚀 ОПУБЛИКОВАТЬ' для публикации в канал.")

async def main():
    await init_db()
    
    # Настройка часового пояса (Корея)
    korea_tz = pytz.timezone(config.KOREA_TIMEZONE)
    
    # Настройка APScheduler
    scheduler_obj = AsyncIOScheduler(timezone=korea_tz)
    
    # 1. Посты с карточками (интервал или фиксированное время)
    if config.SCHEDULER_MODE == "interval":
        scheduler_obj.add_job(send_new_post, 'interval', minutes=config.INTERVAL_MINUTES)
        # Первый пост сразу
        asyncio.create_task(send_new_post())
    else:
        for t in config.FIXED_TIMES:
            hour, minute = map(int, t.split(':'))
            scheduler_obj.add_job(send_new_post, 'cron', hour=hour, minute=minute)
            
    # 2. ТОП-5 недели (Понедельник)
    w_top_h, w_top_m = map(int, config.WEEKLY_TOP_TIME.split(':'))
    scheduler_obj.add_job(send_weekly_report, CronTrigger(day_of_week='mon', hour=w_top_h, minute=w_top_m))

    # Жесткое правило: сброс страйков строго в понедельник 09:30 (МСК)
    scheduler_obj.add_job(reset_weekly_stats, CronTrigger(day_of_week='mon', hour=w_top_h, minute=w_top_m))
    
    # 3. Промо выходных (Суббота и Воскресенье)
    w_promo_h, w_promo_m = map(int, config.WEEKEND_PROMO_TIME.split(':'))
    scheduler_obj.add_job(send_weekend_promo, CronTrigger(day_of_week='sat,sun', hour=w_promo_h, minute=w_promo_m))
    
    # 4. Вечерняя викторина (Ежедневно)
    quiz_h, quiz_m = map(int, config.QUIZ_TIME.split(':'))
    scheduler_obj.add_job(
        send_evening_quiz, 
        'cron', 
        hour=quiz_h, 
        minute=quiz_m,
        id='evening_quiz_job',
        replace_existing=True
    )

    # 5. Обновление закрепа с рейтингом (каждый час)
    scheduler_obj.add_job(
        update_live_leaderboard,
        'interval',
        hours=config.UPDATE_INTERVAL_HOURS,
        id='update_leaderboard_job',
        replace_existing=True
    )
    
    # Запускаем обновление закрепа сразу при старте
    asyncio.create_task(update_live_leaderboard())
    
    scheduler_obj.start()
    
    print(f"Бот в сети (МСК {config.TIMEZONE_OFFSET:+})...")
    await dp.start_polling(bot)

# --- ПРИВЕТСТВИЕ И ОТПИСКА ПОДПИСЧИКОВ (КАНАЛ) ---
@dp.chat_member(F.chat.id == config.CHANNEL_ID)
async def handle_chat_member_updates(event: types.ChatMemberUpdated):
    # 1. ОБРАБОТКА НОВОГО ПОДПИСЧИКА (Приветствие)
    if event.new_chat_member.status == "member" and event.old_chat_member.status in ["left", "kicked"]:
        state = get_bot_state()
        if not state.get("welcome_enabled", False):
            return

        user_id = event.from_user.id
        try:
            # Получаем лидера для "ВАУ" эффекта
            top_players = await get_top_players(limit=1)
            leader_name = "Никто"
            leader_score = 0
            if top_players:
                leader_id, leader_score = top_players[0]
                leader_name = await get_cached_user_name(leader_id)

            # Формируем текст (из конфига)
            welcome_text = f"{config.MSG_WELCOME_TITLE}\n\n{config.MSG_WELCOME_BODY.format(leader_name=leader_name, leader_score=leader_score)}"

            kb = InlineKeyboardBuilder()
            kb.row(InlineKeyboardButton(text=config.BTN_WELCOME_START, url=f"https://t.me/{config.CHANNEL_ID.replace('@', '')}", style="success"))

            # Отправляем в личку с эффектом (салют)
            firework_effect = config.WELCOME_FIREWORK_EFFECT
            welcome_img = config.WELCOME_IMAGE_PATH
            
            if os.path.exists(welcome_img):
                await bot.send_photo(
                    user_id, 
                    FSInputFile(welcome_img), 
                    caption=welcome_text, 
                    reply_markup=kb.as_markup(),
                    message_effect_id=firework_effect,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    user_id, 
                    welcome_text, 
                    reply_markup=kb.as_markup(),
                    message_effect_id=firework_effect,
                    parse_mode="HTML"
                )
            logger.info(f"Приветствие отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки приветствия {user_id}: {e}")

    # 2. ОБРАБОТКА ОТПИСКИ (Удаление из БД)
    elif event.new_chat_member.status in ["left", "kicked"]:
        user_id = event.from_user.id
        try:
            # Удаляем пользователя и все его данные
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,), commit=True)
            await db.execute("DELETE FROM user_answers WHERE user_id = ?", (user_id,), commit=True)
            await db.execute("DELETE FROM greeted_users WHERE user_id = ?", (user_id,), commit=True)
            
            if user_id in USER_CACHE: del USER_CACHE[user_id]
            if user_id in USER_INFO_CACHE: del USER_INFO_CACHE[user_id]
            
            logger.info(f"Пользователь {user_id} отписался и был удален из базы.")
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя {user_id} при отписке: {e}")

# --- ADMIN PANEL ---

async def notify_admin(text):
    try:
        await bot.send_message(config.ADMIN_ID, text)
    except Exception as e:
        print(f"Admin notification failed: {e}")

@dp.message(F.text == "/ping")
async def cmd_ping(m: types.Message):
    await m.answer(f"🏓 Понг! Бот работает. Текущее время (МСК): {get_now().strftime('%H:%M:%S')}")

@dp.message(F.text == "/start")
async def cmd_start(m: types.Message):
    if m.from_user.id == config.ADMIN_ID:
        kb = ReplyKeyboardBuilder()
        kb.row(
            types.KeyboardButton(text="📝 СЛОВО"),
            types.KeyboardButton(text="🧩 ВИКТОРИНА"),
            types.KeyboardButton(text="📊 Статистика")
        )
        kb.row(
            types.KeyboardButton(text="📄 Логи"),
            types.KeyboardButton(text="🧪 Тест: ПРИВЕТСТВИЕ"),
            types.KeyboardButton(text="📥 Бекап БД")
        )
        kb.row(
            types.KeyboardButton(text="🏆 ТОП-5"),
            types.KeyboardButton(text="🌤️ ВЫХОДНЫЕ")
        )
        await m.answer("Панель управления (VDS Ready) 🚀", reply_markup=kb.as_markup(resize_keyboard=True))
    else:
        # Приветствие для новых
        await m.answer("Привет! Я бот для изучения корейского языка. Подпишись на наш канал, чтобы начать!")

# --- ADMIN HANDLERS ---

@dp.callback_query(F.data == "publish_preview")
async def handle_publish_preview(c: types.CallbackQuery):
    admin_id = c.from_user.id
    if admin_id not in ADMIN_PREVIEWS:
        return await c.answer("❌ Данные для публикации не найдены. Попробуйте сгенерировать заново.", show_alert=True)
    
    data = ADMIN_PREVIEWS[admin_id]
    await send_new_post(data)
    
    # Удаляем из превью после публикации
    del ADMIN_PREVIEWS[admin_id]
    
    await c.answer("✅ Опубликовано в канале!", show_alert=True)
    try:
        await c.message.delete()
    except:
        pass

@dp.callback_query(F.data.in_({"approve_welcome", "decline_welcome"}))
async def handle_welcome_preview_btns(c: types.CallbackQuery):
    if c.data == "approve_welcome":
        await c.answer("✅ Превью закрыто (Одобрено)", show_alert=True)
    else:
        await c.answer("❌ Превью закрыто (Отклонено)", show_alert=True)
    try:
        await c.message.delete()
    except:
        pass

@dp.message(F.from_user.id == config.ADMIN_ID)
async def handle_admin_commands(m: types.Message):
    try:
        # --- ГЕНЕРАЦИЯ ПРЕДПРОСМОТРА ---
        if m.text == "📝 СЛОВО":
            data = await get_quiz_data()
            while data.get('is_quiz'):
                data = await get_quiz_data()
            
            ADMIN_PREVIEWS[m.from_user.id] = data
            await send_new_post(data, chat_id=m.chat.id, is_preview=True)
            logger.info(f"Админ {m.from_user.id} запросил превью слова.")

        elif m.text == "🧩 ВИКТОРИНА":
            data = await get_next_quiz_fact()
            if data:
                ADMIN_PREVIEWS[m.from_user.id] = data
                await send_new_post(data, chat_id=m.chat.id, is_preview=True)
                logger.info(f"Админ {m.from_user.id} запросил превью викторины.")

        elif m.text == "🏆 ТОП-5":
            await send_weekly_report(chat_id=m.chat.id, add_publish_button=True)
            await m.answer("Превью ТОП-5 отправлено. Нажми '🚀 ОПУБЛИКОВАТЬ' чтобы опубликовать в канал.")

        elif m.text == "🌤️ ВЫХОДНЫЕ":
            await send_weekend_promo(chat_id=m.chat.id, add_publish_button=True)
            await m.answer("Превью промо выходных отправлено. Нажми '🚀 ОПУБЛИКОВАТЬ' чтобы опубликовать в канал.")

        elif m.text == "🧪 Тест: ПРИВЕТСТВИЕ":
            # Имитируем событие для админа
            try:
                top_players = await get_top_players(limit=1)
                leader_name = "Никто"
                leader_score = 0
                if top_players:
                    leader_id, leader_score = top_players[0]
                    leader_name = await get_cached_user_name(leader_id)

                welcome_text = f"<b>[ТЕСТ]</b> {config.MSG_WELCOME_TITLE}\n\n{config.MSG_WELCOME_BODY.format(leader_name=leader_name, leader_score=leader_score)}"

                kb = InlineKeyboardBuilder()
                kb.row(InlineKeyboardButton(text=config.BTN_WELCOME_START, url=f"https://t.me/{config.CHANNEL_ID.replace('@', '')}", style="success"))
                kb.row(
                    InlineKeyboardButton(text="✅ Одобрить", callback_data="approve_welcome", style="success"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data="decline_welcome", style="danger")
                )

                firework_effect = config.WELCOME_FIREWORK_EFFECT
                welcome_img = config.WELCOME_IMAGE_PATH
                
                if os.path.exists(welcome_img):
                    await bot.send_photo(
                        m.from_user.id, 
                        FSInputFile(welcome_img), 
                        caption=welcome_text, 
                        reply_markup=kb.as_markup(),
                        message_effect_id=firework_effect,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        m.from_user.id, 
                        welcome_text, 
                        reply_markup=kb.as_markup(),
                        message_effect_id=firework_effect,
                        parse_mode="HTML"
                    )
            except Exception as e:
                await m.answer(f"❌ Ошибка теста приветствия: {e}")

        # --- УДАЛЕННЫЙ КОНТРОЛЬ ---
        elif m.text == "📊 Статистика":
            users_count = await db.execute("SELECT COUNT(*) FROM users")
            answers_count = await db.execute("SELECT COUNT(*) FROM user_answers")
            
            stats_text = (
                f"📊 СТАТИСТИКА БОТА\n"
                f"━━━━━━━━━━━━━━\n"
                f"👥 Всего пользователей: {users_count[0][0]}\n"
                f"📝 Всего ответов: {answers_count[0][0]}\n"
                f"🕒 Время сервера: {get_now().strftime('%H:%M:%S')}\n"
            )
            await m.answer(stats_text)

        elif m.text == "📄 Логи":
            if os.path.exists("bot.log"):
                # Читаем последние 20 строк
                with open("bot.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    last_lines = "".join(lines[-20:])
                
                if last_lines:
                    await m.answer(f"📄 ПОСЛЕДНИЕ ЛОГИ:\n\n<pre>{last_lines}</pre>", parse_mode="HTML")
                else:
                    await m.answer("Лог-файл пуст.")
            else:
                await m.answer("❌ Файл логов bot.log не найден.")

        elif m.text == "📥 Бекап БД":
            db_path = os.path.abspath('gamification.db')
            if os.path.exists(db_path):
                await bot.send_document(config.ADMIN_ID, FSInputFile(db_path), caption="📥 Вот резервная копия базы данных.")
                logger.info(f"Админ {m.from_user.id} скачал бэкап БД.")
            else:
                await notify_admin("❌ Файл gamification.db не найден!")

    except Exception as e:
        error_text = f"Критическая ошибка в админ-панели: {e}"
        logger.error(error_text)
        await notify_admin(error_text)

if __name__ == "__main__":
    if sys.platform == 'win32': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
