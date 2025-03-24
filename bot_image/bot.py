import os, logging, re, paramiko, psycopg2
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Переменные окружения
load_dotenv()
token = os.getenv('TOKEN')
rm_host = os.getenv('RM_HOST')
rm_port = os.getenv('RM_PORT')
rm_user = os.getenv('RM_USER')
rm_password = os.getenv('RM_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_database = os.getenv('DB_DATABASE')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# Логирование
logging.basicConfig(filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    level=logging.INFO, encoding='utf-8')
logger = logging.getLogger(__name__)



# ================== Функционал бота ==================

# Список команд
command_list = {r'/help': 'Вывод списка команд',
                r'/cancel': 'Прерывание текущего диалога',
                r'/find_email': 'Поиск email адресов', 
                r'/find_phone_number': 'Поиск номеров телефонов',
                r'/verify_password': 'Проверка надёжности пароля',
                r'/get_release': 'Показать версию релиза удалённого устройства',
                r'/get_uname': 'Показать архитектуру процессора, имя хоста системы и версию ядра удалённого устройства',
                r'/get_uptime': 'Показать время работы удалённого устройства',
                r'/get_df': 'Показать информацию о состоянии файловой системы удалённого устройства',
                r'/get_free': 'Показать информацию о состоянии оперативной памяти устройства',
                r'/get_mpstat': 'Показать информацию о производительности системы удалённого устройства',
                r'/get_w': 'Показать информацию о работающих на удалённом устройстве пользователях',
                r'/get_auths': 'Показать последние 10 входов на удалённом устройстве',
                r'/get_critical': 'Показать последние 5 критических события на удалённом устройстве',
                r'/get_ps': 'Показать информацию о запущенных процессах на удалённом устройстве',
                r'/get_ss': 'Показать информацию об используемых портах на удалённом устройстве',
                r'/get_apt_list': 'Показать информацию об установленных пакетах на удалённом устройстве',
                r'/get_services': 'Показать информацию о запущенных сервисах на удалённом устройстве',
                r'/get_repl_logs': 'Показать информацию о логах репликации',
                r'/get_emails': 'Показать сохранённые электронные адреса',
                r'/get_phone_numbers': 'Показать сохранённые телефонные номера'}


# Сообщение при старте
def startCommand(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}!')


# Вывод доступных команд
def helpCommand(update: Update, context):
    message = 'Список доступных команд:\n'
    for command, disc in command_list.items():
        message += f'{command} - {disc}\n'
    update.message.reply_text(message)

# Остановка диалога
def cancelCommand(update: Update, context: CallbackContext):
    update.message.reply_text("Диалог был прерван")
    return ConversationHandler.END


# Запуск команды поиска email
def findEmailsCommand(update: Update, context: CallbackContext): 
    update.message.reply_text('Введите текст для поиска email-адресов')
    return 'search_email' # Переход к этому состоянию


# Поиск email
def findEmails (update: Update, context: CallbackContext): 
    user_input = update.message.text # Ввод текста пользователем

    emailRegex = re.compile(r'[a-zA-Z0-9_%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}') # Regex для поиска email-адресов
    emailList = emailRegex.findall(user_input) # Найденные email-адреса
    
    if not emailList: # Email-адресов нет
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END
    
    uniqueEmails = [] # Список email
    for number in emailList: # Удаление дубликатов
        if uniqueEmails.count(number) == 0:
            uniqueEmails.append(number)
    
    context.user_data['emails'] = uniqueEmails # Сохранение электронных почт в диалоге

    emails = '' # Строка, где будут email
    for i in range(len(uniqueEmails)):
        emails += f'{i+1}. {uniqueEmails[i]}\n'
    
    update.message.reply_text(f'Найденные email-адреса:\n{emails}') # Отправка сообщения пользователю
    update.message.reply_text('Сохранить их? (Напишите "да" для сохранения)')
    return 'add_email_into_db' # Переход к следующему состоянию


# Сохранение email
def addEmails (update: Update, context: CallbackContext): 
    user_input = update.message.text # Ввод текста пользователем
    user_input = user_input.lower() # Преобразование строки для более удобной проверки

    if user_input != "да": # Проверка ответа пользователя
        update.message.reply_text('Согласия дано не было, сохранения не будет')
        return ConversationHandler.END
    
    emails = context.user_data['emails'] # Получение сохранённых почт

    connection = psycopg2.connect(database=db_database, user=db_user, password=db_password, host=db_host, port=db_port) # Подключение к бд
    cursor = connection.cursor() # Создание курсора
    rowcount = 0 # счётчик затронутых строк
    query = "insert into emails (email) values (%s)" # Запрос (используется заполнитель строки %s чтобы потом подставить вместо 
                                                     # него значение для предотвращения SQLi)


    for email in emails: # Добавление адресов
        cursor.execute(query, (email, )) # (email, ) говорит python сделать кортеж из одного элемента
        rowcount += cursor.rowcount

    connection.commit() # Сохранения результата

    if rowcount == len(emails): # Проверка количества затронутых строк для определяния успешности выполнения запроса
        update.message.reply_text(f'Все email-адреса были добавлены')
    else:
        update.message.reply_text(f'Возникла ошибка при добавлении email-адресов')

    cursor.close() # Закрытие курсора
    connection.close() # Закрытие соединения
    return ConversationHandler.END


# Запуск команды поиска номеров телефона
def findPhoneNumberCommand(update: Update, context: CallbackContext): 
    update.message.reply_text('Введите текст для поиска телефонных номеров')
    return 'search_phone_number' # Переход к этому состоянию


# Поиск номеров телефона
def findPhoneNumbers (update: Update, context: CallbackContext): 
    user_input = update.message.text # Ввод текста пользователем

    phoneNumFormats = [r'(?:8|\+7) \(\d{3}\) \d{3}-\d{2}-\d{2}', # Формат 8/+7 (XXX) XXX-XX-XX
                       r'(?:8|\+7)\d{10}',                       # Формат 8/+7XXXXXXXXXX
                       r'(?:8|\+7)\(\d{3}\)\d{7}',               # Формат 8/+7(XXX)XXXXXXX
                       r'(?:8|\+7) \d{3} \d{3} \d{2} \d{2}',     # Формат 8/+7 XXX XXX XX XX
                       r'(?:8|\+7) \(\d{3}\) \d{3} \d{2} \d{2}', # Формат 8/+7 (XXX) XXX XX XX
                       r'(?:8|\+7)-\d{3}-\d{3}-\d{2}-\d{2}']     # Формат 8/+7-XXX-XXX-XX-XX
    phoneNumberList = [] # Найденные номера телефонов
    for format in phoneNumFormats: # Поиск номеров телефонов
        formatCompiled = re.compile(format)
        phoneNumberList += formatCompiled.findall(user_input)
    
    if not phoneNumberList: # Номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    uniquePhoneNumbers = [] # Список уникальных номеров
    for number in phoneNumberList: # Удаление дубликатов
        if uniquePhoneNumbers.count(number) == 0:
            uniquePhoneNumbers.append(number)
    
    context.user_data['phones'] = uniquePhoneNumbers # Сохранение номеров в диалоге

    phoneNumbers = '' # Строка, где будут номера телефонов
    for i in range(len(uniquePhoneNumbers)):
        phoneNumbers += f'{i+1}. {uniquePhoneNumbers[i]}\n'
    
    update.message.reply_text(f'Найденные номера телефонов:\n{phoneNumbers}') # Отправка сообщения пользователю
    update.message.reply_text('Сохранить их? (Напишите "да" для сохранения)')
    return 'add_phone_into_db' # Переход к следующему состоянию


# Сохранение телефонных номеров
def addPhones (update: Update, context: CallbackContext): 
    user_input = update.message.text # Ввод текста пользователем
    user_input = user_input.lower() # Преобразование строки для более удобной проверки

    if user_input != "да": # Проверка ответа пользователя
        update.message.reply_text('Согласия дано не было, сохранения не будет')
        return ConversationHandler.END
    
    phones = context.user_data['phones'] # Получение сохранённых телефонных номеров

    connection = psycopg2.connect(database=db_database, user=db_user, password=db_password, host=db_host, port=db_port) # Подключение к бд
    cursor = connection.cursor() # Создание курсора
    rowcount = 0 # счётчик затронутых строк
    query = "insert into phones (phone) values (%s)" # Запрос (используется заполнитель строки %s чтобы потом подставить вместо 
                                                     # него значение для предотвращения SQLi)


    for phone in phones: # Добавление адресов
        print(phone)
        cursor.execute(query, (phone, )) # (phone, ) говорит python сделать кортеж из одного элемента
        rowcount += cursor.rowcount

    connection.commit() # Сохранения результата

    if rowcount == len(phones): # Проверка количества затронутых строк для определяния успешности выполнения запроса
        update.message.reply_text(f'Все телефонные номера были добавлены')
    else:
        update.message.reply_text(f'Возникла ошибка при добавлении телефонных номеров')

    cursor.close() # Закрытие курсора
    connection.close() # Закрытие соединения
    return ConversationHandler.END


# Запуск команды проверки пароля
def verifyPasswordCommand(update: Update, context): 
    update.message.reply_text('Введите пароль для проверки')
    return 'verification' # Переход к этому состоянию


# Проверка пароля
def verifyPassword (update: Update, context): 
    user_input = update.message.text # Ввод текста пользователем

    if "\n" in user_input: # Проверка, что была введена одна строка
        update.message.reply_text('Необходимо ввести одну строку')
        update.message.reply_text('Введите пароль для проверки')
        return 'verification'

    passwdRegex = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}') # Regex для проверки пароля
    if re.fullmatch(passwdRegex, user_input): # Проверка сложности пароля
        update.message.reply_text('Пароль сложный')
    else:
         update.message.reply_text('Пароль простой')

    return ConversationHandler.END # Завершение работы обработчика диалога


# Команда для получения информации о релизе
def getReleaseCommand(update: Update, context):
    client = paramiko.SSHClient() # Экземпляр класса клиента
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Устанавление политики автоматического добавления хост-ключей
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password) # Подключение к удалённому хосту
    stdin, stdout, stderr = client.exec_command('lsb_release -a') # Выполнение команды
    data = stdout.read() + stderr.read() # Сохранение вывода
    client.close() # Закрытие соединения
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1] # Форматирование вывода
    update.message.reply_text(data) # Отправка ответа


# Команда для получения информации об архитектуре процессора
def getUnameCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    data = '' # Конечное сообщение
    stdin, stdout, stderr = client.exec_command('uname -m')
    tmp_data = stdout.read() + stderr.read() # Часть сообщения
    tmp_data = str(tmp_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    data += 'Архитектуры процессора: ' + tmp_data # Добавление информации в конечное сообщение
    stdin, stdout, stderr = client.exec_command('uname -n')
    tmp_data = stdout.read() + stderr.read() # Часть сообщения
    tmp_data = str(tmp_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    data += 'Имя хоста: ' + tmp_data # Добавление информации в конечное сообщение
    stdin, stdout, stderr = client.exec_command('uname -v')
    tmp_data = stdout.read() + stderr.read() # Часть сообщения
    tmp_data = str(tmp_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    data += 'Версия ядра: ' + tmp_data # Добавление информации в конечное сообщение
    client.close()
    update.message.reply_text(data)


# Команда для получения информации о времени работы
def getUptimeCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('uptime -p')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о состоянии файловой системы
def getDfCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('df -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о состоянии оперативной памяти
def getFreeCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('free')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о производительности системы
def getMpstatCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о работающих в данной системе пользователях
def getWCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о последних 10 входах в систему
def getAuthsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('last -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о последних 5 критических события
def getCriticalCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('journalctl -p crit -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации о запущенных процессах
def getPsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('ps')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)


# Команда для получения информации об используемых портах
def getSsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('ss -Q')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t').replace('                     ', '    ')[2:-1]
    if len(data) > 4096: # Если сообщение длиннее 4096 символов, то делим его на несколько сообщений
        for i in range(0, len(data), 4096):
            update.message.reply_text(data[i:i+4096])
    else:
        update.message.reply_text(data)


# Запуск команды сбора информации об установленных пакетах
def getAptListCommand(update: Update, context): 
    update.message.reply_text('Введите название пакета (введите "Все" для просмотра всех пакетов)\n*При выводе всех пакетов, ответ будет отправлен в виде текстового файла')
    return 'getting_apt_info' # Переход к этому состоянию

# Вывод информации о пакетах
def getAptList (update: Update, context): 
    user_input = update.message.text # Ввод текста пользователем

    if "\n" in user_input: # Проверка, что была введена одна строка
        update.message.reply_text('Необходимо ввести одну строку')
        update.message.reply_text('Введите название пакета (введите "Все" для просмотра всех пакетов)\n*При выводе всех пакетов, ответ будет отправлен в виде текстового файла')
        return 'getting_apt_info'
    
    command = '' # команда для выполнения
    if user_input == 'Все': # Проверка выбора пакета
        command = 'apt list'
    else:
        command = f'apt show {user_input}'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    if user_input == 'Все': # Если нужно показать все пакеты, то создаётся текстовый файл с ответом
        output = open('reply.txt', 'w') 
        output.write(data)
        output.close()
        output = open('logfile.txt', 'r')
        update.message.reply_document(output, 'Список_всех_установленных_пакетов.txt')
        output.close()
        # os.remove('./reply.txt') # Удаление временного файла с ответами (хотя это не необходимо, т.к. файл просто перезаписывается)
    else: # Иначе просто вывести информацию о пакете
        if len(data) > 4096:
            for i in range(0, len(data), 4096):
                update.message.reply_text(data[i:i+4096])
        else:
            update.message.reply_text(data)

    return ConversationHandler.END # Завершение работы обработчика диалога


# Команда для получения информации о запущенных сервисах
def getServicesCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=rm_host, port=rm_port, username=rm_user, password=rm_password)
    stdin, stdout, stderr = client.exec_command('service --status-all')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    if len(data) > 4096:
        for i in range(0, len(data), 4096):
            update.message.reply_text(data[i:i+4096])
    else:
        update.message.reply_text(data)


# Команда для получения информации о логах репликации
def getReplLogsCommand(update: Update, context):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=db_host, port=rm_port, username=db_user, password=db_password)
    stdin, stdout, stderr = client.exec_command('cat /var/log/postgresql/postgresql-16-main.log | grep "received replication command"')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    output = open('repl_logs.txt', 'w') 
    output.write(data)
    output.close()
    output = open('repl_logs.txt', 'r')
    update.message.reply_document(output, 'Логи_репликации.txt')
    output.close()
    # os.remove('./reply.txt') # Удаление временного файла с ответами (хотя это не необходимо, т.к. файл просто перезаписывается)


# Команда для получения сохранённых электронных почтовых адресов
def getEmailsCommand(update: Update, context):
    connection = psycopg2.connect(database=db_database, user=db_user, password=db_password, host=db_host, port=db_port) # Подключение к бд
    cursor = connection.cursor() # Создание курсора
    query = "SELECT email FROM emails" # Запрос
    cursor.execute(query) # Выполнение запроса
    data = cursor.fetchall() # Получение данных запроса
    reply = 'Сохранённые email-адреса:\n' # Ответное сообщение
    for i in range(len(data)):
        reply += f'{i+1}: {data[i][0]}\n'
    cursor.close() # Закрытие курсора
    connection.close() # Закрытие соединения
    update.message.reply_text(reply)


# Команда для получения сохранённых номеров телефона
def getPhoneNumbersCommand(update: Update, context):
    connection = psycopg2.connect(database=db_database, user=db_user, password=db_password, host=db_host, port=db_port) # Подключение к бд
    cursor = connection.cursor() # Создание курсора
    query = "SELECT phone FROM phones" # Запрос
    cursor.execute(query) # Выполнение запроса
    data = cursor.fetchall() # Получение данных запроса
    reply = 'Сохранённые номера телефонов:\n' # Ответное сообщение
    for i in range(len(data)):
        reply += f'{i+1}: {data[i][0]}\n'
    cursor.close() # Закрытие курсора
    connection.close() # Закрытие соединения
    update.message.reply_text(reply)


# Точка входа
def main():
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher # Диспетчер для регистрации обработчиков

    # Обработчик диалога поиска email
    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={'search_email': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
                'add_email_into_db': [MessageHandler(Filters.text & ~Filters.command, addEmails)]},
        fallbacks=[CommandHandler('cancel', cancelCommand)]
    )

    # Обработчик диалога поиска номеров телефона
    convHandlerFindPhoneNumber = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumberCommand)],
        states={'search_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
                'add_phone_into_db': [MessageHandler(Filters.text & ~Filters.command, addPhones)]},
        fallbacks=[CommandHandler('cancel', cancelCommand)]
    )

    # Обработчик диалога проверки надёжности пароля
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={'verification': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)]},
        fallbacks=[CommandHandler('cancel', cancelCommand)]
    )

    # Обработчик диалога выбора просмотра установленных пакетов
    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={'getting_apt_info': [MessageHandler(Filters.text & ~Filters.command, getAptList)]},
        fallbacks=[CommandHandler('cancel', cancelCommand)]
    )
		
	# Добавление обработчиков команд
    dp.add_handler(CommandHandler("start", startCommand))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerFindPhoneNumber)
    dp.add_handler(convHandlerVerifyPassword)	
    dp.add_handler(CommandHandler("get_release", getReleaseCommand))
    dp.add_handler(CommandHandler("get_uname", getUnameCommand))
    dp.add_handler(CommandHandler("get_uptime", getUptimeCommand))
    dp.add_handler(CommandHandler("get_df", getDfCommand))
    dp.add_handler(CommandHandler("get_free", getFreeCommand))
    dp.add_handler(CommandHandler("get_mpstat", getMpstatCommand))
    dp.add_handler(CommandHandler("get_w", getWCommand))
    dp.add_handler(CommandHandler("get_auths", getAuthsCommand))
    dp.add_handler(CommandHandler("get_critical", getCriticalCommand))
    dp.add_handler(CommandHandler("get_ps", getPsCommand))
    dp.add_handler(CommandHandler("get_ss", getSsCommand))
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(CommandHandler("get_services", getServicesCommand))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLogsCommand))
    dp.add_handler(CommandHandler("get_emails", getEmailsCommand))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhoneNumbersCommand))

    updater.start_polling() # Запуска бота
    updater.idle() # Остановка бота при нажатии Ctrl+C


if __name__ == '__main__':
    main()
