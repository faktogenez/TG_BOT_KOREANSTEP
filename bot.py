import logging
import gspread
import datetime
import pytz
import os
import logging
from os.path import join, exists
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, CallbackContext
from telegram.constants import ParseMode
from config import BOT_TOKEN, ADMIN_ID, SHEET_URL, COURSE_LINK, PAYMENT_DETAILS, CONTACT_USERNAME, COURSE_PRICE, get_payment_message, MESSAGES

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Глобальные переменные и функции для работы с Google Sheets ---
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(join(os.getcwd(), 'credentials.json'), scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
except Exception as e:
    logger.error(f"Ошибка при подключении к Google Sheets: {e}")
    sheet = None

# --- Обработчики команд ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и предлагает варианты оплаты."""

        
    if update.callback_query:
        user = update.callback_query.from_user
    else:
        user = update.effective_user
        
    try:
        if exists(join(os.getcwd(), 'welcome.png')):
            if update.callback_query:
                await update.callback_query.message.reply_photo(photo=InputFile(join(os.getcwd(), 'welcome.png')))
            else:
                await update.message.reply_photo(photo=InputFile(join(os.getcwd(), 'welcome.png')))
        elif exists(join(os.getcwd(), 'welcome.jpg')):
            if update.callback_query:
                await update.callback_query.message.reply_photo(photo=InputFile(join(os.getcwd(), 'welcome.jpg')))
            else:
                await update.message.reply_photo(photo=InputFile(join(os.getcwd(), 'welcome.jpg')))
        elif exists(join(os.getcwd(), 'welcome.mp4')):
            if update.callback_query:
                await update.callback_query.message.reply_video(video=InputFile(join(os.getcwd(), 'welcome.mp4')))
            else:
                await update.message.reply_video(video=InputFile(join(os.getcwd(), 'welcome.mp4')))
    except Exception as e:
        logger.error(f"Ошибка при отправке медиа: {e}")

    payment_buttons = [
        [InlineKeyboardButton("💳 Купить полный курс", callback_data='purchase')],
        [InlineKeyboardButton("📚 Посмотреть бесплатный урок", url=COURSE_LINK)],
        [InlineKeyboardButton("❓ Задать вопрос", url=f"https://t.me/{CONTACT_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(payment_buttons)
    
    welcome_message = MESSAGES['welcome_message']['caption']
    welcome_options = MESSAGES['welcome_message']['options']

    if update.callback_query:
        await update.callback_query.edit_message_text(text=welcome_message, reply_markup=reply_markup, **welcome_options)
    else:
        await update.message.reply_text(text=welcome_message, reply_markup=reply_markup, **welcome_options)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help."""


    help_message = MESSAGES['help_message']['caption']
    help_options = MESSAGES['help_message']['options']
    await update.message.reply_text(text=help_message, **help_options)

# --- Функция отправки напоминания ---
async def send_reminder(context: CallbackContext) -> None:
    """Отправляет напоминание о курсе клиенту, который проявил интерес, но не оплатил."""
    job = context.job
    user_id = job.data
    
    user_info = get_user_info_from_sheet(user_id)
    if user_info and user_info[3] == "Интересуется": # Проверяем, что статус "Интересуется"
        try:
            reminder_text = MESSAGES['reminder_text']['caption']
            reminder_options = MESSAGES['reminder_text']['options']
            
            buttons = [
                [InlineKeyboardButton("💳 Купить полный курс", callback_data='purchase')],
                [InlineKeyboardButton("❓ Задать вопрос", url=f"https://t.me/{CONTACT_USERNAME}")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            
            if exists(join(os.getcwd(), 'reminder_image.jpg')):
                await context.bot.send_photo(chat_id=user_id, photo=InputFile(join(os.getcwd(), 'reminder_image.jpg')), caption=reminder_text, reply_markup=reply_markup, **reminder_options)
            else:
                await context.bot.send_message(chat_id=user_id, text=reminder_text, reply_markup=reply_markup, **reminder_options)
                
            logger.info(f"Отправлено напоминание пользователю {user_id}")
            
        except Exception as e:
            logger.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")

# --- Обработка нажатий на кнопки ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на inline-кнопки."""

        
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data_type = query.data
    
    if data_type == 'purchase':
        if sheet:
            user_exists = True
            try:
                sheet.find(str(user.id))
            except gspread.exceptions.CellNotFound:
                user_exists = False
            
            if not user_exists:
                add_user_to_sheet(user.full_name, user.id, "Интересуется")
                context.job_queue.run_once(send_reminder, datetime.timedelta(hours=24), data=user.id, name=f'reminder_{user.id}')
                
        keyboard = [
            [InlineKeyboardButton("🇷🇺 ЮMoney", callback_data='yoomoney_btn'), InlineKeyboardButton("🇺🇸 VISA", callback_data='visa_btn')],
            [InlineKeyboardButton("🇰🇷 KOREA", callback_data='korean_account_btn'), InlineKeyboardButton("💎 USDT", callback_data='cryptowallet_btn')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = MESSAGES['payment_details_message']['caption'].format(COURSE_PRICE=COURSE_PRICE, PAYMENT_DETAILS=PAYMENT_DETAILS)
        message_options = MESSAGES['payment_details_message']['options']
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, **message_options)
    
    elif data_type in ['yoomoney_btn', 'visa_btn', 'korean_account_btn', 'cryptowallet_btn']:
        payment_type = data_type.replace('_btn', '')
        text, options = get_payment_message(payment_type)
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='purchase')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=text, reply_markup=reply_markup, **options)
        
    elif data_type == 'back_to_menu':
        await start(update, context)

# --- Обработка скриншотов ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает полученные фотографии."""
    user = update.effective_user
    
    # Получаем file_id последней фотографии в сообщении
    if not update.message.photo:
        photo_message = MESSAGES['photo_required']['caption']
        photo_options = MESSAGES['photo_required']['options']
        await update.message.reply_text(text=photo_message, **photo_options)
        return
        
    photo_file_id = update.message.photo[-1].file_id

    # Сначала проверяем, есть ли пользователь в таблице, и добавляем или обновляем его статус
    if sheet:
        user_info = get_user_info_from_sheet(user.id)
        if not user_info:
            add_user_to_sheet(user.full_name, user.id, "На проверке")
        else:
            update_user_status(user.id, "На проверке")

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
        social_links_options = MESSAGES['social_links_text']['options']
        await update.message.reply_text(text=social_links_text, disable_web_page_preview=True, **social_links_options)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает подтверждение оплаты админом."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.data.split('_')[1]
    
    if sheet:
        user_info = get_user_info_from_sheet(user_id)
        if user_info:
             payment_confirmed_message_text = MESSAGES['payment_confirmed_user']['caption'].format(COURSE_LINK=COURSE_LINK)
             payment_confirmed_message_options = MESSAGES['payment_confirmed_user']['options']
             await context.bot.send_message(chat_id=user_id, text=payment_confirmed_message_text, **payment_confirmed_message_options)
             payment_confirmed_admin_message = MESSAGES['payment_confirmed_admin']['caption'].format(user_id=user_id)
             payment_confirmed_admin_options = MESSAGES['payment_confirmed_admin']['options']
             await query.edit_message_caption(caption=payment_confirmed_admin_message, **payment_confirmed_admin_options)
             update_user_status(user_id, "Оплачено")
             remove_job_if_exists(f'reminder_{user_id}', context)
        else:
            user_not_found_admin_message = MESSAGES['user_not_found_admin']['caption'].format(user_id=user_id)
            user_not_found_admin_options = MESSAGES['user_not_found_admin']['options']
            await query.edit_message_caption(caption=user_not_found_admin_message, **user_not_found_admin_options)
    else:
        google_sheets_error_admin_message = MESSAGES['google_sheets_error_admin']['caption']
        google_sheets_error_admin_options = MESSAGES['google_sheets_error_admin']['options']
        await query.edit_message_caption(caption=google_sheets_error_admin_message, **google_sheets_error_admin_options)

async def decline_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает отклонение оплаты админом."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.data.split('_')[1]
    
    payment_declined_message_text = MESSAGES['payment_declined_user']['caption']
    payment_declined_message_options = MESSAGES['payment_declined_user']['options']
    
    keyboard = [
        [InlineKeyboardButton("🛠 Тех.поддержка", url=f"https://t.me/{CONTACT_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(chat_id=user_id, text=payment_declined_message_text, reply_markup=reply_markup, **payment_declined_message_options)

    payment_declined_admin_message = MESSAGES['payment_declined_admin']['caption'].format(user_id=user_id)
    payment_declined_admin_options = MESSAGES['payment_declined_admin']['options']
    await query.edit_message_caption(caption=payment_declined_admin_message, **payment_declined_admin_options)
    if sheet:
        update_user_status(user_id, "Отклонено")

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Удаляет задачу из очереди, если она существует."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    logger.info(f"Задача {name} удалена из очереди.")
    return True

# --- Функции для работы с Google Sheets ---
def add_user_to_sheet(name, user_id, status):
    """Добавляет нового пользователя в таблицу с датой."""
    try:
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        data = [current_time, name, user_id, status]
        sheet.append_row(data)
        logger.info(f"Пользователь {name} добавлен в Google Sheets.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении в Google Sheets: {e}")

def update_user_status(user_id, new_status):
    """Обновляет статус пользователя по его ID."""
    try:
        cell = sheet.find(str(user_id))
        sheet.update_cell(cell.row, 4, new_status)
        logger.info(f"Статус пользователя {user_id} обновлен на {new_status}.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса: {e}")

def get_user_info_from_sheet(user_id):
    """Находит пользователя в таблице по ID и возвращает его данные."""
    cell = sheet.find(str(user_id))
    if cell is None:
        return None  # User not found
    try:
        return sheet.row_values(cell.row)
    except Exception as e:
        logger.error(f"Ошибка при поиске пользователя: {e}")
        return None

# --- Основная функция запуска бота ---
def main() -> None:
    """Запускает бота."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set. Please set it before running the bot.")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(purchase|yoomoney_btn|visa_btn|korean_account_btn|cryptowallet_btn|back_to_menu)$"))
    application.add_handler(CallbackQueryHandler(confirm_payment, pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(decline_payment, pattern="^decline_"))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()