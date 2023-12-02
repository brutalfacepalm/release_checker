import logging
import re
import requests

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, ConversationHandler
from telegram.ext.filters import Regex


def create_bot():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    async def post_init(application: Application):
        """
        Добавляет пункты в меню чата с ботом.
        """
        command_info = [
            BotCommand('start', 'чтобы начать диалог')
        ]
        await application.bot.set_my_commands(command_info)

    async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Точка входа в чат с ботом.
        Приветствие.
        """
        text = 'Текст приветствия и описания работы бота'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        await start_communication(update, context)
        ## TO DO ADD USER TO TABLE DATABASE
        return 0

    async def start_communication(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Точка входа в чат с ботом.
        Приветствие.
        """
        keyboard = [
            [
                KeyboardButton('Проверить новые релизы'),
            ],
            [
                KeyboardButton('Управление моими подписками')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Выбери действие: КОРОТКОЕ ОПИСАНИЕ КАЖДОГО ДЕЙСТВИЯ",
                                       reply_markup=reply_markup)
        send_user = {'user_id': update.message.from_user.id,
                     'username': update.message.from_user.username,
                     'first_name': update.message.from_user.first_name}
        uri = 'http://0.0.0.0:8880/add_user'
        requests.post(uri, json=send_user)
        return 0

    async def check_releases(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ## TO DO SELECT USER-RELEASE-RELEASE_NUMBER FROM TABLES AND CLEAR TABLE BY USER
        await update.message.reply_text('Список обновленных релизов: СПИСОК ОБНОВЛЕННЫХ РЕЛИЗОВ')
        await start_communication(update, context)
        return 0

    async def manage_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # query = update.callback_query
        # await query.answer()
        # await query.edit_message_text(text=f'Selected option: {query}')
        keyboard = [
            [
                KeyboardButton('Показать список подписок')
            ],
            [
                KeyboardButton('Добавить подписки'),
                KeyboardButton('Удалить подписки')
            ],
            [
                KeyboardButton('Подписаться на уведомления'),
                KeyboardButton('Отписаться от уведомлений')
            ],
            [
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Управление подписками: КОРОТКОЕ ОПИСАНИЕ МЕТОДОВ",
                                       reply_markup=reply_markup)
        return 1

    async def list_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ## TO DO SELECT USER-RELEASES FROM TABLE
        await update.message.reply_text('Твой список подписок: СПИСОК ПОДПИСОК')
        await manage_subscription(update, context)
        return 1

    async def add_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                KeyboardButton('Добавить одну'),
                KeyboardButton('Добавить списком')
            ],
            [
                KeyboardButton('Назад'),
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Добавление подписок: ОБЩАЯ ИНСТРУКЦИЯ ПО ДОБАВЛЕНИЮ",
                                       reply_markup=reply_markup)
        return 2

    async def delete_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                KeyboardButton('Удалить списком'),
                KeyboardButton('Удалить все')
            ],
            [
                KeyboardButton('Назад'),
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Удаление подписок: ОБЩАЯ ИНСТРУКЦИЯ ПО УДАЛЕНИЮ",
                                       reply_markup=reply_markup)
        return 4

    async def set_time_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                KeyboardButton('Назад'),
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Установи время увдомлений: ОБЩАЯ ИНСТРУКЦИЯ ПО УСТАНОВКЕ УВЕДОМЛЕНИЙ",
                                       reply_markup=reply_markup)
        ## TO DO JOB SCHEDULE BY TIME
        return 6

    async def set_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Уведомления установлены')
        await manage_subscription(update, context)
        return 1

    async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ## TO DO CLEAR JOBS BY USER
        await update.message.reply_text('Уведомления отключены')
        await manage_subscription(update, context)
        return 1

    async def add_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Инструкция по добавлению одной библиотеки')
        return 3

    async def add_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Инструкция по добавлению списка библиотек')
        return 3

    async def add_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        parse_libs = re.findall(r'(https://github.com/(\w+)/(\w+))', update.message.text)
        libs = []
        for lib in parse_libs:
            ## TO DO ADD REPO TO TABLE DATABASE REPOS AND SUBSCRIPTIONS AND NOTIFICATIONS
            libs.append((lib[1], lib[2]))

        if len(parse_libs) == 0:
            await update.message.reply_text('Не удалось определить путь до библиотеки')
        elif len(parse_libs) == 1:
            await update.message.reply_text(f'Библиотека {libs[0][1]}(by {libs[0][0]}) добавлена в список отслеживания')
        elif len(parse_libs) > 1:
            libs = ', '.join([f'{l[1]}(by {l[0]})' for l in libs])
            await update.message.reply_text(f'Библиотеки {libs} добавлены к отслеживанию')
        await add_subscription(update, context)
        return 2

    async def delete_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('ВЫДАТЬ СПИСОК ПОДПИСОК')
        # await update.message.reply_text('ИНСТРУКЦИЯ ПО УДАЛЕНИЮ СПИСКА БИБЛИОТЕК ИЗ ОТСЛЕЖИВАНИЯ')
        keyboard = [
            [
                KeyboardButton('Назад'),
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='ИНСТРУКЦИЯ ПО УДАЛЕНИЮ СПИСКА БИБЛИОТЕК ИЗ ОТСЛЕЖИВАНИЯ',
                                       reply_markup=reply_markup)
        return 5

    async def delete_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        parse_id_libs = re.findall(r'(\d)', update.message.text)
        libs = []
        for lib in parse_id_libs:
            ## TO DO SELECT OWNER AND REPO FROM TABLES AND DELETE FROM TABLE SUBSRIPTIONS
            libs.append(lib[0])
        if len(parse_id_libs) == 0:
            await update.message.reply_text('Не удалось определить библиотеки для удаления из отслеживания')
        elif len(parse_id_libs) == 1:
            await update.message.reply_text(f'Библиотека {libs[0][0]}(by {libs[0][0]}) удалена из списка отслеживания')
        elif len(parse_id_libs) > 1:
            libs = ', '.join([f'{l[0]}(by {l[0]})' for l in libs])
            await update.message.reply_text(f'Библиотеки {libs} удалены из списка отслеживания')
        await delete_subscription(update, context)
        return 4

    async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ## TO DO DELETE ALL REPOS FROM SUBSCRIPTIONS BY USER
        await update.message.reply_text('Список отслеживания очищен')
        await manage_subscription(update, context)
        return 1

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Жми /start для запуска бота.')

    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END

    def bot_start():
        application_telegram = Application.builder().token('6810547658:AAEs0B_CY77vGiuN_CD3FRSVwlngh0koCAY').post_init(post_init).build()

        # application_telegram.add_handler(CommandHandler('start', welcome))
        # application_telegram.add_handler(MessageHandler(Regex('^(В начало)$'), start_communication))
        start_conv = ConversationHandler(entry_points=[CommandHandler('start', welcome),
                                                       MessageHandler(Regex('^(В начало)$'), start_communication)],
                                         states={0: [MessageHandler(Regex('^(Проверить новые релизы)$'), check_releases),
                                                     MessageHandler(Regex('^(Управление моими подписками)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 1: [MessageHandler(Regex('^(Показать список подписок)$'), list_subscription),
                                                     MessageHandler(Regex('^(Добавить подписки)$'), add_subscription),
                                                     MessageHandler(Regex('^(Удалить подписки)$'), delete_subscription),
                                                     MessageHandler(Regex('^(Подписаться на уведомления)$'), set_time_notification),
                                                     MessageHandler(Regex('^(Отписаться от уведомлений)$'), delete_notification),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 2: [MessageHandler(Regex('^(Добавить одну)$'), add_one),
                                                     MessageHandler(Regex('^(Добавить списком)$'), add_list),
                                                     MessageHandler(Regex('^(Назад)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 3: [MessageHandler(Regex('https:\/\/github\.com\/(\w+)\/(\w+)'), add_repos),
                                                     MessageHandler(Regex('^(Добавить одну)$'), add_one),
                                                     MessageHandler(Regex('^(Добавить списком)$'), add_list),
                                                     MessageHandler(Regex('^(Назад)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 4: [MessageHandler(Regex('^(Удалить списком)$'), delete_list),
                                                     MessageHandler(Regex('^(Удалить все)$'), delete_all),
                                                     MessageHandler(Regex('^(Назад)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 5: [MessageHandler(Regex('(\d)'), delete_repos),
                                                     MessageHandler(Regex('^(Назад)$'), delete_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 6: [MessageHandler(Regex('^(([0,1]?\d|[2][0-3]):([0-5]\d))$'), set_notification),
                                                     MessageHandler(Regex('^(Назад)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)]},
                                         fallbacks=[CommandHandler('cancel', cancel)])
        application_telegram.add_handler(start_conv)

        # application_telegram.add_handler(MessageHandler(Regex('^(Проверить новые релизы)$'), check_releases))
        # application_telegram.add_handler(MessageHandler(Regex('^(Управление моими подписками)$'), manage_subscription))

        # application_telegram.add_handler(MessageHandler(Regex('^(Показать список подписок)$'), list_subscription))
        # application_telegram.add_handler(MessageHandler(Regex('^(Добавить подписки)$'), add_subscription))
        # application_telegram.add_handler(MessageHandler(Regex('^(Удалить подписки)$'), delete_subscription))
        # application_telegram.add_handler(MessageHandler(Regex('^(Подписаться на уведомления)$'), set_time_notification))
        # application_telegram.add_handler(MessageHandler(Regex('^(Отписаться от уведомлений)$'), delete_notification))
        # application_telegram.add_handler(MessageHandler(Regex('^(Управление моими подписками)$'), manage_subscription))

        # conv_handler_add = ConversationHandler(entry_points=[MessageHandler(Regex('^(Добавить одну)$'), add_one),
        #                                                      MessageHandler(Regex('^(Добавить списком)$'), add_list)],
        #                                        states={0: [MessageHandler(Regex('https:\/\/github\.com\/(\w+)\/(\w+)'), add_repos)]},
        #                                        fallbacks=[])
        # conv_handler_del = ConversationHandler(entry_points=[MessageHandler(Regex('^(Удалить списком)$'), delete_list)],
        #                                        states={1: [MessageHandler(Regex('(\d)'), delete_repos)]},
        #                                        fallbacks=[])
        # application_telegram.add_handler(MessageHandler(Regex('^(Удалить все)$'), delete_all))
        # application_telegram.add_handler(conv_handler_del)
        # application_telegram.add_handler(MessageHandler(Regex('^(Установить уведомления)$'), set_notification))

        application_telegram.add_handler(CommandHandler('help', help_command))
        application_telegram.run_polling(allowed_updates=Update.ALL_TYPES)

    bot_start()

# def bot_stop():
#     application_telegram.stop()

if __name__ == '__main__':
    create_bot()

# application_telegram.bot(bot)



