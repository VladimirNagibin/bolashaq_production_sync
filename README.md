# bitrix_production_sync
Bitrix24 processing.

## Запуск одного профиля
docker compose --profile migrate up

## Начальная авторизация
настроить BITRIX_REDIRECT_URI в .env
установить путь вашего обработчика в приложении в Битрикс
запустить запрос к Битрикс24
авторизоваться по ссылке из сообщения об исключении
