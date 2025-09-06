# bot.py
import logging
import datetime
import pytz
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, InputFile
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, CallbackContext
from telegram.ext import JobQueue
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import BOT_TOKEN, ADMIN_ID, COURSE_LINK, PAYMENT_DETAILS, CONTACT_USERNAME, COURSE_PRICE, MESSAGES, MAIN_MENU_KEYBOARD, REMINDER_INTERVAL_MINUTES, SHEET_URL, REMINDER_IMAGE_PATH, get_payment_message

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Глобальные переменные и функции для работы с Google Sheets ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(BASE_DIR, 'credentials.json'), scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
    logger.info("Подключение к Google Sheets успешно.")
except Exception as e:
    logger.error(f"Ошибка при подключении к Google Sheets: {e}")
    sheet = None

def get_cached_user_status(context, user_id):
    """
    Получает статус пользователя из кэша (user_data) или из таблицы.
    """
    if 'payment_status' in context.user_data:
        return context.user_data['payment_status']
    
    status = get_user_status(user_id)
    if status:
        context.user_data['payment_status'] = status
    return status

def get_user_status(user_id):
    """
    Получает статус пользователя из таблицы Google Sheets по его Telegram ID.
    Возвращает статус или None, если пользователь не найден.
    """
    if not sheet:
        return None
    try:
        cell = sheet.find(str(user_id), in_column=4) # Колонка 4 - "Telegram ID"
        if cell:
            return sheet.cell(cell.row, 5).value # Колонка 5 - "Статус оплаты"
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении статуса пользователя {user_id}: {e}")
        return None

def update_user_status_and_cache(context, user_id, user_name, status):
    """
    Обновляет статус пользователя в таблице и в кэше.
    """
    context.user_data['payment_status'] = status
    add_or_update_user_status(user_id, user_name, status)

def add_or_update_user_status(user_id, user_name, status):
    """
    Добавляет пользователя в таблицу или обновляет его статус, если он уже существует.
    """
    if not sheet:
        logger.error("Невозможно обновить таблицу, так как подключение не установлено.")
        return

    try:
        current_time_korea = datetime.datetime.now(pytz.timezone('Asia/Seoul')).strftime("%d.%m.%Y %H:%M:%S")

        # Ищем пользователя по ID в колонке "Telegram ID" (колонка 4)
        cell = sheet.find(str(user_id), in_column=4)

        if cell:
            # Пользователь найден, обновляем "Дату" и "Статус"
            row_index = cell.row
            sheet.update_cell(row_index, 2, current_time_korea) # Колонка 2: Дата
            sheet.update_cell(row_index, 5, status) # Колонка 5: Статус оплаты
            logger.info(f"Статус и дата пользователя {user_name} ({user_id}) обновлены на '{status}'.")
        else:
            # Пользователь не найден, добавляем новую строку
            next_row_number = len(sheet.get_all_records()) + 1
            new_row = [
                next_row_number,
                current_time_korea,
                user_name,
                user_id,
                status
            ]
            sheet.append_row(new_row)
            logger.info(f"Новый пользователь {user_name} ({user_id}) добавлен в таблицу со статусом '{status}'.")

    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API при работе с Google Sheets: {e}")
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка при добавлении/обновлении пользователя: {e}")


async def setup_bot_commands(application) -> None:
    """Устанавливает команды бота для отображения в меню."""
    commands = [
        BotCommand("start", "🚀 ГЛАВНОЕ МЕНЮ"),
        BotCommand("buy", "✅ КУПИТЬ КУРС"),
        BotCommand("lesson", "🎁 БЕСПЛАТНЫЙ УРОК"),
        BotCommand("question", "⁉️ ЗАДАТЬ ВОПРОС"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота установлены")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start - главное меню."""
    user = update.effective_user
    update_user_status_and_cache(context, user.id, user.full_name, "Зашел в бота")
    schedule_reminder_if_needed(context, user.id, user.full_name, REMINDER_INTERVAL_MINUTES)

    welcome_message = MESSAGES['welcome_message']['caption'].format(user_first_name=user.first_name)
    welcome_options = MESSAGES['welcome_message']['options']

    keyboard = []
    for text, data, type in MAIN_MENU_KEYBOARD:
        if type == "callback_data":
            keyboard.append([InlineKeyboardButton(text, callback_data=data)])
        elif type == "url":
            if data == "lesson":
                keyboard.append([InlineKeyboardButton(text, url=COURSE_LINK)])
            elif data == "question":
                keyboard.append([InlineKeyboardButton(text, url=f"https://t.me/{CONTACT_USERNAME}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=welcome_message,
                reply_markup=reply_markup,
                **welcome_options
            )
        except Exception:
            # If editing fails (e.g., message is a photo), send a new message
            await update.callback_query.message.reply_text(
                text=welcome_message,
                reply_markup=reply_markup,
                **welcome_options
            )
    else:
        await update.message.reply_text(
            text=welcome_message,
            reply_markup=reply_markup,
            **welcome_options
        )


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /buy - покупка курса."""
    user = update.effective_user
    update_user_status_and_cache(context, user.id, user.full_name, "Смотрел цены")
    schedule_reminder_if_needed(context, user.id, user.full_name, REMINDER_INTERVAL_MINUTES)

    keyboard = [
        [InlineKeyboardButton("🇷🇺 ЮMoney", callback_data='yoomoney_btn'), InlineKeyboardButton("🇺🇸 VISA", callback_data='visa_btn')],
        [InlineKeyboardButton("🇰🇷 KOREA", callback_data='korean_account_btn'), InlineKeyboardButton("💎 USDT", callback_data='cryptowallet_btn')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = MESSAGES['payment_details_message']['caption']
    message_options = MESSAGES['payment_details_message']['options']

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup, **message_options)
        except Exception:
            # If editing fails (e.g., message is a photo), send a new message
            await update.callback_query.message.reply_text(text=message_text, reply_markup=reply_markup, **message_options)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup, **message_options)

async def lesson_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /lesson - бесплатный урок."""
    user = update.effective_user
    update_user_status_and_cache(context, user.id, user.full_name, "Смотрел бесплатный урок")
    schedule_reminder_if_needed(context, user.id, user.full_name, REMINDER_INTERVAL_MINUTES)

    lesson_message = (
        "📚 <b>Бесплатный урок корейского языка!</b>\n\n"
        "Посмотрите наш бесплатный урок и познакомьтесь с курсом:\n\n"
        f"🔗 <a href='{COURSE_LINK}'>Перейти к уроку</a>\n\n"
        "После просмотра вы можете приобрести полный курс! 🇰🇷"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Купить полный курс", callback_data='purchase')],
        [InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=lesson_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception:
            # If editing fails (e.g., message is a photo), send a new message
            await update.callback_query.message.reply_text(text=lesson_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text=lesson_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def question_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /question - задать вопрос."""
    question_message = (
        "❓ <b>Задать вопрос</b>\n\n"
        "У вас есть вопросы о курсе или оплате?\n\n"
        "💬 Напишите нам лично и мы обязательно ответим!\n\n"
        f"🔗 <a href='https://t.me/{CONTACT_USERNAME}'>Написать в личку</a>"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Купить курс", callback_data='purchase')],
        [InlineKeyboardButton("🔙 Главное меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=question_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except Exception:
            # If editing fails (e.g., message is a photo), send a new message
            await update.callback_query.message.reply_text(text=question_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await update.message.reply_text(text=question_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def handle_any_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает любое текстовое сообщение и показывает главное меню."""
    await start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help."""
    help_message = MESSAGES['help_message']['caption']
    help_options = MESSAGES['help_message']['options']
    await update.message.reply_text(text=help_message, **help_options)

def schedule_reminder_if_needed(context: ContextTypes.DEFAULT_TYPE, user_id, user_name, delay_minutes: int) -> None:
    """Проверяет статус пользователя и планирует напоминание, если оно необходимо."""
    status = get_cached_user_status(context, user_id)
    if status == "Оплачено":
        logger.info(f"Пользователь {user_name} ({user_id}) уже оплатил курс. Напоминание не будет запланировано.")
        return

    job_name = f"reminder_{user_id}"
    # Отменяем предыдущее напоминание, если оно есть
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()

    context.job_queue.run_once(
        send_reminder,
        datetime.timedelta(minutes=delay_minutes),
        chat_id=user_id,
        name=job_name
    )
    logger.info(f"Напоминание для пользователя {user_name} ({user_id}) запланировано на {delay_minutes} минут.")

async def send_reminder(context: CallbackContext) -> None:
    """Отправляет напоминание пользователю с картинкой и текстом."""
    job = context.job
    try:
        reminder_text = MESSAGES['reminder_text']['caption']
        reminder_options = MESSAGES['reminder_text']['options']

        keyboard = [
            [InlineKeyboardButton("💳 КУПИТЬ КУРС", callback_data='purchase')],
            [InlineKeyboardButton("⁉️ ЗАДАТЬ ВОПРОС", url=f"https://t.me/{CONTACT_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        image_path = os.path.join(BASE_DIR, REMINDER_IMAGE_PATH)

        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo_file:
                await context.bot.send_photo(
                    chat_id=job.chat_id,
                    photo=InputFile(photo_file),
                    caption=reminder_text,
                    reply_markup=reply_markup,
                    **reminder_options
                )
            logger.info(f"Напоминание с картинкой отправлено пользователю с ID {job.chat_id}")
        else:
            await context.bot.send_message(
                chat_id=job.chat_id,
                text=reminder_text,
                reply_markup=reply_markup,
                **reminder_options
            )
            logger.warning(f"Файл изображения не найден по пути: {image_path}. Отправлено только текстовое напоминание.")

    except Exception as e:
        logger.error(f"Не удалось отправить напоминание пользователю с ID {job.chat_id}: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на inline-кнопки."""
    query = update.callback_query
    await query.answer()

    data_type = query.data

    if data_type == 'purchase':
        await buy_command(update, context)

    elif data_type == 'lesson':
        await lesson_command(update, context)

    elif data_type in ['yoomoney_btn', 'visa_btn', 'korean_account_btn', 'cryptowallet_btn']:
        payment_type = data_type.replace('_btn', '')
        text, options = get_payment_message(payment_type)

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='purchase')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup, **options)
        except Exception:
            # If editing fails (e.g., message is a photo), send a new message
            await query.message.reply_text(text=text, reply_markup=reply_markup, **options)

    elif data_type == 'back_to_menu':
        await start(update, context)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает полученные фотографии."""
    user = update.effective_user

    if not update.message.photo:
        photo_message = MESSAGES['photo_required']['caption']
        photo_options = MESSAGES['photo_required']['options']
        await update.message.reply_text(text=photo_message, **photo_options)
        return

    photo_file_id = update.message.photo[-1].file_id

    update_user_status_and_cache(context, user.id, user.full_name, "Ожидает подтверждения")

    context.user_data['payment_user_id'] = user.id

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    korea_tz = pytz.timezone('Asia/Seoul')
    korea_time = datetime.datetime.now(korea_tz)
    date_str = korea_time.strftime("%d.%m.%Y %H:%M:%S")

    caption_text = (
        f"🥳 <b>Новый скриншот оплаты от пользователя!</b>\n\n"
        f"👤 <b>Имя:</b> {user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"⏰ <b>Дата и время (Корея):</b> {date_str}\n\n"
        f"✅ Подтвердить оплату?"
    )

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id,
                                 caption=caption_text,
                                 parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    if 0 <= korea_time.hour < 7:
        night_message = MESSAGES['night_check_message']['caption']
        night_options = MESSAGES['night_check_message']['options']
        await update.message.reply_text(text=night_message, **night_options)
    else:
        social_links_text = MESSAGES['social_links_text']['caption']
        social_links_options = MESSAGES['social_links_options']['options']
        await update.message.reply_text(text=social_links_text, **social_links_options)


async def handle_document_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает полученные документы."""
    document_message = MESSAGES['document_not_supported']['caption']
    document_options = MESSAGES['document_not_supported']['options']
    await update.message.reply_text(text=document_message, **document_options)


async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение оплаты админом."""
    query = update.callback_query
    await query.answer()

    user_id_to_confirm = query.data.split('_')[1]

    if str(query.from_user.id) != str(ADMIN_ID):
        await query.answer("У вас нет прав для этого действия.")
        return

    try:
        # Отменяем напоминание для пользователя
        job_name = f"reminder_{user_id_to_confirm}"
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
            logger.info(f"Напоминание для пользователя {user_id_to_confirm} отменено после подтверждения оплаты.")

        payment_confirmed_user_text = MESSAGES['payment_confirmed_user']['caption']
        payment_confirmed_user_options = MESSAGES['payment_confirmed_user']['options']
        await context.bot.send_message(chat_id=user_id_to_confirm, text=payment_confirmed_user_text, **payment_confirmed_user_options)

        user = await context.bot.get_chat(user_id_to_confirm)
        update_user_status_and_cache(context, user_id_to_confirm, user.full_name, "Оплачено")

        payment_confirmed_admin_message = MESSAGES['payment_confirmed_admin']['caption'].format(user_id=user_id_to_confirm)
        payment_confirmed_admin_options = MESSAGES['payment_confirmed_admin']['options']
        await query.edit_message_caption(caption=payment_confirmed_admin_message, **payment_confirmed_admin_options)

    except Exception as e:
        logger.error(f"Failed to confirm payment for user {user_id_to_confirm}: {e}")
        await query.edit_message_caption("Произошла ошибка при подтверждении.")


async def decline_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает отклонение оплаты админом."""
    query = update.callback_query
    await query.answer()

    user_id_to_decline = query.data.split('_')[1]

    if str(query.from_user.id) != str(ADMIN_ID):
        await query.answer("У вас нет прав для этого действия.")
        return

    try:
        payment_declined_user_text = MESSAGES['payment_declined_user']['caption']
        payment_declined_user_options = MESSAGES['payment_declined_user']['options']

        keyboard = [
            [InlineKeyboardButton("🛠 Тех.поддержка", url=f"https://t.me/{CONTACT_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=user_id_to_decline, text=payment_declined_user_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML, **payment_declined_user_options)

        payment_declined_admin_message = MESSAGES['payment_declined_admin']['caption'].format(user_id=user_id_to_decline)
        payment_declined_admin_options = MESSAGES['payment_declined_admin']['options']
        await query.edit_message_caption(caption=payment_declined_admin_message, **payment_declined_admin_options)

    except Exception as e:
        logger.error(f"Failed to decline payment for user {user_id_to_decline}: {e}")
        await query.edit_message_caption("Произошла ошибка при отклонении.")

def main() -> None:
    """Запускает бота."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set. Please set it before running the bot.")

    application = Application.builder().token(BOT_TOKEN).job_queue(JobQueue()).build()

    application.post_init = post_init

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("lesson", lesson_command))
    application.add_handler(CommandHandler("question", question_command))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(purchase|lesson|yoomoney_btn|visa_btn|korean_account_btn|cryptowallet_btn|back_to_menu)$"))
    application.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(decline_payment, pattern="^decline_"))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO & ~filters.COMMAND, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_text))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def post_init(application):
    """Вызывается после инициализации приложения."""
    await application.bot.delete_webhook()
    await setup_bot_commands(application)

if __name__ == '__main__':
    main()