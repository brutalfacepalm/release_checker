import os
import datetime
import pytz
import logging
import re
import requests
import json

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, BotCommand
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, ConversationHandler
from telegram.ext.filters import Regex, ALL

from database import sm as session_maker
from querysets import NotificationJobsQueryset


def create_bot():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.INFO)

    logger = logging.getLogger(__name__)

    async def post_init(application: Application):
        """
        Добавляет пункты в меню чата с ботом.
        """

        async with application.sm.begin() as session:
            current_jobs = await NotificationJobsQueryset.select(session)
            if current_jobs:
                for user_id, chat_id, hour, minute in current_jobs:
                    application.job_queue.run_daily(callback=send_notifications,
                                                    time=datetime.time(hour=hour, minute=minute,
                                                                       tzinfo=pytz.timezone('Europe/Moscow')),
                                                    user_id=user_id,
                                                    chat_id=chat_id)
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
        send_user = {'user_id': update.message.from_user.id,
                     'username': update.message.from_user.username if update.message.from_user.username else '',
                     'first_name': update.message.from_user.first_name if update.message.from_user.first_name else ''}
        uri = 'http://fastapi:8880/add_user'
        requests.post(uri, json=send_user)

        us_name = update.message.from_user.username if update.message.from_user.username \
            else update.message.from_user.first_name if update.message.from_user.first_name else 'Stranger'


        text = f'''Привет, {us_name}!\nМеня зовут Rchecker и я не человек.\n'''
        text += 'Я могу отслеживать обновления релизов интересных тебе библиотек Python, которые есть на GitHub.\n'
        text += 'Просто следуй инструкциям и будь в курсе последних обновлений твоих любимых библиотек!'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        await start_communication(update, context)

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
        return 0

    def get_releases(user):
        uri = f'http://fastapi:8880/get_releases/{user}'
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
        await update.message.reply_text('Секундочку... это может занять некоторе время.')
        subscriptions_repos = get_releases(update.message.from_user.id)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=subscriptions_repos,
                                       parse_mode='Markdown', disable_web_page_preview=True)
        await start_communication(update, context)
        return 0

    async def manage_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                KeyboardButton('Показать список подписок')
            ],
            [
                KeyboardButton('Добавить подписки'),
                KeyboardButton('Удалить подписки')
            ],
            [
                KeyboardButton('Установить уведомления'),
                KeyboardButton('Отключить уведомления')
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
        text += '4. \U0001F514 *Установить уведомления* - если хочешь включить автоматические уведомления.\n'
        text += '5. \U0001F515 *Отключить уведомления* - если уведомления нужно отключить.\n'
        text += '6. \U00002B05 *В начало* - вернуться в начало.'
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup, parse_mode='Markdown')
        return 1

    def get_subscription(user):
        uri = f'http://fastapi:8880/get_subscriptions/{user}'
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

        subscriptions_repos += '\nУчти, что список содержит последние данные о библиотеках, которые я для тебя отслеживю '
        subscriptions_repos += 'не смотря на то, получал ты увдомления об изменениях или нет.\U0001F632\n'
        subscriptions_repos += 'Я хочу сказать, что ты все еще можешь получить уведомление о новой версии, хотя и будешь о ней знать из этого раздела.\U0001F937'

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
        text = 'Выбери интересующий тебя пукт удаления подписок.\n'
        text += 'Если уже знаешь, что делать - действуй.\n'
        text += '*ВАЖНО:*\U000026A0 Если нажмешь \U00002705*Удалить все*, то сразу удалятся все твои подписки. '
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup,
                                       parse_mode='Markdown')
        return 5

    async def set_time_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                KeyboardButton('Назад'),
                KeyboardButton('В начало')
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           resize_keyboard=True)
        text = f"""Если ты хочешь подключить автоматические уведомления, просто укажи время в формате ЧЧ:ММ.\n"""
        text += "Тогда ты будешь получать информацию о новых релизах, как только они появятся.\n"
        text += "Если ты уже подписался, но хочешь изменить время уведомлений, просто отправь новое время и я все исправлю."
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=text,
                                       reply_markup=reply_markup)
        return 6

    async def send_notifications(context):
        user_id = context._user_id
        chat_id = context._chat_id
        subscriptions_repos = get_releases(user_id)
        if subscriptions_repos:
            await context.bot.send_message(chat_id=chat_id,
                                           text=subscriptions_repos,
                                           parse_mode='Markdown', disable_web_page_preview=True)

    async def set_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        parse_libs = re.findall(r'^([0,1]?\d|[2][0-3]):([0-5]\d)$', update.message.text)[0]
        if parse_libs:
            if context.job_queue.jobs():
                for job in context.job_queue.jobs():
                    if job.user_id == update.message.from_user.id:
                        job.schedule_removal()
                        async with context.application.sm.begin() as session:
                            await NotificationJobsQueryset.delete(session, update.message.from_user.id)

            hour = int(parse_libs[0])
            minute = int(parse_libs[1])

            context.job_queue.run_daily(callback=send_notifications,
                                        time=datetime.time(hour=hour, minute=minute,
                                                           tzinfo=pytz.timezone('Europe/Moscow')),
                                        user_id=update.message.from_user.id,
                                        chat_id=update.effective_message.chat_id
                                        )
            async with context.application.sm.begin() as session:
                await NotificationJobsQueryset.create(session, update.message.from_user.id,
                                                      update.effective_message.chat_id, hour, minute)

        await update.message.reply_text(f'Уведомления успешно подключены. Теперь ты будешь получать их в {hour}:{minute} МСК\U000023F1')
        await manage_subscription(update, context)
        return 1

    async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.job_queue.jobs():
            for job in context.job_queue.jobs():
                if job.user_id == update.message.from_user.id:
                    job.schedule_removal()
                    async with context.application.sm.begin() as session:
                        await NotificationJobsQueryset.delete(session, update.message.from_user.id)
        await update.message.reply_text('Ты успешно отписался от всех уведомлений! \U0001F515')
        await manage_subscription(update, context)
        return 1

    async def send_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Не удалось распознать команду\U0001F648')
        await manage_subscription(update, context)
        return 1

    async def add_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = 'Если хочешь добавить подписку на одну библиотеку - *добавь ссылку на нее* по следующему шаблону:\n'
        text += '*https://gihub.com/OWNER/REPO_NAME*, где\n'
        text += '*OWNER* - пользователь GitHub\n*REPO_NAME* - название репозитория пользователя\n'
        text += '*ВАЖНО:*\U000026A0 репозиторий должен быть зарегистрирован как библиотека и иметь релиз. '
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        return 3

    async def add_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = 'Если хочешь добавить подписку на несколько библиотек - *добавь ссылки на них через запятую* по следующему шаблону:\n'
        text += '*https://gihub.com/OWNER_1/REPO_NAME_1, https://gihub.com/OWNER_2/REPO_NAME_2*, где\n'
        text += '*OWNER_N* - пользователь GitHub\n*REPO_NAME_N* - название репозитория соответствующего пользователя\n'
        text += '*ВАЖНО:*\U000026A0 репозиторий должен быть зарегистрирован как библиотека и иметь релиз. '
        await update.message.reply_text(text, parse_mode='Markdown', disable_web_page_preview=True)
        return 3

    async def add_repos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        parse_libs = re.findall(r'(https://github.com/([^/]+)/([^/,]+))', update.message.text)
        libs = []
        for lib in parse_libs:
            libs.append((lib[1], lib[2]))

        await update.message.reply_text('Секундочку... это может занять некоторе время.')

        send_repos = {'user_id': update.message.from_user.id,
                      'repos': libs}
        uri = 'http://fastapi:8880/add_repos'
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
        _, repos = get_subscription(update.message.from_user.id)

        parse_id_libs = re.findall(r'(\d)', update.message.text)
        libs = []
        repos_uri = []
        for lib in parse_id_libs:
            libs.append(repos[int(lib)])
            repos_uri.append(repos[int(lib)][2])

        send_repos = {'user_id': update.message.from_user.id,
                      'repos': repos_uri}
        uri = 'http://fastapi:8880/delete_subscriptions'
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

        return 5

    async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Список отслеживания очищен \U0001F44C')
        send_repos = {'user_id': update.message.from_user.id}
        uri = 'http://fastapi:8880/delete_all_subscriptions'
        requests.post(uri, json=send_repos)

        await manage_subscription(update, context)
        return 1

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Жми /start для запуска бота.')

    async def cancel(*args):
        return ConversationHandler.END

    def bot_start():
        application_telegram = (Application.builder().token(os.environ.get("TELEGRAM_BOT_TOKEN"))
                                .read_timeout(30).connect_timeout(30).write_timeout(30).post_init(post_init).build())

        to_welcome = CommandHandler('start', welcome)
        to_start = CommandHandler('start', start_communication)
        to_begining = MessageHandler(Regex('^(В начало)$'), start_communication)
        to_backward = MessageHandler(Regex('^(Назад)$'), manage_subscription)
        to_check_releases = MessageHandler(Regex('^(Проверить новые релизы)$'), check_releases)
        to_manage_subscription = MessageHandler(Regex('^(Управление моими подписками)$'), manage_subscription)
        to_list_subscription = MessageHandler(Regex('^(Показать список подписок)$'), list_subscription)
        to_add_subscription = MessageHandler(Regex('^(Добавить подписки)$'), add_subscription)
        to_delete_subscription = MessageHandler(Regex('^(Удалить подписки)$'), delete_subscription)
        to_set_time_notification = MessageHandler(Regex('^(Установить уведомления)$'), set_time_notification)
        to_delete_notification = MessageHandler(Regex('^(Отключить уведомления)$'), delete_notification)
        to_add_one = MessageHandler(Regex('^(Добавить одну)$'), add_one)
        to_add_list = MessageHandler(Regex('^(Добавить списком)$'), add_list)
        to_delete_list = MessageHandler(Regex('^(Удалить списком)$'), delete_list)
        to_delete_all = MessageHandler(Regex('^(Удалить все)$'), delete_all)
        cancel_command = CommandHandler('cancel', cancel)
        to_unknown_message = MessageHandler(ALL, send_unknown_command)
        to_add_repos = MessageHandler(Regex('https:\/\/github\.com\/([^\/]+)\/([^\/,]+)'), add_repos)
        to_delete_repos = MessageHandler(Regex('(\d)'), delete_repos)
        to_set_notification = MessageHandler(Regex('^(([0,1]?\d|[2][0-3]):([0-5]\d))$'), set_notification)

        start_conv = ConversationHandler(entry_points=[to_welcome, to_begining, to_backward, to_check_releases,
                                                       to_manage_subscription, to_list_subscription,
                                                       to_add_subscription, to_delete_subscription,
                                                       to_set_time_notification, to_delete_notification,
                                                       to_add_one, to_add_list, to_delete_list, to_delete_all],

                                         states={0: [to_start, to_check_releases, to_manage_subscription,
                                                     to_begining, cancel_command,
                                                     MessageHandler(ALL, send_unknown_command)],

                                                 1: [to_start, to_list_subscription, to_add_subscription,
                                                     to_delete_subscription, to_set_time_notification,
                                                     to_delete_notification, to_begining, cancel_command,
                                                     to_unknown_message],

                                                 3: [to_start, to_add_repos, to_add_one, to_add_list, to_backward,
                                                     to_begining, cancel_command, to_unknown_message],

                                                 5: [to_start, to_delete_repos, to_delete_list, to_delete_all,
                                                     to_backward, to_begining, cancel_command, to_unknown_message],

                                                 6: [to_start, to_set_notification, to_backward,
                                                     to_begining, cancel_command, to_unknown_message]
                                                 },
                                         fallbacks=[cancel_command])
        application_telegram.add_handler(start_conv)
        application_telegram.sm = session_maker
        application_telegram.add_handler(CommandHandler('help', help_command))
        application_telegram.job_queue.start()

        application_telegram.run_polling(allowed_updates=Update.ALL_TYPES)

    bot_start()


if __name__ == '__main__':
    create_bot()

