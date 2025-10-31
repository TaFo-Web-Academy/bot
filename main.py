# main.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, \
    CallbackQueryHandler
from database import Database
from admin import admin_export, admin_stats, admin_broadcast
from config import BOT_TOKEN, MESSAGES, ADMIN_IDS, REGISTRATION_LINK

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Состояния разговора
QUESTIONS = 0

# Вопросы теста
questions = [
    {
        'text': '1. Кӣ қарорҳои муҳимро дар зиндагии ту мегирад?',
        'options': [
            'А) Ман худам',
            'Б) Оила/муаллим/шарик',
            'В) Қисман ман, қисман дигарон',
            'Г) Ман метарсам қарор гирам'
        ],
        'scores': [3, 1, 2, 0]
    },
    {
        'text': '2. Вақте зиндагият хуб намеравад, аввал кӣ айбдор мешавад?',
        'options': [
            'А) Ман',
            'Б) Дигарон',
            'В) Тақдир ҳамин будааст',
            'Г) Намедонам'
        ],
        'scores': [3, 1, 0, 2]
    },
    {
        'text': '3. Кай охирон бор орзуҳои кӯдакиятро навишти?',
        'options': [
            'А) Ҳа, ман дорам',
            'Б) Не, фаромӯш кардам',
            'В) Онҳо хандаоваранд',
            'Г) Ман дигар орзу намекунам'
        ],
        'scores': [3, 1, 0, 0]
    },
    {
        'text': '4. Калимаи "зершуур" ба назари ту чӣ маънӣ дорад?',
        'options': [
            'А) Неруи дохилӣ',
            'Б) Барои равоншиносон аст',
            'В) Ман манфиатдорам, намефаҳмам',
            'Г) Бовар надорам'
        ],
        'scores': [3, 1, 2, 0]
    },
    {
        'text': '5. Оё дар ту барномаҳое ҳастанд, ки зиндагистро идора мекунанд?',
        'options': [
            'А) Ҳа, ва ман пай бурдаам',
            'Б) Шояд, ман мезӯсам',
            'В) Ман ҳамаашро идора мекунам',
            'Г) Намефаҳмам ин чӣ аст'
        ],
        'scores': [3, 2, 1, 0]
    },
    {
        'text': '6. Оя ҳис кардӣ, ки "ин ҳаёт аз они ман нест"?',
        'options': [
            'А) Зиёд',
            'Б) Баъзан',
            'В) Ҳа, ҳамааш моли ман аст',
            'Г) Ман саргардонам'
        ],
        'scores': [0, 1, 3, 2]
    },
    {
        'text': '7. Овози дохилият чӣ мегӯяд?',
        'options': [
            'А) "Метавонӣ, ба пеш!"',
            'Б) "Шояд нашавад..."',
            'В) "Мунтазир шав"',
            'Г) Ман намешунавам'
        ],
        'scores': [3, 1, 2, 0]
    },
    {
        'text': '8. Зершуур метавонад…',
        'options': [
            'А) Зиндагиамро озод кунад',
            'Б) Ба ман кӯмак кунад, ки бибахшам',
            'В) Нафаҳмидам',
            'Г) Барои дигарон аст'
        ],
        'scores': [3, 2, 1, 0]
    },
    {
        'text': '9. Агар имрӯз вараки холӣ медоштӣ, чӣ менависӣ?',
        'options': [
            'А) Ҷавоби пурмуҳаббат, шахсӣ, орзуӣ',
            'Б) Ҷавоби норавшан, кӯтоҳ',
            'В) Ҷавоби тарсон, "ҳарчӣ шавад"',
            'Г) Намедонам'
        ],
        'scores': [3, 1, 0, 0]
    },
    {
        'text': '10. Омодаӣ, ки тақдирро худат нависӣ?',
        'options': [
            'А) Бале, 100%',
            'Б) Мехоҳам, вале метарсам',
            'В) Ҳоло намефаҳмам',
            'Г) Ман қабул кардам ҳамин ҳаётро'
        ],
        'scores': [3, 2, 1, 0]
    }
]


def get_result(total_score):
    if total_score >= 25:
        return "Нависандаи Тақдир", "Ту омодаӣ, ки зиндагии худро ба дасти худ бигирӣ. Шояд дар гузашта барномаҳо ва тарсҳо буданд, аммо имрӯз ту бедор шуда истодаӣ. Курси 'Тақдири худро навис' метавонад суръататро дучанд кунад.\n\n→ Ту барои тренинг 100% омода ҳастӣ."
    elif total_score >= 15:
        return "Дар марҳилаи бедорӣ", "Ту ҳис мекунӣ, ки дигар 'барномаҳои кӯҳна' ба дард намехӯранд. Аммо ҳоло ҳанӯз дар ҷустуҷӯи садои ҳақиқати худ ҳастӣ. Ту ба як такон ниёз дорӣ, то тақдирро воқеан худат нависӣ.\n\n→ Ин тренинг метавонад оғози нав бошад."
    else:
        return "Тақдири ту зери таъсири дигарон аст", "Шояд ин ҳаёт комилан туву нест. Қарорҳо, эҳсосҳо ва орзуҳо зери қабати барномаҳои кӯҳна пинҳон шудаанд. Аммо агар ту ин тестро кардӣ — ин аломати бедориаст.\n\n→ Вақти он расидааст, ки бедор шавӣ."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if db.user_exists(user_id):
        await update.message.reply_text(
            "┌─────────────────────┐\n"
            "│  🎯 САЛОМ ДӮСТ!  │\n"
            "└─────────────────────┘\n\n"
            "Шумо аллакай ин тестро\n"
            "гузаронидаед! ✅\n\n"
            f"📅 Тренинг: 8 ноябр\n"
            f"🕐 Соат: 14:00\n"
            f"📍 Душанбе, Профсаюз\n"
            f"   Доми София 3 этаж\n\n"
            f"🔗 Барои сабти ном:\n{REGISTRATION_LINK}"
        )
        return ConversationHandler.END

    # Сбрасываем все данные при старте
    context.user_data.clear()
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0

    await update.message.reply_text(
        "╔═══════════════════════════╗\n"
        "║   🧠 ТЕСТ ПСИХОЛОГИИ   ║\n"
        "╚═══════════════════════════╝\n\n"
        "💭 «ОЯ ТУ ТАҚДИРИ ХУДРО\n"
        "      МЕНАВИСӢ?»\n\n"
        "┌─────────────────────────┐\n"
        "│  📋 ТАРЗИ КОР:          │\n"
        "├─────────────────────────┤\n"
        "│  • 10 савол            │\n"
        "│  • Барои ҳар ҷавоб     │\n"
        "│    хол гир             │\n"
        "│  • Дар охир натиҷа     │\n"
        "│    ва роҳнамоӣ         │\n"
        "└─────────────────────────┘\n\n"
        "⏱ Вақт: 2-3 дақиқа\n\n"
        "👇 Барои оғоз тугмаро\n"
        "    пахш кунед:"
    )

    await ask_question(update, context)
    return QUESTIONS


async def ask_question(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update_or_query, Update):
        message_method = update_or_query.message.reply_text
    else:
        message_method = update_or_query.message.reply_text

    current_question = context.user_data.get('current_question', 0)

    logger.info(f"📝 Задаём вопрос №{current_question + 1}")

    if current_question < len(questions):
        question = questions[current_question]

        # Прогресс бар
        progress = "█" * (current_question + 1) + "░" * (len(questions) - current_question - 1)
        percentage = int((current_question + 1) / len(questions) * 100)

        question_text = (
            f"╔═══════════════════════════╗\n"
            f"║  📊 ПРОГРЕСС: {percentage}%  [{progress}]\n"
            f"╚═══════════════════════════╝\n\n"
            f"❓ Савол {current_question + 1}/{len(questions)}\n\n"
            f"┌─────────────────────────┐\n"
            f"│ {question['text']}\n"
            f"└─────────────────────────┘\n\n"
            f"📌 Интихоб кунед:\n\n"
        )

        for i, option in enumerate(question['options']):
            emoji = ["🅰️", "🅱️", "🆎", "🅾️"][i]
            question_text += f"{emoji} {option}\n"

        keyboard = [
            [
                InlineKeyboardButton("🅰️ А", callback_data=f"ans_{current_question}_0"),
                InlineKeyboardButton("🅱️ Б", callback_data=f"ans_{current_question}_1")
            ],
            [
                InlineKeyboardButton("🆎 В", callback_data=f"ans_{current_question}_2"),
                InlineKeyboardButton("🅾️ Г", callback_data=f"ans_{current_question}_3")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await message_method(question_text, reply_markup=reply_markup)
    else:
        # Показываем результат
        total_score = context.user_data.get('score', 0)
        result_title, result_description = get_result(total_score)

        context.user_data['result_title'] = result_title
        context.user_data['total_score'] = total_score

        result_message = (
            f"╔═══════════════════════════╗\n"
            f"║    🎯 НАТИҶА ТАЙЁР!    ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"🏆 НАТИҶАИ ШУМ:\n"
            f"┌─────────────────────────┐\n"
            f"│ 📊 Баллы: {total_score}/30\n"
            f"│ 🎭 Статус:\n"
            f"│    «{result_title}»\n"
            f"└─────────────────────────┘\n\n"
            f"💬 ТАВСИФИ НАТИҶА:\n"
            f"─────────────────────────\n"
            f"{result_description}\n\n"
            f"╔═══════════════════════════╗\n"
            f"║  📅 ТРЕНИНГИ АСОСӢ     ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"{MESSAGES['training_info']}\n\n"
            f"┌─────────────────────────┐\n"
            f"│ 🔗 САБТИ НОМ ТАВАССУТИ │\n"
            f"│    ССЫЛКАИ ЗЕРИН:      │\n"
            f"└─────────────────────────┘\n\n"
            f"👉 {REGISTRATION_LINK}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ Мо дар интизори шумо!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        await message_method(result_message)

        # Сохраняем в базу
        user_id = update_or_query.effective_user.id if isinstance(update_or_query, Update) else update_or_query.from_user.id
        username = (update_or_query.effective_user.username if isinstance(update_or_query, Update)
                    else update_or_query.from_user.username) or "Номаълум"

        db.add_user(user_id, username, result_title, total_score)
        logger.info(f"✅ Тест завершён: {username}, результат: {result_title} ({total_score} баллов)")

        return ConversationHandler.END


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Парсим callback_data: "ans_0_2" -> вопрос 0, ответ 2
    try:
        parts = query.data.split('_')
        question_index = int(parts[1])
        answer_index = int(parts[2])
    except (ValueError, IndexError) as e:
        logger.error(f"❌ Ошибка парсинга callback_data: {query.data}, ошибка: {e}")
        await query.message.reply_text("❌ Хато. Лутфан аз нав кӯшиш кунед /start")
        return ConversationHandler.END

    current_question = context.user_data.get('current_question', 0)

    # Проверяем, что отвечаем на правильный вопрос
    if question_index != current_question:
        logger.warning(f"⚠️ Игнорируем старую кнопку: вопрос {question_index}, ожидали {current_question}")
        return QUESTIONS

    question = questions[question_index]
    score = question['scores'][answer_index]
    context.user_data['score'] = context.user_data.get('score', 0) + score

    logger.info(
        f"✅ Вопрос {question_index + 1}: ответ {answer_index}, баллов +{score}, всего {context.user_data['score']}")

    # Удаляем предыдущее сообщение
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    # Переходим к следующему вопросу
    context.user_data['current_question'] = question_index + 1

    if context.user_data['current_question'] < len(questions):
        await ask_question(query, context)
        return QUESTIONS
    else:
        # Показываем результат
        total_score = context.user_data['score']
        result_title, result_description = get_result(total_score)

        context.user_data['result_title'] = result_title
        context.user_data['total_score'] = total_score

        result_message = (
            f"╔═══════════════════════════╗\n"
            f"║    🎯 НАТИҶА ТАЙЁР!    ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"🏆 НАТИҶАИ ШУМО:\n"
            f"┌─────────────────────────┐\n"
            f"│ 📊 Баллы: {total_score}/30\n"
            f"│ 🎭 Статус:\n"
            f"│    «{result_title}»\n"
            f"└─────────────────────────┘\n\n"
            f"💬 ТАВСИФИ НАТИҶА:\n"
            f"─────────────────────────\n"
            f"{result_description}\n\n"
            f"╔═══════════════════════════╗\n"
            f"║  📅 ТРЕНИНГИ АСОСӢ     ║\n"
            f"╚═══════════════════════════╝\n\n"
            f"{MESSAGES['training_info']}\n\n"
            f"┌─────────────────────────┐\n"
            f"│ 🔗 САБТИ НОМ ТАВАССУТИ │\n"
            f"│    ССЫЛКАИ ЗЕРИН:      │\n"
            f"└─────────────────────────┘\n\n"
            f"👉 {REGISTRATION_LINK}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ Мо дар интизори шумо!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        await query.message.reply_text(result_message)

        # Сохраняем в базу
        user_id = query.from_user.id
        username = query.from_user.username or "Номаълум"

        db.add_user(user_id, username, result_title, total_score)
        logger.info(f"✅ Тест завершён: {username}, результат: {result_title} ({total_score} баллов)")

        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '┌─────────────────────┐\n'
        '│  👋 ТО ВОХӮРӢ!   │\n'
        '└─────────────────────┘\n\n'
        'Барои оғози нав /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTIONS: [CallbackQueryHandler(handle_answer, pattern='^ans_')],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("export", admin_export))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("broadcast", admin_broadcast))

    logger.info("🤖 Бот запущен...")
    logger.info(f"📋 Админы: {ADMIN_IDS}")
    application.run_polling()


if __name__ == '__main__':
    main()