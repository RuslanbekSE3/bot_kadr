from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InputFile, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)
from config import BOT_TOKEN, ADMINS, GROUP_ID
import os

# Этапы диалога
LANGUAGE, FULL_NAME, AGE, RESUME, PHONE, VACANCY = range(6)

languages = ["uz", "qq", "ru"]

TRANSLATIONS = {
    "uz": {
        "select_language": "Iltimos, tilni tanlang:",
        "full_name": "Iltimos, to'liq ismingizni kiriting (F.I.Sh):",
        "age": "Yoshingizni kiriting:",
        "invalid_age": "Iltimos, yaroqli yosh kiriting.",
        "resume": "Iltimos, rezyumeni yuboring (PDF, DOCX va h.k.):",
        "ask_resume": "Iltimos, rezyumeni yuboring (PDF, DOCX va h.k.):",
        "invalid_file": "Iltimos, to‘g‘ri fayl yuboring.",
        "phone": "Telefon raqamingizni yuboring yoki tugmani bosing:",
        "vacancy": "Vakansiyani tanlang:",
        "submit": "Davom etish",
        "submitted": "Rahmat! Arizangiz yuborildi.",
        "cancel": "Suhbat bekor qilindi. /start orqali qayta boshlang."
    },
    "qq": {
        "select_language": "Tildi tańlań:",
        "full_name": "Tolıq atıńızdı kiritiń (F.A.Ə):",
        "age": "Jasıńızdı kiritiń:",
        "invalid_age": "Iltimas, dúrís jasta kíríziń.",
        "resume": "Iltimas, rezyumeni jiberiń (PDF, DOCX hám t.b):",
        "ask_resume": "Iltimas, rezyumeni jiberiń (PDF, DOCX hám t.b):",
        "invalid_file": "Duris fayl jiberiń.",
        "phone": "Telefon nomerińizdi jiberiń yaki túymeni basıń:",
        "vacancy": "Vakansiyani tańlań:",
        "submit": "Jiberiw",
        "submitted": "Raxmet! Arızańız jiberildi.",
        "cancel": "Sóylesiw toqtaldi. /start menen qayta baslań."
    },
    "ru": {
        "select_language": "Пожалуйста, выберите язык:",
        "full_name": "Пожалуйста, введите ФИО:",
        "age": "Введите ваш возраст:",
        "invalid_age": "Пожалуйста, введите корректный возраст.",
        "resume": "Отправьте ваше резюме (PDF, DOCX и т.д.):",
        "ask_resume": "Пожалуйста, отправьте ваше резюме (PDF, DOCX и т.д.):",
        "invalid_file": "Пожалуйста, отправьте корректный файл.",
        "phone": "Отправьте ваш номер телефона или нажмите кнопку:",
        "vacancy": "Выберите вакансию:",
        "submit": "Продолжить",
        "submitted": "Спасибо! Ваша заявка отправлена.",
        "cancel": "Диалог отменён. Напишите /start чтобы начать заново."
    }
}

vacancy_buttons = [["1-vacancy", "2-vacancy"], ["3-vacancy", "4-vacancy"]]
menu_commands = ReplyKeyboardMarkup([["/start", "/cancel"]], resize_keyboard=True)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(lang)] for lang in languages]
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык / Тилди таńлаń:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return LANGUAGE


# LANGUAGE SELECTED
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text.lower()
    if lang not in languages:
        return await start(update, context)
    context.user_data['lang'] = lang
    await update.message.reply_text(TRANSLATIONS[lang]['full_name'], reply_markup=menu_commands)
    return FULL_NAME


# FULL NAME
async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(TRANSLATIONS[lang]['age'], reply_markup=menu_commands)
    return AGE


# AGE
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    age_text = update.message.text

    if not age_text.isdigit():
        await update.message.reply_text(TRANSLATIONS[lang]['invalid_age'], reply_markup=menu_commands)
        return AGE

    context.user_data['age'] = age_text
    await update.message.reply_text(TRANSLATIONS[lang]['ask_resume'], reply_markup=menu_commands)
    return RESUME


# RESUME FILE
async def get_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    document = update.message.document
    if not document:
        await update.message.reply_text(TRANSLATIONS[lang]['invalid_file'], reply_markup=menu_commands)
        return RESUME
    context.user_data['resume'] = document.file_id

    # PHONE REQUEST BUTTON
    contact_button = KeyboardButton("📱 Share Contact", request_contact=True)
    phone_keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(TRANSLATIONS[lang]['phone'], reply_markup=phone_keyboard)
    return PHONE


# PHONE
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']

    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    context.user_data['phone'] = phone

    await update.message.reply_text(
        TRANSLATIONS[lang]['vacancy'],
        reply_markup=ReplyKeyboardMarkup(vacancy_buttons, resize_keyboard=True)
    )
    return VACANCY


# VACANCY
async def get_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['vacancy'] = update.message.text
    lang = context.user_data['lang']

    message = (
        f"📄 {context.user_data['full_name']}\n"
        f"🎂 {context.user_data['age']} yosh\n"
        f"📱 {context.user_data['phone']}\n"
        f"💼 Vakansiya: {context.user_data['vacancy']}"
    )

    # Отправка админу
    for admin in ADMINS:
        try:
            await context.bot.send_document(admin, document=context.user_data['resume'], caption=message)
        except:
            pass

    # Отправка в группу
    try:
        await context.bot.send_document(GROUP_ID, document=context.user_data['resume'], caption=message)
    except:
        pass

    await update.message.reply_text(TRANSLATIONS[lang]['submitted'], reply_markup=menu_commands)
    return ConversationHandler.END


# CANCEL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    await update.message.reply_text(TRANSLATIONS[lang]['cancel'], reply_markup=menu_commands)
    return ConversationHandler.END


# MAIN
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            RESUME: [MessageHandler(filters.Document.ALL, get_resume)],
            PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, get_phone)],
            VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vacancy)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))

    print("Bot running...")
    app.run_polling()















# from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile, ReplyKeyboardRemove


# from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
# from telegram.ext import ContextTypes
# from config import BOT_TOKEN, ADMINS, GROUP_ID
# import os
#
# LANGUAGE, FULL_NAME, AGE, RESUME, PHONE, VACANCY = range(6)
#
# languages = ["uz", "qq", "ru"]
#
# TRANSLATIONS = {
#     "uz": {
#         "select_language": "Iltimos, tilni tanlang:",
#         "full_name": "Iltimos, to'liq ismingizni kiriting (F.I.Sh):",
#         "age": "Yoshingizni kiriting:",
#         "resume": "Rezyumeni yuboring (PDF, DOCX, va hokazo):",
#         "phone": "Telefon raqamingizni yuboring:",
#         "vacancy": "Vakansiyani tanlang:",
#         "submit": "Davom etish",
#         "submitted": "Rahmat! Arizangiz yuborildi.",
#         "cancel": "Suhbat bekor qilindi. /start orqali qayta boshlang.",
#         "invalid_file": "Iltimos, to‘g‘ri fayl yuboring."
#     },
#     "qq": {
#         "select_language": "Tildi tańlań:",
#         "full_name": "Tolıq atıńızdı kiritiń (F.A.Ə):",
#         "age": "Jasıńızdı kiritiń:",
#         "resume": "Rezyumeni jiberiń (PDF, DOCX, h.t.b):",
#         "phone": "Telefon nomerińizdi jiberiń:",
#         "vacancy": "Vakansiyani tańlań:",
#         "submit": "Jiberiw",
#         "submitted": "Raxmet! Arızańız jiberildi.",
#         "cancel": "Sóylesiw toqtaldi. /start menen qayta baslań.",
#         "invalid_file": "Duris fayl jiberiń."
#     },
#     "ru": {
#         "select_language": "Пожалуйста, выберите язык:",
#         "full_name": "Пожалуйста, введите ФИО:",
#         "age": "Введите ваш возраст:",
#         "resume": "Отправьте ваше резюме (PDF, DOCX и т.д.):",
#         "phone": "Отправьте ваш номер телефона:",
#         "vacancy": "Выберите вакансию:",
#         "submit": "Продолжить",
#         "submitted": "Спасибо! Ваша заявка отправлена.",
#         "cancel": "Диалог отменён. Напишите /start чтобы начать заново.",
#         "invalid_file": "Пожалуйста, отправьте корректный файл."
#     }
# }
#
# vacancy_buttons = [["1-vacancy", "2-vacancy"], ["3-vacancy", "4-vacancy"]]
# menu_commands = ReplyKeyboardMarkup([["/start", "/cancel"]], resize_keyboard=True)
#
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [[KeyboardButton(lang)] for lang in languages]
#     await update.message.reply_text(
#         "Tilni tanlang / Выберите язык / Тилди таńлаń:",
#         reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
#     )
#     return LANGUAGE
#
# async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     lang = update.message.text.lower()
#     if lang not in languages:
#         return await start(update, context)
#     context.user_data['lang'] = lang
#     await update.message.reply_text(TRANSLATIONS[lang]['full_name'], reply_markup=menu_commands)
#     return FULL_NAME
#
# async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data['full_name'] = update.message.text
#     lang = context.user_data['lang']
#     await update.message.reply_text(TRANSLATIONS[lang]['age'], reply_markup=menu_commands)
#     return AGE
#
# async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data['age'] = update.message.text
#     lang = context.user_data['lang']
#     await update.message.reply_text(TRANSLATIONS[lang]['resume'], reply_markup=menu_commands)
#     return RESUME
#
# async def get_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     lang = context.user_data['lang']
#     document = update.message.document
#     if not document:
#         await update.message.reply_text(TRANSLATIONS[lang]['invalid_file'], reply_markup=menu_commands)
#         return RESUME
#     context.user_data['resume'] = document.file_id
#     await update.message.reply_text(TRANSLATIONS[lang]['phone'], reply_markup=menu_commands)
#     return PHONE
#
# async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data['phone'] = update.message.text
#     lang = context.user_data['lang']
#     await update.message.reply_text(TRANSLATIONS[lang]['vacancy'], reply_markup=ReplyKeyboardMarkup(vacancy_buttons, resize_keyboard=True))
#     return VACANCY
#
# async def get_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     context.user_data['vacancy'] = update.message.text
#     lang = context.user_data['lang']
#
#     message = (
#         f"📄 {context.user_data['full_name']}\n"
#         f"🎂 {context.user_data['age']} yosh\n"
#         f"📱 {context.user_data['phone']}\n"
#         f"💼 Vakansiya: {context.user_data['vacancy']}"
#     )
#
#     for admin in ADMINS:
#         try:
#             await context.bot.send_document(admin, document=context.user_data['resume'], caption=message)
#         except:
#             pass
#     try:
#         await context.bot.send_document(GROUP_ID, document=context.user_data['resume'], caption=message)
#     except:
#         pass
#
#     await update.message.reply_text(TRANSLATIONS[lang]['submitted'], reply_markup=menu_commands)
#     return ConversationHandler.END
#
# async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     lang = context.user_data.get('lang', 'ru')
#     await update.message.reply_text(TRANSLATIONS[lang]['cancel'], reply_markup=menu_commands)
#     return ConversationHandler.END
#
# if __name__ == '__main__':
#     app = ApplicationBuilder().token(BOT_TOKEN).build()
#
#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={
#             LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
#             FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
#             AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
#             RESUME: [MessageHandler(filters.Document.ALL, get_resume)],
#             PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
#             VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vacancy)]
#         },
#         fallbacks=[CommandHandler("cancel", cancel)]
#     )
#
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("cancel", cancel))
#     app.add_handler(CommandHandler("start", start))
#     print("Bot running...")
#     app.run_polling()
