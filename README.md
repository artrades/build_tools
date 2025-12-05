# build_tools

## Обзор

**build_tools** позволяют автоматически получить и установить все компоненты, необходимые для процесса компиляции, все зависимости, требуемые для корректной работы **ONLYOFFICE Document Server**, **Document Builder** и **Desktop Editors**, а также получить последнюю версию исходного кода **продуктов ONLYOFFICE** и собрать все их компоненты.

**Важно!** Мы можем гарантировать корректную работу только продуктов, собранных из ветки `master`.

## Как использовать - Linux

**Примечание**: Решение было протестировано на **Ubuntu 14.04**.

### Установка зависимостей

Вам может потребоваться установить **Python** в зависимости от вашей версии Ubuntu:

```bash
sudo apt-get install -y python
```

### Сборка исходного кода продуктов ONLYOFFICE

1. Клонируйте репозиторий build_tools:

    ```bash
    git clone https://github.com/ONLYOFFICE/build_tools.git
    ```

2. Перейдите в директорию `build_tools/tools/linux`:

    ```bash
    cd build_tools/tools/linux
    ```

3. Запустите скрипт `automate.py`:

    ```bash
    ./automate.py
    ```

Если запустить скрипт без параметров, это позволит собрать **ONLYOFFICE Document Server**, **Document Builder** и **Desktop Editors**.

Результат будет доступен в директории `./out`.

Чтобы собрать продукты **ONLYOFFICE** отдельно, запустите скрипт с параметром, соответствующим необходимому продукту.

Также возможно собрать несколько продуктов одновременно, как показано в примере ниже.

**Пример**: Сборка **Desktop Editors** и **Document Server**

```bash
./automate.py desktop server
```

### Использование Docker

Вы также можете собрать все **продукты ONLYOFFICE** одновременно с помощью Docker.
Соберите Docker-образ `onlyoffice-document-editors-builder` с использованием предоставленного `Dockerfile` и запустите соответствующий Docker-контейнер.

```bash
mkdir out
docker build --tag onlyoffice-document-editors-builder .
docker run -v $PWD/out:/build_tools/out onlyoffice-document-editors-builder
```

Результат будет доступен в директории `./out`.

### Сборка и запуск продуктов ONLYOFFICE отдельно

#### Document Builder

##### Сборка Document Builder

```bash
./automate.py builder
```

##### Запуск Document Builder

```bash
cd ../../out/linux_64/onlyoffice/documentbuilder
./docbuilder
```

#### Desktop Editors

##### Сборка Desktop Editors

```bash
./automate.py desktop
```

##### Запуск Desktop Editors

```bash
cd ../../out/linux_64/onlyoffice/desktopeditors
LD_LIBRARY_PATH=./ ./DesktopEditors
```

#### Document Server

##### Сборка Document Server

```bash
./automate.py server
```

##### Установка и настройка зависимостей Document Server

**Document Server** использует **NGINX** в качестве веб-сервера и **PostgreSQL** в качестве базы данных.
**RabbitMQ** также требуется для корректной работы **Document Server**.

###### Установка и настройка NGINX

1. Установите NGINX:

    ```bash
    sudo apt-get install nginx
    ```

2. Отключите сайт по умолчанию:

    ```bash
    sudo rm -f /etc/nginx/sites-enabled/default
    ```

3. Настройте новый сайт. Для этого создайте файл `/etc/nginx/sites-available/onlyoffice-documentserver` со следующим содержимым:

    ```bash
    map $http_host $this_host {
      "" $host;
      default $http_host;
    }
    map $http_x_forwarded_proto $the_scheme {
      default $http_x_forwarded_proto;
      "" $scheme;
    }
    map $http_x_forwarded_host $the_host {
      default $http_x_forwarded_host;
      "" $this_host;
    }
    map $http_upgrade $proxy_connection {
      default upgrade;
      "" close;
    }
    proxy_set_header Host $http_host;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $proxy_connection;
    proxy_set_header X-Forwarded-Host $the_host;
    proxy_set_header X-Forwarded-Proto $the_scheme;
    server {
      listen 0.0.0.0:80;
      listen [::]:80 default_server;
      server_tokens off;
      rewrite ^\/OfficeWeb(\/apps\/.*)$ /web-apps$1 redirect;
      location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
      }
    }
    ```

4. Добавьте символьную ссылку на вновь созданный сайт в директорию `/etc/nginx/sites-available`:

    ```bash
    sudo ln -s /etc/nginx/sites-available/onlyoffice-documentserver /etc/nginx/sites-enabled/onlyoffice-documentserver
    ```

5. Перезапустите NGINX для применения изменений:

    ```bash
    sudo nginx -s reload
    ```

###### Установка и настройка PostgreSQL

1. Установите PostgreSQL:

    ```bash
    sudo apt-get install postgresql
    ```

2. Создайте базу данных PostgreSQL и пользователя:

    **Примечание**: Созданная база данных должна иметь **onlyoffice** как для пользователя, так и для пароля.

    ```bash
    sudo -i -u postgres psql -c "CREATE DATABASE onlyoffice;"
    sudo -i -u postgres psql -c "CREATE USER onlyoffice WITH password 'onlyoffice';"
    sudo -i -u postgres psql -c "GRANT ALL privileges ON DATABASE onlyoffice TO onlyoffice;"
    ```

3. Настройте базу данных:

    ```bash
    psql -hlocalhost -Uonlyoffice -d onlyoffice -f ../../out/linux_64/onlyoffice/documentserver/server/schema/postgresql/createdb.sql
    ```

**Примечание**: После этого вам будет предложено ввести пароль для пользователя PostgreSQL **onlyoffice**. Пожалуйста, введите пароль **onlyoffice**.

###### Установка RabbitMQ

```bash
sudo apt-get install rabbitmq-server
```

###### Генерация данных о шрифтах

```bash
cd out/linux_64/onlyoffice/documentserver/
mkdir fonts
LD_LIBRARY_PATH=${PWD}/server/FileConverter/bin server/tools/allfontsgen \
  --input="${PWD}/core-fonts" \
  --allfonts-web="${PWD}/sdkjs/common/AllFonts.js" \
  --allfonts="${PWD}/server/FileConverter/bin/AllFonts.js" \
  --images="${PWD}/sdkjs/common/Images" \
  --selection="${PWD}/server/FileConverter/bin/font_selection.bin" \
  --output-web='fonts' \
  --use-system="true"
```

###### Генерация тем презентаций

```bash
cd out/linux_64/onlyoffice/documentserver/
LD_LIBRARY_PATH=${PWD}/server/FileConverter/bin server/tools/allthemesgen \
  --converter-dir="${PWD}/server/FileConverter/bin"\
  --src="${PWD}/sdkjs/slide/themes"\
  --output="${PWD}/sdkjs/common/Images"
```

##### Запуск Document Server

**Примечание**: Все компоненты **Document Server** запускаются как процессы переднего плана. Таким образом, вам нужны отдельные терминальные консоли для их запуска или специальные инструменты, которые позволят запускать процессы переднего плана в фоновом режиме.

1. Запустите службу **FileConverter**:

    ```bash
    cd out/linux_64/onlyoffice/documentserver/server/FileConverter
    LD_LIBRARY_PATH=$PWD/bin \
    NODE_ENV=development-linux \
    NODE_CONFIG_DIR=$PWD/../Common/config \
    ./converter
    ```

2. Запустите службу **DocService**:

    ```bash
    cd out/linux_64/onlyoffice/documentserver/server/DocService
    NODE_ENV=development-linux \
    NODE_CONFIG_DIR=$PWD/../Common/config \
    ./docservice
    ```
