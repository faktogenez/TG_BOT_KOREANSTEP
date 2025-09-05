# config.py

BOT_TOKEN = '8150212382:AAHdmMEGdgPJYdWKb2gbIB6Wxoo8WHgYQW0'
ADMIN_ID = '468021908'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1AhlV6Ftgu2jdYvRJRNbrKFwy34JWFA4MVJoRLi-CSkk/edit?gid=0#gid=0'
COURSE_LINK = 'https://t.me/+4EUrEaG8NsE2NzUy'
CONTACT_USERNAME = 'bodaYan'

# Стоимость курса в разных валютах
COURSE_PRICE = {
    'RUB': 990,
    'USD': 12,
    'KRW': 17000,
    'USDT': 12
}

# Реквизиты и тексты для оплаты
PAYMENT_DETAILS = {
    'yoomoney': {
        'amount': {'currency': 'RUB', 'value': COURSE_PRICE['RUB']},
        'text': (
            "<b>💳 Оплата ЮMoney</b>\n\n"
            "Сумма: <b>{value} {currency}</b>\n\n"
            "<b>Ю-Money</b>\n<code>4100118514656098</code>\n\n"
            "<b>Карта МИР от Ю-Money</b>\n<code>5599002056140298</code>\n"
            "<code>2204120115246189</code>\n\n"
            "<blockquote>Оплатить в приложении «СберБанк Онлайн»:\n"
            "1. Перейдите в «Платежи и переводы» → «Перевод на счет в ЮMoney».\n"
            "2. Введите кошелек <code>4100118514656098</code> и сумму — <b>{value} {currency}</b>.\n\n"
            "С Тинькофф → на карту МИР <code>5599002056140298</code>, сумма — <b>{value} {currency}</b>.</blockquote>\n\n"
            "*Реквизиты копируются при нажатии\n"
            "✅ После оплаты отправте чек (скриншот).\n\n"
            "Нажмите на <b>📎СКРЕПКУ</b>, выберите фото чека и отправьте его мне на проверку."
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
            "<blockquote>Просто переведите указанную сумму на карту.</blockquote>"
            "\n\n*Реквизиты копируются при нажатии\n"
            "✅ После оплаты пришлите чек (скриншот).\n\n"
            "Нажмите на <b>📎СКРЕПКУ</b>, выберите фото чека и отправьте его мне на проверку."
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
            "<blockquote>Переводы возможны только внутри Кореи.</blockquote>"
            "\n\n*Реквизиты копируются при нажатии\n"
            "✅ После оплаты пришлите чек (скриншот).\n\n"
            "Нажмите на <b>📎СКРЕПКУ</b>, выберите фото чека и отправьте его мне на проверку."
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
            "<blockquote>⚠️ Проверьте адрес и сеть. Комиссия зависит от блока.</blockquote>"
            "\n*Реквизиты копируются при нажатии\n"
            "✅ После оплаты пришлите чек (скриншот).\n\n"
            "Нажмите на <b>📎СКРЕПКУ</b>, выберите фото чека и отправьте его мне на проверку."
        ),
        'caption': "",
        'options': {'parse_mode': 'HTML'}
    }
}

# Сообщения бота
MESSAGES = {
    'welcome_message': {
        'caption': (
            "<b>🇰🇷 Добро пожаловать в мир Корейского языка!</b>\n\n"
            "Меня зовут <b>Ханги</b>, и я помогу вам освоить Корейский алфавит всего за один день "
            "и научиться ✍️ писать свое имя по-корейски! \n\n"
            "Наш курс <b>«Хангыль за 1 день»</b> — это:\n"
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
            "Привет! 👋 Заметил, что Вы интересовались нашим курсом <b>«Хангыль за 1 день»</b>. "
            "Может быть, у Вас остались вопросы? Мы всегда готовы помочь! 😊\n\n"
            "Не упустите шанс освоить корейский алфавит всего за один день! 🇰🇷✨\n\n"
            "👇 Готовы начать? Нажмите на кнопку ниже!"
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
        'caption': "Пожалуйста, отправьте, пожалуйста, именно фотографию.",
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
            "🥰 <b>Спасибо!</b>\n\n"
            "Ваш скриншот отправлен на проверку. Я сообщу вам, как только оплата будет подтверждена (до 30 минут).\n\n"
            "⏰ Пока ждете, можете пройти <b>ТЕСТЫ</b> или выучить новые <b>СЛОВА</b> 👇\n\n"

            "<b>🎬 TikTok:</b>\nhttps://www.tiktok.com/@korean.step_by\n\n"
            "<b>🌐 VK:</b>\nhttps://vk.com/korean_step_by_step\n\n"
            "<b>📸 Instagram:</b>\nhttps://www.instagram.com/korean_stepbystep/\n\n"
            "<b>🧵 Threads:</b>\nhttps://www.threads.com/@korean_stepbystep\n\n"
            "<b>▶️ YouTube:</b>\nhttps://www.youtube.com/@Korean.step_by"
        ),
        'options': {'parse_mode': 'HTML', 'disable_web_page_preview': True}
    },
    'night_check_message': {
        'caption': (
            "<b>🌙 Сейчас в Корее ночь и все спят.</b>\n"
            "Но не волнуйтесь, ваш запрос в очереди, и я обязательно проверю его утром.\n"
            "<b>Благодарим вас за терпение!</b>\n\n"

            "⏰ Пока ждете, можете пройти <b>ТЕСТЫ</b> или выучить новые <b>СЛОВА</b> 👇\n\n"

            "<b>🎬 TikTok:</b>\nhttps://www.tiktok.com/@korean.step_by\n\n"
            "<b>🌐 VK:</b>\nhttps://vk.com/korean_step_by_step\n\n"
            "<b>📸 Instagram:</b>\nhttps://www.instagram.com/korean_stepbystep/\n\n"
            "<b>🧵 Threads:</b>\nhttps://www.threads.com/@korean_stepbystep\n\n"
            "<b>▶️ YouTube:</b>\nhttps://www.youtube.com/@Korean.step_by"
        ),
        'options': {'parse_mode': 'HTML'}
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
            "Пожалуйста, убедитесь, что вы правильно выбрали фото, и отправьте его ещё раз.\n\n"
            "Скриншоты проверяются человеком!\nСпасибо за понимание!\n\n"
            "<b>⚠️ Внимание:</b>\n"
            "Если вы оплатили курс, но его не получили, пожалуйста, свяжитесь с нами, нажав кнопку ниже 👇.\n\n"
           

        ),
        'options': {'parse_mode': 'HTML'}
    },
    'payment_declined_admin': {
        'caption': f"❌ Оплата отклонена для пользователя с ID: <code>{{user_id}}</code>",
        'options': {'parse_mode': 'HTML'}
    },
    'payment_details_message': {
        'caption': "Выберите способ оплаты:",
        'options': {'parse_mode': 'HTML'}
    }
}


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