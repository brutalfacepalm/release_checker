from telegram import KeyboardButton

menu_schema = {'start_communication': [[KeyboardButton('Проверить новые релизы')],
                                       [KeyboardButton('Управление моими подписками')]],
               'manage_subscription': [[KeyboardButton('Показать список подписок')],
                                       [KeyboardButton('Добавить подписки'),
                                        KeyboardButton('Удалить подписки')],
                                       [KeyboardButton('Установить уведомления'),
                                        KeyboardButton('Отключить уведомления')],
                                       [KeyboardButton('В начало')]],
               'add_subscription': [[KeyboardButton('Добавить одну'),
                                     KeyboardButton('Добавить списком')],
                                    [KeyboardButton('Назад'),
                                     KeyboardButton('В начало')]],
               'delete_subscription': [[KeyboardButton('Удалить списком'),
                                        KeyboardButton('Удалить все')],
                                       [KeyboardButton('Назад'),
                                        KeyboardButton('В начало')]],
               'set_time_notification': [[KeyboardButton('Назад'),
                                          KeyboardButton('В начало')]],
               'delete_list': [[KeyboardButton('Назад'),
                                KeyboardButton('В начало')]],
               }

if __name__ == '__main__':
    pass
