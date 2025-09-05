# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
SHEET_URL = os.getenv('SHEET_URL')
COURSE_LINK = os.getenv('COURSE_LINK')
CONTACT_USERNAME = os.getenv('CONTACT_USERNAME')

# Стоимость курса в разных валютах
COURSE_PRICE = {
    'RUB': 990,
    'USD': 12,
    'KRW': 17000,
    'USDT': 12
}

# Общие инструкции по оплате
PAYMENT_INSTRUCTIONS_HTML = (
    "\n\n*Реквизиты копируются при нажатии\n"
    "✅ После оплаты пришлите чек (скриншот).\n\n"
    "Нажмите на <b>📎СКРЕПКУ</b>, выберите фото чека и отправьте его мне на проверку."
)

# Реквизиты и тексты для оплаты
PAYMENT_DETAILS = {
    'yoomoney': {
        'amount': {'currency': 'RUB', 'value': COURSE_PRICE['RUB']},
        'text': (
            "<b>Ю-Money</b>\n<code>4100118514656098</code>\n\n"
            "<b>Карта МИР от Ю-Money</b>\n<code>5599002056140298</code>\n"
            "<code>2204120115246189</code>\n\n"
            "<blockquote>Оплатить в приложении «СберБанк Онлайн»:\n"
            "1. Перейдите в «Платежи и переводы» → «Перевод на счет в ЮMoney».\n"
            "2. Введите кошелек <code>4100118514656098</code> и сумму — <b>{value} {currency}</b>.\n\n"
            "С Тинькофф → на карту МИР <code>5599002056140298</code>, сумма — <b>{value} {currency}</b>.</blockquote>" +
            PAYMENT_INSTRUCTIONS_HTML
        ),
        'caption': "",
        'options': {'parse_mode': 'HTML'}
    },
    'visa': {
        'amount': {'currency': 'USD', 'value': COURSE_PRICE['USD']},
        'text': (
            "<b>💳 Оплата картой VISA</b>\n\n"
            "Сумма: <b>{value} {currency}</b>\n\n"
            "Номер карты: <code>4023060247740425</code>\n\n"
            "<blockquote>Просто переведите указанную сумму на карту.</blockquote>" +
            PAYMENT_INSTRUCTIONS_HTML
        ),
        'caption': "",
        'options': {'parse_mode': 'HTML'}
    },
    'korean_account': {
        'amount': {'currency': 'KRW', 'value': COURSE_PRICE['KRW']},
        'text': (
            "<b>🇰🇷 Корейский счет</b>\n\n"
            "Сумма: <b>{value} {currency}</b>\n\n"
            "신협 <code>132-142-428707</code> Shirokovskiy Vladimir\n\n"
            "하나은행 <code>398-910474-45307</code> Li Elena\n\n"
            "<blockquote>Переводы возможны только внутри Кореи.</blockquote>" +
            PAYMENT_INSTRUCTIONS_HTML
        ),
        'caption': "",
        'options': {'parse_mode': 'HTML'}
    },
    'cryptowallet': {
        'amount': {'currency': 'USDT', 'value': COURSE_PRICE['USDT']},
        'text': (
            "<b>💰 Криптовалютный кошелек</b>\n\n"
            "Сумма: <b>{value} {currency}</b>\n\n"
            "<b>BTC</b>\n<code>1D6QvTNuPTn1YkxUgc5GiznkAhckxBagAU</code>\n\n"
            "<b>TON</b>\n<code>UQACtkYM9GI1jyrr39ixKoKMitZdEEK_UYVWKdc4UxU30LAr</code>\n\n"
            "<b>USDT (TRC20)</b>\n<code>TYFL58AnHjeWzKpmZAN6nak7NEX35KWZE2</code>\n\n"
            "<blockquote>⚠️ Проверьте адрес и сеть. Комиссия зависит от блока.</blockquote>" +
            PAYMENT_INSTRUCTIONS_HTML
        ),
        'caption': "",
        'options': {'parse_mode': 'HTML'}
    }
}

# HTML для социальных ссылок (используется в нескольких местах)
SOCIAL_LINKS_HTML = (
    "НАШИ СОЦ СЕТИ: 👇 \n"
    " \n"
    "🎬 <a href='https://www.tiktok.com/@korean.step_by'>TikTok</a> | 🌐 <a href='https://vk.com/korean_step_by_step'>VK</a> | 📸 <a href='https://www.instagram.com/korean_stepbystep/'>Instagram</a> \n"
    "ᅠ ᅠ"
)

# Путь к изображению для напоминаний
REMINDER_IMAGE_PATH = 'reminder_image.jpg'

# Интервал напоминания (в минутах)
REMINDER_INTERVAL_MINUTES = 1

# Сообщения бота
MESSAGES = {
    'welcome_message': {
        'caption': (
            "<b>🇰🇷 Добро пожаловать в мир Корейского языка!</b>\n\n"
            "Я помогу вам освоить Корейский алфавит всего за один день "
            "и научиться ✍️ писать свое имя по-корейски! \n\n"
            "Наш курс <b>«Хангыль за 1 день»</b> — это:\n\n"
            "• 3 видеоурока с нуля до уверенного чтения\n"
            "• PDF-прописи, карточки и тесты\n"
            "• Навык на всю жизнь!\n\n"
            "Наша команда всегда на связи! Если нужна помощь с оплатой или выбором — просто напишите нам 😊\n\n"
            "<b>👇 Выберите действие:</b>\n\n"
        ),
        'options': {'parse_mode': 'HTML'}
    },
    'help_message': {
        'caption': "Я могу помочь вам оплатить курс. Пожалуйста, начните с команды /start.",
        'options': {'parse_mode': 'HTML'}
    },
    'reminder_text': {
        'caption': (
            "Здравствуйте! 👋 Мы заметили, что Вам был интересен наш курс <b>«Хангыль за 1 день»</b>. "
            "Возможно, у Вас остались вопросы? Будем рады помочь и всё подробно рассказать! 😊\n\n"
            "Не упустите возможность выучить корейский алфавит всего за один день 🇰🇷✨\n\n"
            "👇 Если будете готовы начать, пожалуйста, нажмите на кнопку ниже."
        ),
        'options': {'parse_mode': 'HTML'}
    },
    'purchase_message': {
        'caption': (
            f"<b>💳 Стоимость курса:</b>\n\n"
            f"🇷🇺 {COURSE_PRICE['RUB']} RUB\n"
            f"🇺🇸 {COURSE_PRICE['USD']} USD\n"
            f"🇰🇷 {COURSE_PRICE['KRW']} KRW\n\n"
            f"Выберите удобный способ оплаты: 👇\n"
        ),
        'options': {'parse_mode': 'HTML'}
    },
    'photo_required': {
        'caption': "⛔️ Пожалуйста, отправьте, пожалуйста, именно <b>фотографию чека оплаты</b>.",
        'options': {'parse_mode': 'HTML'}
    },
    'new_screenshot_admin_caption': {
        'caption': (
            f"🥳 <b>Новый скриншот оплаты от пользователя!</b>\n\n"
            f"👤 <b>Имя:</b> {{user_full_name}}\n"
            f"🆔 <b>ID:</b> <code>{{user_id}}</code>\n"
            f"⏰ <b>Дата и время (Корея):</b> {{date_str}}\n\n"
            f"✅ Подтвердить оплату?"
        ),
        'options': {'parse_mode': 'HTML'}
    },
    'social_links_text': {
        'caption': (
            "ᅠ ᅠ \n"
            "🥰 <b>Спасибо!</b> \n"
            " \n"
            "Скриншот оплаты отправлен на <b>проверку</b>.  \n"
            "Мы сообщим вам, как только оплата будет подтверждена <i>(до 30 минут).</i> \n"
            " \n"
            "❤️ <b>Благодарим за понимание!</b> \n\n"
            + SOCIAL_LINKS_HTML
        ),
        'options': {'parse_mode': 'HTML', 'disable_web_page_preview': True}
    },
    'night_check_message': {
        'caption': (
            "ᅠ ᅠ \n"
            "🌙 <b>Сейчас в Корее ночь.</b> \n"
            "Но не волнуйтесь, ваш запрос в очереди. \n"
            "Мы обязательно ответим вам утром по корейскому времени! \n\n"
            "❤️ <b>Благодарим за понимание!</b> \n"
            " \n"
            + SOCIAL_LINKS_HTML
        ),
        'options': {'parse_mode': 'HTML', 'disable_web_page_preview': True}
    },
    'payment_confirmed_user': {
        'caption': (
            "<b>✅ Ваша оплата подтверждена.</b>\n\n"
            "Вот ссылка на курс:\n"
            f"{COURSE_LINK}\n\n"
            "<b>Спасибо за покупку! 🥰</b>"
        ),
        'options': {'parse_mode': 'HTML'}
    },
    'payment_confirmed_admin': {
        'caption': f"✅ Оплата подтверждена для пользователя с ID: <code>{{user_id}}</code>",
        'options': {'parse_mode': 'HTML'}
    },
    'user_not_found_admin': {
        'caption': f"❌ Не удалось найти пользователя с ID: <code>{{user_id}}</code> в таблице.",
        'options': {'parse_mode': 'HTML'}
    },
    'google_sheets_error_admin': {
        'caption': "❌ Ошибка: Не удалось подключиться к Google Sheets.",
        'options': {'parse_mode': 'HTML'}
    },
    'payment_declined_user': {
        'caption': (
            "<b>❌ К сожалению, ваше фото ОПЛАТЫ не одобрено.</b>\n\n"
            "Пожалуйста, убедитесь, что вы правильно выбрали фото, и <b>отправьте его ещё раз</b>\n\n"
            "Скриншоты проверяются человеком!\\nСпасибо за понимание!\\n\\n"
            "<b>⚠️ Внимание:</b>\\n"
            "Если у вас есть вопросы, пожалуйста, свяжитесь с нами, нажав кнопку ниже 👇.\\n\\n"
        ),
        'options': {'parse_mode': 'HTML'}
    },
    'payment_declined_admin': {
        'caption': f"❌ Оплата отклонена для пользователя с ID: <code>{{user_id}}</code>",
        'options': {'parse_mode': 'HTML'}
    },
    'payment_details_message': {
        'caption': (
            "<b>Цена: </b> \n \n"
            f"🇷🇺 ЮMoney - <b>{COURSE_PRICE['RUB']}</b> rub \n🇺🇸 VISA - <b>{COURSE_PRICE['USD']}</b> usd \n"
            f"🇰🇷 KOREA - <b>{COURSE_PRICE['KRW']}</b> krw \n💎 USDT - <b>{COURSE_PRICE['USDT']}</b> usdt \n \n"
            "<i>Выберите способ оплаты:</i> 👇\n\n"
        ),
        'options': {'parse_mode': 'HTML'}
    }
}

MAIN_MENU_KEYBOARD = [
    ("✅ УЗНАТЬ ЦЕНУ", "purchase", "callback_data"),
    ("🎁 БЕСПЛАТНЫЙ УРОК", "lesson", "url"),
    ("⁉️ ЗАДАТЬ ВОПРОС", "question", "url")
]

def get_payment_message(method: str):
    details = PAYMENT_DETAILS.get(method)
    if not details:
        return "Метод оплаты не найден", {}

    text = details['text'].format(
        value=details['amount']['value'],
        currency=details['amount']['currency']
    )
    options = details.get('options', {})
    return text, options