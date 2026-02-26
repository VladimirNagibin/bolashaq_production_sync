Добавление нового источника лидов/сделок:
1. В .env.mail добавить в TARGET_SENDER_EMAIL адрес отправителя через ,
2. В schemas/email_schemas.py добавить в TypeEvent новое значение и в EVENT_ROUTING добавить соответствие (тема письма, отправитель):тип события
3. В RequestParserService добавить парсер для нового типа