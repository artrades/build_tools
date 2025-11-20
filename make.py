#!/usr/bin/env python

# Импорт необходимых модулей
import os 
import sys

# Определение абсолютного пути к директории текущего скрипта
__dir__name__ = os.path.dirname(os.path.abspath(__file__))

# Добавление различных путей к модулям сборки в системный путь Python
sys.path.append(__dir__name__ + '/scripts')  # Основные скрипты
sys.path.append(__dir__name__ + '/scripts/develop')  # Скрипты для разработки
sys.path.append(__dir__name__ + '/scripts/develop/vendor')  # Вендорные зависимости для разработки
sys.path.append(__dir__name__ + '/scripts/core_common')  # Общие основные скрипты
sys.path.append(__dir__name__ + '/scripts/core_common/modules')  # Модули общих скриптов
sys.path.append(__dir__name__ + '/scripts/core_common/modules/android')  # Android-специфичные модули

# Импорт кастомных модулей сборки
import config       # Модуль для работы с конфигурацией
import base         # Базовые утилиты и функции
import build_sln    # Сборка решений (Visual Studio проекты)
import build_js     # Сборка JavaScript компонентов
import build_server # Сборка серверной части
import deploy       # Деплой собранных артефактов
import make_common  # Сборка общих компонентов и зависимостей
import develop      # Задачи разработки
import argparse     # Парсинг аргументов командной строки

# Цвета для терминала
class Colors:
    RED       = '\033[91m'
    GREEN     = '\033[92m'
    YELLOW    = '\033[93m'
    BLUE      = '\033[94m'
    MAGENTA   = '\033[95m'
    CYAN      = '\033[96m'
    WHITE     = '\033[97m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    END       = '\033[0m'

def print_make_message(message, color=Colors.WHITE, require_setup=False):
    """
    Функция для вывода сообщений с пометкой [make.py]
    
    Args:
        message (str): Текст сообщения
        color (str): Цвет сообщения
        require_setup (bool): Требуется ли установка дополнительных модулей
    """
    current_dir = os.getcwd()
    tag_color = Colors.RED if require_setup else Colors.GREEN
    tag = f"{tag_color}[make.py]{Colors.END}"
    
    print(f"{tag} {color}{message}{Colors.END}")
    print(f"{tag} {Colors.CYAN}Текущая директория: {current_dir}{Colors.END}")

def ask_continue(action_description, require_setup=False):
    """
    Функция для запроса подтверждения продолжения выполнения действия
    
    Args:
        action_description (str): Описание действия, которое будет выполнено
        require_setup (bool): Требуется ли установка дополнительных модулей
    """
    if AUTO_YES:
        print_make_message(f"СЛЕДУЮЩЕЕ ДЕЙСТВИЕ: {action_description}", Colors.YELLOW, require_setup)
        print_make_message("Автоматическое подтверждение (--auto-yes)", Colors.GREEN)
        return True
        
    print_make_message(f"СЛЕДУЮЩЕЕ ДЕЙСТВИЕ:\n{action_description}", Colors.YELLOW, require_setup)
    response = input(f"{Colors.RED}[make.py]{Colors.END} {Colors.WHITE}Продолжить выполнение? (y/n/yes/no): {Colors.END}").strip().lower()
    if response in ['y', 'yes']:
        print_make_message("Продолжаем выполнение...", Colors.GREEN)
        return True
    elif response in ['n', 'no']:
        print_make_message("Прерывание выполнения по запросу пользователя.", Colors.RED)
        exit(0)
    else:
        print_make_message("Неверный ввод. Продолжаем выполнение.", Colors.YELLOW)
        return True

# Проверка версии Python перед началом работы
base.check_python()

# Настройка парсера аргументов командной строки
parser = argparse.ArgumentParser(description="options")
# Добавление флага для сборки только брендинга
parser.add_argument("--build-only-branding", action="store_true")
# Добавление флага для автоматического подтверждения всех действий
parser.add_argument("--auto-yes", "-y", action="store_true", help="Автоматически подтверждать все действия")
args = parser.parse_args()

# Глобальная переменная для автоматического подтверждения
AUTO_YES = args.auto_yes

# Если указан флаг --build-only-branding, устанавливаем соответствующую переменную окружения
if (args.build_only_branding):
    print_make_message("Установка флага сборки только брендинга", Colors.YELLOW)
    base.set_env("OO_BUILD_ONLY_BRANDING", "1")

# Парсинг конфигурации сборки из различных источников (файлы, переменные окружения и т.д.)
print_make_message("Парсинг конфигурации сборки...", Colors.CYAN)
config.parse()

# Получение базовой директории скрипта
base_dir = base.get_script_dir(__file__)
print_make_message(f"Базовая директория скрипта: {base_dir}", Colors.CYAN)

# Установка переменной окружения с информацией о платформе сборки
platform = config.option("platform")
print_make_message(f"Установка платформы сборки: {platform}", Colors.CYAN)
base.set_env("BUILD_PLATFORM", platform)

# Обработка брендинга - важная особенность системы сборки
# Проверяем, что мы не находимся уже в процессе выполнения брендинга и указан конкретный брендинг
if ("1" != base.get_env("OO_RUNNING_BRANDING")) and ("" != config.option("branding")):
    # Формируем путь к директории брендинга (предположительно в родительской директории)
    branding_dir = base_dir + "/../" + config.option("branding")
    print_make_message(f"Обработка брендинга: {config.option('branding')}", Colors.MAGENTA, require_setup=True)
    print_make_message(f"Директория брендинга: {branding_dir}", Colors.CYAN)

    # Если включен режим обновления, работаем с репозиторием брендинга
    if ("1" == config.option("update")):
        is_exist = True
        # Если директория брендинга не существует, клонируем репозиторий
        if not base.is_dir(branding_dir):
            is_exist = False
            print_make_message(f"Клонирование репозитория брендинга: {config.option('branding-url')}", Colors.YELLOW, require_setup=True)
            base.cmd("git", ["clone", config.option("branding-url"), branding_dir])

        # Получаем последние изменения из удаленного репозитория
        print_make_message("Получение обновлений для брендинга...", Colors.YELLOW)
        base.cmd_in_dir(branding_dir, "git", ["fetch"], True)

        # Если директории не было или выключен легкий режим обновления, переключаемся на нужную ветку
        if not is_exist or ("1" != config.option("update-light")):
            print_make_message(f"Переключение на ветку: {config.option('branch')}", Colors.YELLOW)
            base.cmd_in_dir(branding_dir, "git", ["checkout", "-f", config.option("branch")], True)

        # Получаем последние изменения из текущей ветки
        print_make_message("Обновление локальной копии брендинга...", Colors.YELLOW)
        base.cmd_in_dir(branding_dir, "git", ["pull"], True)

    # Если в брендинге есть свой собственный скрипт сборки make.py
    if base.is_file(branding_dir + "/build_tools/make.py"):
        # Проверяем версию сборки в брендинге
        base.check_build_version(branding_dir + "/build_tools")
        # Устанавливаем флаг, что мы выполняем брендинг (для предотвращения рекурсии)
        base.set_env("OO_RUNNING_BRANDING", "1")
        # Сохраняем информацию о текущем брендинге
        base.set_env("OO_BRANDING", config.option("branding"))
        
        # Запрос подтверждения для запуска скрипта сборки брендинга
        if ask_continue(
            f"Запуск скрипта сборки брендинга: {branding_dir}/build_tools/make.py\n"
            "  → ПРЕДУПРЕЖДЕНИЕ: Это рекурсивный вызов скрипта для брендинга\n"
            "  → После завершения основной скрипт остановится",
            require_setup=True
        ):
            # Запускаем скрипт сборки брендинга и завершаем текущий скрипт
            print_make_message(f"Запуск скрипта брендинга...", Colors.MAGENTA, require_setup=True)
            base.cmd_in_dir(branding_dir + "/build_tools", "python", ["make.py"])
            exit(0)

# После обработки брендинга (или если его нет) парсим значения по умолчанию
# Это нужно потому, что репозиторий брендинга мог быть обновлен
print_make_message("Парсинг значений конфигурации по умолчанию...", Colors.CYAN)
config.parse_defaults()

# Проверяем версию сборки в основном проекте
print_make_message("Проверка версии сборки...", Colors.CYAN)
base.check_build_version(base_dir)

# Если включен режим обновления, обновляем все репозитории проекта
if ("1" == config.option("update")):
    if ask_continue(
        "Обновление всех репозиториев проекта из системы контроля версий (Git)\n"
        "  → Будут обновлены: core, core-ext, desktop, mobile, server и другие\n"
        "  → Время выполнения: 1-5 минут (зависит от количества изменений)\n"
        "  → Можно править: НЕ рекомендуется - изменения могут конфликтовать с обновлением",
        require_setup=True
    ):
        print_make_message("Получение списка репозиториев...", Colors.YELLOW)
        repositories = base.get_repositories()  # Получаем список репозиториев
        print_make_message(f"Найдено репозиториев: {len(repositories)}", Colors.CYAN)
        base.update_repositories(repositories)  # Обновляем их

# Настройка общих приложений, необходимых для сборки
if ask_continue(
    "Настройка общих приложений и утилит для процесса сборки\n"
    "  → Проверяются: qmake, npm, node, git, подписывание сертификаты\n"
    "  → Устанавливаются: зависимости для 3rdParty библиотек\n"
    "  → Время выполнения: 2-10 минут (при первом запуске)\n"
    "  → Можно править: НЕ требуется - это автоматическая настройка окружения"
):
    print_make_message("Настройка общих приложений...", Colors.YELLOW)
    base.configure_common_apps()

# Выполнение задач разработки (компиляция ресурсов, кодогенерация и т.д.)
if ask_continue(
    "Выполнение задач разработки: компиляция ресурсов, кодогенерация и подготовительные операции\n"
    "  → Компилируются: .qrc файлы, .ts файлы переводов\n"
    "  → Генерируются: иконки, стили, заголовочные файлы\n"
    "  → Время выполнения: 3-15 минут\n"
    "  → Можно править: файлы ресурсов (.qrc, .ts, .svg) до этого шага\n"
    "  → ПРЕДУПРЕЖДЕНИЕ: После этого шага править сгенерированные файлы НЕ имеет смысла!"
):
    print_make_message("Запуск задач разработки...", Colors.YELLOW)
    develop.make()

# Проверка флага сборки только JavaScript компонентов
# Если установлен - собираем JS и завершаем скрипт
if ("1" == base.get_env("OO_ONLY_BUILD_JS")):
    if ask_continue(
        "Сборка только JavaScript компонентов (режим OO_ONLY_BUILD_JS)\n"
        "  → Будут собраны: редакторы документов (Document, Spreadsheet, Presentation)\n"
        "  → Время выполнения: 10-45 минут\n"
        "  → Можно править: .js, .json, .html файлы в SDKJS до этого шага\n"
        "  → ПРЕДУПРЕЖДЕНИЕ: После сборки изменения в JS потребуют повторной сборки!"
    ):
        print_make_message("Сборка JavaScript компонентов...", Colors.YELLOW)
        build_js.make()
        exit(0)

# Закомментированная проверка инструментов сборки
#base.check_tools()

# Сборка общих компонентов и сторонних зависимостей (3rdParty)
if ask_continue(
    "Сборка общих компонентов и сторонних зависимостей (3rdParty libraries)\n"
    "  → Будут собраны: библиотеки core_common (kernel, network, graphics)\n"
    "  → Время выполнения: 15-40 минут (при первой сборке)\n"
    "  → Можно править: CMakeLists.txt, configure.py в core_common/\n"
    "  → ПОСЛЕ ЭТОГО: Начнется долгая компиляция C++ проектов (30-90 минут)!\n"
    "  → Важно: Любые изменения в core_common после этого потребуют ПОВТОРНОЙ сборки!"
):
    print_make_message("Сборка общих компонентов и зависимостей...", Colors.YELLOW)
    make_common.make()

# Настройка параметров для сборки десктопной версии
if config.check_option("module", "desktop"):
    # Добавляем URL для веб-приложений помощи с версией продукта
    product_version = base.get_env('PRODUCT_VERSION')
    help_url = f"https://download.onlyoffice.com/install/desktop/editors/help/v {product_version}/apps"
    print_make_message(f"Настройка URL для веб-приложений помощи: {help_url}", Colors.CYAN)
    config.extend_option("qmake_addon", f"URL_WEBAPPS_HELP={help_url}")

    # Дополнительные настройки специфичные для Windows платформы
    if "windows" == base.host_platform():
        if ask_continue(
            "Настройка параметров для Windows-версии десктопного приложения\n"
            "  → Настройки: обновления, каналы дистрибуции\n"
            "  → URL: appcast.json, online installer\n"
            "  → Время выполнения: мгновенно\n"
            "  → Можно править: НЕ рекомендуется - это конфигурация релизной инфраструктуры"
        ):
            print_make_message("Настройка Windows-специфичных параметров...", Colors.YELLOW)
            # Добавляем конфигурацию для модуля обновлений
            config.extend_option("config", "updmodule")
            # Устанавливаем URL для каналов обновлений десктопного приложения
            base.set_env("DESKTOP_URL_UPDATES_MAIN_CHANNEL", "https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/appcast.json ")
            base.set_env("DESKTOP_URL_UPDATES_DEV_CHANNEL",  "https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/appcastdev.json ")
            base.set_env("DESKTOP_URL_INSTALL_CHANNEL",      "https://download.onlyoffice.com/install/desktop/editors/windows/distrib/onlyoffice/ <file>")
            base.set_env("DESKTOP_URL_INSTALL_DEV_CHANNEL",  "https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/onlineinstallerdev/ <file>")

# ПОСЛЕДНЯЯ ВОЗМОЖНОСТЬ внести изменения в C++ код!
if ask_continue(
    f"{'='*60}\n"
    "ПОСЛЕДНЯЯ ВОЗМОЖНОСТЬ внести изменения в C++ код!\n"
    "После подтверждения начнется компиляция, которая займет ОЧЕНЬ много времени\n"
    f"{'='*60}\n"
    "Что можно править:\n"
    "  → core/           (ядро приложения)\n"
    "  → desktop/        (десктопная версия)\n"
    "  → libcfc/         (криптография)\n"
    "  → ooxml/          (OOXML форматы)\n"
    "  → UnicodeConverter/ (конвертация кодировок)\n"
    "Время выполнения: 30-90 минут (в зависимости от платформы и модуля)\n"
    "Важно: Любые изменения в C++ коде ПОСЛЕ этого шага потребуют полной перекомпиляции!",
    require_setup=True
):
    pass  # Пауза для внесения правок

# Основной этап сборки - компиляция решений (C++ проектов, .sln файлов)
if ask_continue(
    "Основная сборка: компиляция решений (C++ проекты, .sln файлы)\n"
    "  → Компилируются: core, desktop, server, мобильные модули\n"
    "  → Используется: Visual Studio (Windows), GCC/Clang (Linux/Mac)\n"
    "  → Время выполнения: 30-90 минут (!)\n"
    "  → Можно править: НИЧЕГО - изменения не будут учтены без пересборки!"
):
    print_make_message("Запуск основной сборки решений...", Colors.YELLOW)
    build_sln.make()

# Сборка JavaScript компонентов (вероятно, веб-редакторы)
if ask_continue(
    "Сборка JavaScript компонентов (веб-редакторы и фронтенд приложения)\n"
    "  → Будут собраны: docbuilder, web-apps, sdkjs\n"
    "  → Используется: npm, webpack, grunt\n"
    "  → Время выполнения: 10-45 минут\n"
    "  → Можно править: локальные .js файлы в SDKJS/ (но придется пересобирать)"
):
    print_make_message("Сборка JavaScript компонентов...", Colors.YELLOW)
    build_js.make()

# Сборка серверной части
if ask_continue(
    "Сборка серверной части и бэкенд компонентов\n"
    "  → Будут собраны: DocService, FileConverter, SpellChecker\n"
    "  → Время выполнения: 5-15 минут\n"
    "  → Можно править: файлы конфигурации сервера после сборки (в deploy/)"
):
    print_make_message("Сборка серверной части...", Colors.YELLOW)
    build_server.make()

# Финальный этап - деплой собранных артефактов (упаковка, создание установщиков и т.д.)
if ask_continue(
    "Финальный деплой: упаковка собранных артефактов, создание установщиков и дистрибутивов\n"
    "  → Создаются: .exe, .dmg, .deb, .rpm пакеты\n"
    "  → Время выполнения: 10-30 минут\n"
    "  → Можно править: файлы лицензий, README, скрипты установки в deploy/\n"
    "  → Результат: готовые дистрибутивы в out/"
):
    print_make_message("Запуск деплоя...", Colors.YELLOW)
    deploy.make()

print_make_message("{'='*60}", Colors.GREEN)
print_make_message("СБОРКА УСПЕШНО ЗАВЕРШЕНА!", Colors.GREEN + Colors.BOLD)
print_make_message("{'='*60}", Colors.GREEN)
print_make_message("Все этапы сборки выполнены успешно!", Colors.GREEN)
print_make_message(f"Результат находится в: {base_dir}/out/", Colors.CYAN)
