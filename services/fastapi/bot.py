import logging
import re
import requests
import json

import emoji
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
            BotCommand('start', 'чтобы начать беседу'),
            BotCommand('cancel', 'закончить эту беседу что бы начать такую же')
        ]
        await application.bot.set_my_commands(command_info)

    async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Точка входа в чат с ботом.
        Приветствие.
        """

        us_name = update.message.from_user.username if update.message.from_user.username \
            else update.message.from_user.first_name if update.message.from_user.first_name else 'Stranger'
        text = f'''Привет, {us_name}!\nМеня зовут Rchecker и я не человек.\n'''
        text += 'Я могу отслеживать обновления релизов интересных тебе библиотек Python, которые есть на GitHub.\n'
        text += 'Просто следуй инструкциям и будь в курсе последних обновлений твоих любимых библиотек!'
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
        text = f'Здесь ты можешь проверить наличие обновлений библиотек, нажав\n\U00002705 *Проверить новые релизы*.\n\n'
        text += 'А если ты еще не подписался на обновления, то можешь сделать это в разделе\n\U00002705 *Управление моими подписками*.'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup,
                                       parse_mode='Markdown')
        send_user = {'user_id': update.message.from_user.id,
                     'username': update.message.from_user.username if update.message.from_user.username else '',
                     'first_name': update.message.from_user.first_name if update.message.from_user.first_name else ''}
        uri = 'http://0.0.0.0:8880/add_user'
        requests.post(uri, json=send_user)
        return 0

    def get_releases(user):
        uri = f'http://0.0.0.0:8880/get_releases/{user}'
        response = requests.get(uri)
        subscriptions_repos = 'Список обновленных релизов: \n{}'
        if response.status_code == 200:
            response_subscriptions = json.loads(response.text)
            if response_subscriptions:
                subscript = ''
                for idx, repo in enumerate(response_subscriptions):
                    if repo['user_id'] == user:
                        subscript += f"{idx + 1}. [{repo['repo_name']}(by {repo['owner']})]({repo['repo_uri']}), релиз № {repo['release']} от {repo['release_date']} \n"
            else:
                subscript = 'Обновлений не обнаружено.\U0001F61E'
        else:
            subscript = 'Неизвестная ошибка чтения списка обновленных релизов.\U0001F47D'

        subscriptions_repos = subscriptions_repos.format(subscript)
        return subscriptions_repos

    async def check_releases(update: Update, context: ContextTypes.DEFAULT_TYPE):
        subscriptions_repos = get_releases(update.message.from_user.id)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=subscriptions_repos,
                                       parse_mode='Markdown', disable_web_page_preview=True)
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
        text = 'Краткое руководство по разделу\n'
        text += '1. \U0001F4CB *Показать список подписок* - если нужно отобразить текущие подписки.\n'
        text += '2. \U00002795 *Добавить подписки* - для добавления подписок (списком или поштучно).\n'
        text += '3. \U00002796 *Удалить подписки* - для удаления всех или некоторых подписок.\n'
        text += '4. \U0001F514 *Подписаться на уведомления* - если хочешь включить автоматические уведомления.\n'
        text += '5. \U0001F515 *Отписаться от уведомлений* - если уведомления нужно отключить.\n'
        text += '6. \U00002B05 *В начало* - вернуться в начало.'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup, parse_mode='Markdown')
        return 1

    def get_subscription(user):
        uri = f'http://0.0.0.0:8880/get_subscriptions/{user}'
        response = requests.get(uri)

        subscriptions_repos = 'Твой список подписок: \n{}'
        repos = {}
        if response.status_code == 200:
            response_subscriptions = json.loads(response.text)
            if response_subscriptions:
                subscript = ''
                for idx, repo in enumerate(response_subscriptions):
                    if repo['user_id'] == user:
                        subscript += f"{idx + 1}. [{repo['repo_name']}(by {repo['owner']})]({repo['repo_uri']}), релиз № {repo['release']} от {repo['release_date']} \n"
                        repos[idx + 1] = [repo['owner'], repo['repo_name'], f"'{repo['repo_uri']}'"]
            else:
                subscript = 'Подписок не обнаружено.\U0001F61E'
        else:
            subscript = 'Неизвестная ошибка чтения списка подписок.\U0001F47D'

        return subscriptions_repos.format(subscript), repos

    async def list_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        subscriptions_repos, _ = get_subscription(update.message.from_user.id)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=subscriptions_repos,
                                       parse_mode='Markdown', disable_web_page_preview=True)
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
        text = 'Выбери интересующий тебя пункт добавления подписок.\n'
        text += 'Если уже знаешь, что делать - действуй.'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup)
        return 3

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
        text = 'Выбери интересующий тебя нукт удаления подписок.\n'
        text += 'Если уже знаешь, что делать - действуй.\n'
        text += '*ВАЖНО:*\U000026A0 Если нажмешь \U00002705*Удалить все*, то сразу удалятся все твои подписки. '
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup,
                                       parse_mode='Markdown')
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
                                       text=f"РАЗДЕЛ В РАЗРАБОТКЕ\U0001F6E0",
                                       reply_markup=reply_markup)
        ## TO DO JOB SCHEDULE BY TIME
        return 6

    async def set_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('РАЗДЕЛ В РАЗРАБОТКЕ\U0001F6E0')
        await manage_subscription(update, context)
        return 1

    async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ## TO DO CLEAR JOBS BY USER
        await update.message.reply_text('РАЗДЕЛ В РАЗРАБОТКЕ\U0001F6E0')
        await manage_subscription(update, context)
        return 1

    async def add_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = 'Если хочешь добавить подписку на одну библиотеку - *добавить ссылку на нее* по следующему шаблону:\n'
        text += '*https://gihub.com/OWNER/REPO_NAME*, где\n'
        text += '*OWNER* - пользователь GitHub\n*REPO_NAME* - название репозитория пользователя\n'
        text += '*ВАЖНО:*\U000026A0 репозиторий должен быть зарегистрирован как библиотека и иметь релиз. '
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        return 3

    async def add_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = 'Если хочешь добавить подписку на несколько библиотек - *добавить ссылки на них через запятую* по следующему шаблону:\n'
        text += '*https://gihub.com/OWNER_1/REPO_NAME_1, https://gihub.com/OWNER_2/REPO_NAME_2*, где\n'
        text += '*OWNER_N* - пользователь GitHub\n*REPO_NAME_N* - название репозитория соответствующего пользователя\n'
        text += '*ВАЖНО:*\U000026A0 репозиторий должен быть зарегистрирован как библиотека и иметь релиз. '
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        return 3

    async def add_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        parse_libs = re.findall(r'(https://github.com/(\w+)/(\w+))', update.message.text)
        libs = []
        for lib in parse_libs:
            ## TO DO ADD REPO TO TABLE DATABASE REPOS AND SUBSCRIPTIONS AND NOTIFICATIONS
            libs.append((lib[1], lib[2]))

        send_repos = {'user_id': update.message.from_user.id,
                      'repos': libs}
        uri = 'http://0.0.0.0:8880/add_repos'
        response = requests.post(uri, json=send_repos)

        if response.status_code == 201:
            if len(parse_libs) == 0:
                await update.message.reply_text('Не удалось определить путь до библиотеки\U0001F61E')
            elif len(parse_libs) == 1:
                await update.message.reply_text(f'Библиотека {libs[0][1]}(by {libs[0][0]}) добавлена в список отслеживания\U0001F44C')
            elif len(parse_libs) > 1:
                multi_libs = ', '.join([f'{l[1]}(by {l[0]})' for l in libs])
                await update.message.reply_text(f'Библиотеки {multi_libs} добавлены к отслеживанию\U0001F44C')
            await add_subscription(update, context)

        return 3

    async def delete_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # await update.message.reply_text('ИНСТРУКЦИЯ ПО УДАЛЕНИЮ СПИСКА БИБЛИОТЕК ИЗ ОТСЛЕЖИВАНИЯ')
        keyboard = [
            [
                KeyboardButton('Назад'),
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        text = 'Если хочешь удалить из списка подписки на некоторые библиотеки, просто укажи их номера через запятую.'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup)
        subscriptions_repos, _ = get_subscription(update.message.from_user.id)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=subscriptions_repos,
                                       parse_mode='Markdown', disable_web_page_preview=True)

        return 5

    async def delete_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, repos = get_subscription(update)

        parse_id_libs = re.findall(r'(\d)', update.message.text)
        libs = []
        repos_uri = []
        for lib in parse_id_libs:
            ## TO DO SELECT OWNER AND REPO FROM TABLES AND DELETE FROM TABLE SUBSRIPTIONS
            libs.append(repos[int(lib)])
            repos_uri.append(repos[int(lib)][2])

        send_repos = {'user_id': update.message.from_user.id,
                      'repos': repos_uri}
        print(send_repos)
        uri = 'http://0.0.0.0:8880/delete_subscriptions'
        response = requests.post(uri, json=send_repos)

        if response.status_code == 200:
            if len(parse_id_libs) == 0:
                await update.message.reply_text('Не удалось определить библиотеки для удаления из отслеживания\U0001F44C')
            elif len(parse_id_libs) == 1:
                await update.message.reply_text(f'Библиотека {libs[0][1]}(by {libs[0][0]}) удалена из списка отслеживания\U0001F44C')
            elif len(parse_id_libs) > 1:
                deleted_repos = ', '.join([f'{l[1]}(by {l[0]})' for l in libs])
                await update.message.reply_text(f'Библиотеки {deleted_repos} удалены из списка отслеживания\U0001F44C')
            await delete_subscription(update, context)

        return 4

    async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ## TO DO DELETE ALL REPOS FROM SUBSCRIPTIONS BY USER
        await update.message.reply_text('Список отслеживания очищен \U0001F44C')
        send_repos = {'user_id': update.message.from_user.id}
        uri = 'http://0.0.0.0:8880/delete_all_subscriptions'
        requests.post(uri, json=send_repos)

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
                                         states={0: [CommandHandler('start', start_communication),
                                                     MessageHandler(Regex('^(Проверить новые релизы)$'), check_releases),
                                                     MessageHandler(Regex('^(Управление моими подписками)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 1: [CommandHandler('start', start_communication),
                                                     MessageHandler(Regex('^(Показать список подписок)$'), list_subscription),
                                                     MessageHandler(Regex('^(Добавить подписки)$'), add_subscription),
                                                     MessageHandler(Regex('^(Удалить подписки)$'), delete_subscription),
                                                     MessageHandler(Regex('^(Подписаться на уведомления)$'), set_time_notification),
                                                     MessageHandler(Regex('^(Отписаться от уведомлений)$'), delete_notification),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 3: [CommandHandler('start', start_communication),
                                                     MessageHandler(Regex('https:\/\/github\.com\/(\w+)\/(\w+)'), add_repos),
                                                     MessageHandler(Regex('^(Добавить одну)$'), add_one),
                                                     MessageHandler(Regex('^(Добавить списком)$'), add_list),
                                                     MessageHandler(Regex('^(Назад)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 4: [CommandHandler('start', start_communication),
                                                     MessageHandler(Regex('^(Удалить списком)$'), delete_list),
                                                     MessageHandler(Regex('^(Удалить все)$'), delete_all),
                                                     MessageHandler(Regex('^(Назад)$'), manage_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 5: [CommandHandler('start', start_communication),
                                                     MessageHandler(Regex('(\d)'), delete_repos),
                                                     MessageHandler(Regex('^(Назад)$'), delete_subscription),
                                                     MessageHandler(Regex('^(В начало)$'), start_communication)],

                                                 6: [CommandHandler('start', start_communication),
                                                     MessageHandler(Regex('^(([0,1]?\d|[2][0-3]):([0-5]\d))$'), set_notification),
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
