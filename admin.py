# admin.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from config import ADMIN_IDS
import os

db = Database()
logger = logging.getLogger(__name__)


async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт данных в Excel для админов"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        logger.warning(f"Попытка доступа к /export от неавторизованного пользователя {update.effective_user.id}")
        return

    try:
        logger.info(f"📊 Экспорт данных запрошен админом {update.effective_user.id}")
        filename = db.export_to_excel()
        with open(filename, 'rb') as file:
            await update.message.reply_document(
                document=file,
                caption=f"📊 Экспорт данных ({db.get_users_count()} пользователей)"
            )
        os.remove(filename)
        logger.info(f"✅ Экспорт успешно отправлен")
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка экспорта: {e}")


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика для админов"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        logger.warning(f"Попытка доступа к /stats от неавторизованного пользователя {update.effective_user.id}")
        return

    try:
        count = db.get_users_count()
        users = db.get_all_users()[:5]

        stats_text = (
            "╔═══════════════════════╗\n"
            "║   📈 СТАТИСТИКА    ║\n"
            "╚═══════════════════════╝\n\n"
            f"👥 Всего участников: {count}\n\n"
            "📋 Последние регистрации:\n"
            "─────────────────────────\n"
        )

        for i, user in enumerate(users, 1):
            stats_text += f"{i}. @{user[1]} - {user[2]} ({user[3]} балла)\n"

        await update.message.reply_text(stats_text)
        logger.info(f"✅ Статистика отправлена админу {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рассылка сообщений всем пользователям"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Доступ запрещен")
        logger.warning(f"Попытка доступа к /broadcast от неавторизованного пользователя {update.effective_user.id}")
        return

    if not context.args:
        await update.message.reply_text(
            "📢 Использование:\n"
            "/broadcast <сообщение>\n\n"
            "Пример:\n"
            "/broadcast Напоминаем о тренинге завтра!"
        )
        return

    message = ' '.join(context.args)
    users = db.get_all_users()
    success = 0
    failed = 0

    logger.info(f"📢 Начинается рассылка для {len(users)} пользователей")

    status_message = await update.message.reply_text(
        f"📤 Начинаем рассылку...\n"
        f"Всего пользователей: {len(users)}"
    )

    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=message)
            success += 1
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user[0]}: {e}")
            failed += 1

    result_text = (
        "╔═══════════════════════╗\n"
        "║  📢 РАССЫЛКА       ║\n"
        "╚═══════════════════════╝\n\n"
        f"✅ Успешно: {success}\n"
        f"❌ Не удалось: {failed}\n"
        f"📊 Всего: {len(users)}"
    )

    await status_message.edit_text(result_text)
    logger.info(result_text)