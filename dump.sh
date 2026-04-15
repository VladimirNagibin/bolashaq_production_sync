#!/bin/bash
set -e

cd "$(dirname "$0")"

# Загрузка .env
if [ -f .env ]; then
    set -a; source .env; set +a
else
    echo ".env not found"
    exit 1
fi

# Переменные
FILENAME="dump-$(date +"%Y-%m-%d").sql.gz"
FILEPATH="/home/user_bolashaq/bolashaq_sync/$FILENAME"
TMP_DIR="/dev/shm"  # или другой быстрый временный каталог (tmpfs)
# EMAIL=bitrix.bob@yandex.ru

# 1. Создаём сжатый дамп без промежуточного SQL-файла
echo "Creating compressed dump..."
sudo docker exec -i bolashaq_sync-db-1 /bin/bash -c \
    "PGPASSWORD=$POSTGRES_PASSWORD pg_dump --username $POSTGRES_USER $POSTGRES_DB" \
    | gzip -9 > "$FILEPATH"

# Проверка размера
if [ ! -s "$FILEPATH" ]; then
    echo "Dump file is empty, aborting"
    exit 1
fi

# 2. Отправка файла на Яндекс.Диск
sendFile() {
    local file="$1"
    echo "Start sending: $file"

    # Получаем URL для загрузки
    response=$(curl -s -H "Authorization: OAuth $TOKEN_YANDEX_DISK" \
        "https://cloud-api.yandex.net/v1/disk/resources/upload/?path=app:/$FILENAME&overwrite=true")

    # Извлекаем href с помощью jq (надёжно)
    if ! command -v jq &> /dev/null; then
        echo "jq is not installed, please run: sudo apt install jq -y"
        exit 1
    fi
    upload_url=$(echo "$response" | jq -r '.href')

    if [ -z "$upload_url" ] || [ "$upload_url" = "null" ]; then
        echo "Failed to get upload URL. API response: $response"
        exit 1
    fi

    # Загружаем файл с повышенными таймаутами
    curl -T "$file" -H "Authorization: OAuth $TOKEN_YANDEX_DISK" \
        --connect-timeout 60 --max-time 3600 \
        "$upload_url"

    echo "Upload completed: $file"
}

sendFile "$FILEPATH"

# 3. Очистка
rm "$FILEPATH"
echo "All done."

# crontab -e - Откройте crontab для редактирования
# Запланировать выполнение скрипта каждый день в 22:00
# 0 22 * * *  /home/user_bolashaq/bolashaq_sync/dump.sh  >> /home/user_bolashaq/bolashaq_sync/dump.log 2>&1
# crontab -l - Проверьте, что задание добавилось
