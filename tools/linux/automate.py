#!/usr/bin/env python

import sys
sys.path.append('../../scripts')

# Выводим текущий Python path
print("=== PYTHON PATH ===")
for path in sys.path:
    print(path)


import base
import os
import subprocess
import deps


# Пробуем импортировать и вывести информацию о модулях
print("\n=== MODULE INFO ===")
try:
    import base
    print("base module found at:", base.__file__)
except ImportError as e:
    print("base import error:", e)

try:
    import deps
    print("deps module found at:", deps.__file__)
except ImportError as e:
    print("deps import error:", e)




# =============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С GIT И УСТАНОВКИ QT
# =============================================================================

def get_branch_name(directory):
    """Получает имя текущей ветки Git в указанной директории"""
    cur_dir = os.getcwd()
    os.chdir(directory)
    # Определяем ветку build_tools
    # command = "git branch --show-current"
    command = "git symbolic-ref --short -q HEAD"
    current_branch = base.run_command(command)['stdout']
    os.chdir(cur_dir)
    return current_branch

def install_qt():
    """Установка Qt из исходников"""
    # Скачивание исходников Qt
    if not base.is_file("./qt_source_5.9.9.tar.xz"):
        base.download("https://download.qt.io/new_archive/qt/5.9/5.9.9/single/qt-everywhere-opensource-src-5.9.9.tar.xz", "./qt_source_5.9.9.tar.xz")
    
    # Распаковка исходников
    if not base.is_dir("./qt-everywhere-opensource-src-5.9.9"):
        base.cmd("tar", ["-xf", "./qt_source_5.9.9.tar.xz"])
    
    # Параметры конфигурации Qt
    qt_params = ["-opensource",
                 "-confirm-license", 
                 "-release",
                 "-shared",
                 "-accessibility",
                 "-prefix",
                 "./../qt_build/Qt-5.9.9/gcc_64",
                 "-qt-zlib",
                 "-qt-libpng", 
                 "-qt-libjpeg",
                 "-qt-xcb",
                 "-qt-pcre",
                 "-no-sql-sqlite",
                 "-no-qml-debug",
                 "-gstreamer", "1.0",
                 "-nomake", "examples",
                 "-nomake", "tests",
                 "-skip", "qtenginio",
                 "-skip", "qtlocation", 
                 "-skip", "qtserialport",
                 "-skip", "qtsensors",
                 "-skip", "qtxmlpatterns",
                 "-skip", "qt3d",
                 "-skip", "qtwebview",
                 "-skip", "qtwebengine"]
    
    # Сборка Qt из исходников
    base.cmd_in_dir("./qt-everywhere-opensource-src-5.9.9", "./configure", qt_params)
    base.cmd_in_dir("./qt-everywhere-opensource-src-5.9.9", "make", ["-j", "4"])
    base.cmd_in_dir("./qt-everywhere-opensource-src-5.9.9", "make", ["install"])
    return

def install_qt_prebuild():
    """Установка предварительно собранной версии Qt"""
    url_amd64 = "https://s3.eu-west-1.amazonaws.com/static-doc.teamlab.eu.com/qt/5.9.9/linux_amd64/qt_binary.7z"
    base.download(url_amd64, "./qt_amd64.7z")
    base.extract("./qt_amd64.7z", "./qt_build")
    base.create_dir("./qt_build/Qt-5.9.9")
    base.cmd("mv", ["./qt_build/qt_amd64", "./qt_build/Qt-5.9.9/gcc_64"])
    base.setup_local_qmake("./qt_build/Qt-5.9.9/gcc_64/bin")
    return

def get_system_info():
    """Получает информацию о системе без использования socket"""
    current_dir = 'unknown'
    username = 'unknown'
    hostname = 'unknown'
    domain = 'local'
    
    try:
        # Получаем текущую директорию
        current_dir = os.getcwd()
    except Exception as e:
        print(f"Ошибка при получении текущей директории: {e}")
        current_dir = 'unknown'
    
    try:
        # Получаем имя пользователя
        username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
    except Exception as e:
        print(f"Ошибка при получении имени пользователя: {e}")
        username = 'unknown'
    
    try:
        # Получаем имя хоста из переменных окружения или файлов системы
        hostname = os.getenv('HOSTNAME') or os.getenv('COMPUTERNAME') or 'unknown'
        
        # Для Linux/Unix систем пробуем прочитать из файла
        try:
            if os.path.exists('/etc/hostname'):
                with open('/etc/hostname', 'r') as f:
                    hostname = f.read().strip()
            elif os.path.exists('/proc/sys/kernel/hostname'):
                with open('/proc/sys/kernel/hostname', 'r') as f:
                    hostname = f.read().strip()
        except Exception as e:
            print(f"Ошибка при чтении файлов hostname: {e}")
            # Оставляем значение из переменных окружения
    except Exception as e:
        print(f"Ошибка при получении имени хоста: {e}")
        hostname = 'unknown'
    
    return current_dir, username, hostname, domain

def red_text(text):
    """Возвращает текст в красном цвете"""
    return f"\033[91m{text}\033[0m"

def wait_for_continue(step_name):
    """Ожидание нажатия клавиши для продолжения"""
    current_dir, username, hostname, domain = get_system_info()
    
    print(f"\n{'='*80}")
    print(f"СИСТЕМНАЯ ИНФОРМАЦИЯ:")
    print(f"  Текущая директория: {current_dir}")
    print(f"  Пользователь: {username}")
    print(f"  Хост: {hostname}")
    print(f"  Домен: {domain}")
    print(f"{'='*80}")
    print(red_text(f"ЭТАП: {step_name}"))
    print(f"{'='*80}")
    input("Нажмите любую клавишу для продолжения...")
    print()

# =============================================================================
# ЭТАП 1: ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ
# =============================================================================

wait_for_continue("ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ")
print("Проверяем наличие установленных зависимостей (Node.js и другие)...")

if not base.is_file("./node_js_setup_14.x"):
    print("Зависимости не найдены. Устанавливаем...")
    deps.install_deps()  # Установка Node.js и других зависимостей
else:
    print("Зависимости уже установлены. Пропускаем установку.")

# =============================================================================
# ЭТАП 2: УСТАНОВКА QT
# =============================================================================

wait_for_continue("УСТАНОВКА QT")
print("Проверяем наличие установленного Qt...")

if not base.is_dir("./qt_build"):
    print("Qt не найден. Устанавливаем предварительно собранную версию Qt...")
    install_qt_prebuild()  # Используем предварительно собранный Qt
    print("Qt успешно установлен.")
else:
    print("Qt уже установлен. Пропускаем установку.")

# =============================================================================
# ЭТАП 3: ОПРЕДЕЛЕНИЕ ВЕТКИ GIT
# =============================================================================

wait_for_continue("ОПРЕДЕЛЕНИЕ ВЕТКИ GIT")
print("Определяем текущую ветку Git проекта...")

branch = get_branch_name("../..")  # Получаем имя текущей ветки
print(f"Текущая ветка: {branch}")

# =============================================================================
# ЭТАП 4: ПАРСИНГ АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ
# =============================================================================

wait_for_continue("ПАРСИНГ АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ")
print("Анализируем переданные аргументы командной строки...")

array_args = sys.argv[1:]
array_modules = []
params = []

config = {}
for arg in array_args:
    if (0 == arg.find("--")):
        indexEq = arg.find("=")
        if (-1 != indexEq):
            # Обрабатываем параметры вида --ключ=значение
            config[arg[2:indexEq]] = arg[indexEq + 1:]
            params.append(arg[:indexEq])
            params.append(arg[indexEq + 1:])
    else:
        array_modules.append(arg)

# Если ветка указана в параметрах - используем её
if ("branch" in config):
    branch = config["branch"]
    print(f"Ветка переопределена через аргументы: {branch}")

print("---------------------------------------------")
print("build branch: " + branch)
print("---------------------------------------------")

# =============================================================================
# ЭТАП 5: ПОДГОТОВКА ПАРАМЕТРОВ ДЛЯ СБОРКИ
# =============================================================================

wait_for_continue("ПОДГОТОВКА ПАРАМЕТРОВ ДЛЯ СБОРКИ")
print("Формируем параметры для системы сборки...")

# Определяем модули для сборки
modules = " ".join(array_modules)
if "" == modules:
    modules = "desktop builder server"  # Модули по умолчанию
    print("Используем модули по умолчанию")

print("---------------------------------------------")
print("build modules: " + modules)
print("---------------------------------------------")

# Формируем параметры для скрипта сборки
build_tools_params = ["--branch", branch, 
                      "--module", modules, 
                      "--update", "1",
                      "--qt-dir", os.getcwd() + "/qt_build/Qt-5.9.9"] + params

print(f"Параметры сборки: {build_tools_params}")

# =============================================================================
# ЭТАП 6: КОНФИГУРАЦИЯ СБОРКИ
# =============================================================================

wait_for_continue("КОНФИГУРАЦИЯ СБОРКИ")
print("Запускаем скрипт конфигурации сборки...")
print("configure.py настраивает переменные окружения, пути и параметры компиляции")

# Запускаем скрипт конфигурации с подготовленными параметрами
base.cmd_in_dir("../..", "./configure.py", build_tools_params)
print("Конфигурация завершена успешно!")

# =============================================================================
# ЭТАП 7: НЕПОСРЕДСТВЕННАЯ СБОРКА ПРОЕКТА
# =============================================================================

wait_for_continue("НЕПОСРЕДСТВЕННАЯ СБОРКА ПРОЕКТА")
print("Запускаем компиляцию проекта...")
print("make.py выполняет сборку всех указанных модулей")

# Запускаем непосредственно компиляцию проекта
base.cmd_in_dir("../..", "./make.py")
print("Сборка завершена успешно!")

print("\n" + "="*80)
print(red_text("ВСЕ ЭТАПЫ ЗАВЕРШЕНЫ УСПЕШНО!"))
print("="*80)
