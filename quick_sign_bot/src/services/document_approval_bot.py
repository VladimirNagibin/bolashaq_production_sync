import os

# import asyncio
from datetime import datetime
from typing import Any

# from typing import Optional, Dict, Union
from telegram import (  # ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode  # ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from core.logger import logger
from core.settings import settings

# from database import Database
# from api_server import api_server


# Состояния для ConversationHandler
SEND_DOCUMENT, WAIT_COMMENT = range(2)


class DocumentApprovalBot:
    def __init__(self) -> None:
        self.application = (
            Application.builder().token(settings.BOT_TOKEN).build()
        )
        self.setup_handlers()

        # Устанавливаем ссылку на бота в API сервере
        # api_server.set_bot_instance(self)

    def setup_handlers(self) -> None:
        """Настройка обработчиков"""

        # Conversation для отправки документов
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                SEND_DOCUMENT: [
                    MessageHandler(
                        filters.Document.ALL, self.receive_document
                    ),
                    MessageHandler(filters.PHOTO, self.receive_photo),
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.receive_text_document,
                    ),
                ],
                WAIT_COMMENT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, self.receive_comment
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel_command),
                CommandHandler("help", self.help_command),
            ],
            allow_reentry=True,
        )

        # Обработчики команд
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(
            CommandHandler("status", self.status_command)
        )
        self.application.add_handler(
            CommandHandler("pending", self.pending_command)
        )
        self.application.add_handler(
            CommandHandler("my_docs", self.my_documents_command)
        )
        self.application.add_handler(
            CommandHandler("api_info", self.api_info_command)
        )

        # Обработчики сообщений
        self.application.add_handler(conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.button_handler))

        # Обработчик документов вне диалога
        self.application.add_handler(
            MessageHandler(
                filters.Document.ALL | filters.PHOTO,
                self.handle_document_outside_conversation,
            )
        )

        # Обработка текстовых сообщений
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, self.handle_text_message
            )
        )

    async def send_document_to_approvers(
        self,
        document: str | InputFile,
        doc_id: int,
        sender_name: str,
        file_name: str | None = None,
    ) -> None:
        """
        Отправка документа всем согласующим

        Args:
            document: file_id (str) или InputFile
            doc_id: ID документа в базе
            sender_name: имя отправителя
            file_name: имя файла (опционально)

        Returns:
            Количество успешно отправленных согласующим
        """
        approver_id = settings.APPROVER_ID
        try:
            # Создаем клавиатуру для согласования
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Подтвердить", callback_data=f"approve_{doc_id}"
                    ),
                    InlineKeyboardButton(
                        "Отклонить", callback_data=f"reject_{doc_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "С комментарием", callback_data=f"comment_{doc_id}"
                    )
                ],
            ]

            # Отправляем документ
            if isinstance(document, InputFile):
                # Отправляем файл из bytes
                message = await self.application.bot.send_document(
                    chat_id=approver_id,
                    document=document,
                    caption=(
                        f"Документ на согласование\n"
                        f"ID: #{doc_id}\n"
                        f"От: {sender_name}\n"
                        f"Файл: {file_name or 'Без названия'}\n"
                        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML,
                )
            else:
                # Отправляем по file_id
                message = await self.application.bot.send_document(
                    chat_id=approver_id,
                    document=document,
                    caption=(
                        f"Документ на согласование\n"
                        f"ID: #{doc_id}\n"
                        f"От: {sender_name}\n"
                        f"Файл: {file_name or 'Без названия'}\n"
                        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML,
                )
                print(message.message_id)
            # Логируем отправку
            # db.add_approver_sent(
            #     doc_id=doc_id,
            #     approver_id=approver_id,
            #     message_id=message.message_id
            # )

            logger.info(
                f"Документ #{doc_id} отправлен согласующему {approver_id}"
            )

        except Exception as e:
            logger.error(f"Ошибка отправки согласующему {approver_id}: {e}")

    async def receive_document(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int | None:
        """Прием документа от пользователя через Telegram"""
        try:
            # user = update.effective_user
            if not update.message:
                return None

            document = update.message.document

            if not document:
                return None

            # Проверка типа файла
            file_ext = (
                os.path.splitext(document.file_name)[1].lower()
                if document.file_name
                else ""
            )
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                await update.message.reply_text(
                    f"Формат {file_ext} не поддерживается.\n"
                    "Допустимые форматы: "
                    f"{', '.join(settings.ALLOWED_EXTENSIONS)}"
                )
                return SEND_DOCUMENT

            # Проверка размера
            if (
                document.file_size
                and document.file_size > settings.MAX_FILE_SIZE
            ):
                await update.message.reply_text(
                    f"Файл слишком большой.\n"
                    "Максимальный размер: "
                    f"{settings.MAX_FILE_SIZE // 1024 // 1024} MB"
                )
                return SEND_DOCUMENT

            # Уведомляем о начале обработки
            await update.message.reply_text(
                "Отправляю документ на согласование..."
            )

            # Получаем информацию о файле
            # file_info = {
            #     "file_id": document.file_id,
            #     "file_name": document.file_name or "Без названия",
            #     "file_type": document.mime_type,
            #     "file_size": document.file_size,
            #     "sender_id": user.id,
            #     "sender_name": user.full_name,
            #     "sender_username": user.username,
            #     "chat_id": update.effective_chat.id,
            #     "message_id": update.message.message_id,
            # }

            # Сохраняем в базу
            # doc_id = db.add_document(file_info)

            # Отправляем согласующим
            # sent_count = await self.send_document_to_approvers(
            #     document=document.file_id,
            #     doc_id=doc_id,
            #     sender_name=user.full_name,
            #     file_name=document.file_name,
            # )

            # if sent_count > 0:
            #     await update.message.reply_text(
            #         f"Документ отправлен {sent_count} согласующим(им).\n"
            #         f"ID документа: #{doc_id}\n\n"
            #         "Ожидайте решения."
            #     )
            # else:
            #     await update.message.reply_text(
            #         "Не удалось отправить документ согласующим.\n"
            #         "Попробуйте позже или свяжитесь с администратором."
            #     )

            return ConversationHandler.END  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            await update.message.reply_text(
                "Произошла ошибка при обработке документа.\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
            return ConversationHandler.END  # type: ignore[no-any-return]

    async def api_info_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Информация об API"""
        user = update.effective_user

        if user.id != settings.ADMIN_ID:
            await update.message.reply_text(
                "Эта команда только для администратора."
            )
            return

        api_url = f"http://{settings.APP_HOST}:{settings.APP_PORT}"

        info_text = (
            f"*Информация об API*\n\n"
            f"URL: `{api_url}`\n"
            f"API Key: `{settings.API_SECRET_KEY}`\n"
            f"Upload folder: `{settings.UPLOAD_FOLDER}`\n\n"
            f"*Доступные эндпоинты:*\n"
            f"• `POST /api/v1/documents/upload` - загрузка документа\n"
            f"• `GET /api/v1/documents/{'{id}'}` - статус документа\n"
            f"• `GET /api/v1/documents` - список документов\n"
            f"• `POST /api/v1/webhook/decision` - webhook для решений\n\n"
            f"*Пример curl для загрузки:*\n"
            f"```bash\n"
            f"curl -X POST {api_url}/api/v1/documents/upload \\\n"
            f"  -H 'X-API-Key: {settings.API_SECRET_KEY}' \\\n"
            f"  -F 'file=@document.pdf' \\\n"
            f"  -F 'sender_name=API User' \\\n"
            f"  -F 'description=Документ из API'\n"
            f"```"
        )

        await update.message.reply_text(
            info_text, parse_mode=ParseMode.MARKDOWN
        )

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Обработка команды /start"""
        user = update.effective_user

        # Логируем пользователя
        # db.log_user(user.id, user.username, user.full_name)

        await update.message.reply_text(
            f"Привет, {user.first_name}!\n\n"
            "Я бот для отправки документов на согласование.\n"
            "Чтобы отправить документ, просто отправьте его мне.\n\n"
            "Доступные команды:\n"
            "/start - начать работу\n"
            "/help - помощь\n"
            "/status - статус ваших документов\n"
            "/my_docs - мои документы\n"
            "/cancel - отмена текущего действия\n\n"
            "Для согласующих:\n"
            "/pending - документы на согласование",
            reply_markup=ReplyKeyboardRemove(),
        )
        return SEND_DOCUMENT

    async def send_to_approvers(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        document: Any,
        doc_id: int,
        sender_name: str,
    ) -> int:
        """Отправка документа всем согласующим"""
        sent_count = 0

        approver_id = settings.APPROVER_ID
        try:
            # Создаем клавиатуру для согласования
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Подтвердить", callback_data=f"approve_{doc_id}"
                    ),
                    InlineKeyboardButton(
                        "Отклонить", callback_data=f"reject_{doc_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "С комментарием", callback_data=f"comment_{doc_id}"
                    )
                ],
            ]

            # Отправляем документ
            message = await context.bot.send_document(
                chat_id=approver_id,
                document=document.file_id,
                # caption=(
                #      f"Документ на согласование\n"
                #     f"ID: #{doc_id}\n"
                #     f"От: {sender_name}\n"
                #     f"Файл: {document.file_name or 'Без названия'}\n"
                #     f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                # ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML,
            )

            # Логируем отправку
            # db.add_approver_sent(
            #     doc_id=doc_id,
            #     approver_id=approver_id,
            message_id = message.message_id
            # )

            sent_count += 1
            logger.info(
                f"Документ #{doc_id} отправлен согласующему {approver_id} "
                f"message_id: {message_id}"
            )

        except Exception as e:
            logger.error(f"Ошибка отправки согласующему {approver_id}: {e}")

        return sent_count

    async def button_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Обработка нажатий inline-кнопок"""
        query = update.callback_query
        await query.answer()

        user = query.from_user

        # Проверяем, является ли пользователь согласующим
        if user.id != settings.APPROVER_ID:
            await query.edit_message_text(
                "У вас нет прав для согласования документов."
            )
            return

        # Парсим данные callback
        data = query.data

        if data.startswith("approve_"):
            doc_id = int(data.split("_")[1])
            await self.approve_document(update, context, doc_id)

        elif data.startswith("reject_"):
            doc_id = int(data.split("_")[1])
            await self.reject_document(update, context, doc_id)

        elif data.startswith("comment_"):
            doc_id = int(data.split("_")[1])
            await self.request_comment(update, context, doc_id)

    async def approve_document(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, doc_id: int
    ) -> None:
        """Подтверждение документа"""
        query = update.callback_query
        user = query.from_user

        # Получаем документ из базы
        # document = db.get_document(doc_id)
        # if not document:
        #     await query.edit_message_text("Документ не найден.")
        #     return

        # # Обновляем статус в базе
        # db.update_document_status(
        #     doc_id=doc_id,
        #     status='approved',
        #     approver_data={
        #         'id': user.id,
        #         'name': user.full_name,
        #         'username': user.username
        #     }
        # )

        # Уведомляем отправителя
        try:
            ...
            # await context.bot.send_message(
            #     chat_id=document['sender_id'],
            #     text=(
            #         f"Ваш документ подтвержден!\n"
            #         f"ID: #{doc_id}\n"
            #         f"Файл: {document['file_name']}\n"
            #         f"Согласующий: {user.full_name}\n"
            #         f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            #     )
            # )
        except Exception as e:
            logger.error(f"Не удалось уведомить отправителя: {e}")

        # Обновляем сообщение у согласующего
        await query.edit_message_caption(
            caption=(
                f"Документ подтвержден\n"
                f"ID: #{doc_id}\n"
                f"Согласующий: {user.full_name}\n"
                f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            ),
            reply_markup=None,
        )

        logger.info(f"Документ #{doc_id} подтвержден пользователем {user.id}")

    async def reject_document(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, doc_id: int
    ) -> Any:
        """Отклонение документа"""
        query = update.callback_query
        # user = query.from_user

        # Получаем документ из базы
        # document = db.get_document(doc_id)
        # if not document:
        #     await query.edit_message_text("Документ не найден.")
        #     return

        # # Сохраняем ID документа для комментария
        # context.user_data['reject_doc_id'] = doc_id
        # context.user_data['reject_doc_info'] = document
        # context.user_data['reject_approver'] = {
        #     'id': user.id,
        #     'name': user.full_name,
        #     'username': user.username
        # }

        # Запрашиваем комментарий
        await query.message.reply_text(
            "Пожалуйста, укажите причину отклонения:"
        )

        return WAIT_COMMENT

    async def request_comment(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, doc_id: int
    ) -> Any:
        """Запрос комментария к решению"""
        query = update.callback_query
        # user = query.from_user

        # Получаем документ из базы
        # document = db.get_document(doc_id)
        # if not document:
        #     await query.edit_message_text("Документ не найден.")
        #     return

        # # Сохраняем данные для комментария
        # context.user_data['comment_doc_id'] = doc_id
        # context.user_data['comment_doc_info'] = document
        # context.user_data['comment_approver'] = {
        #     'id': user.id,
        #     'name': user.full_name,
        #     'username': user.username
        # }

        # Создаем клавиатуру для выбора действия после комментария
        keyboard = [
            [
                InlineKeyboardButton(
                    "Подтвердить с комментарием",
                    callback_data=f"approve_comment_{doc_id}",
                ),
                InlineKeyboardButton(
                    "Отклонить с комментарием",
                    callback_data=f"reject_comment_{doc_id}",
                ),
            ]
        ]

        # Обновляем сообщение
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Запрашиваем комментарий
        await query.message.reply_text("Пожалуйста, введите ваш комментарий:")

        return WAIT_COMMENT

    async def receive_comment(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Прием комментария"""
        comment = update.message.text
        # user = update.effective_user

        # Проверяем, для какого действия комментарий
        if "reject_doc_id" in context.user_data:
            # Комментарий для отклонения
            doc_id = context.user_data["reject_doc_id"]
            document = context.user_data["reject_doc_info"]
            approver_data = context.user_data["reject_approver"]

            # Обновляем статус с комментарием
            # db.update_document_status(
            #     doc_id=doc_id,
            #     status='rejected',
            #     approver_data=approver_data,
            #     comment=comment
            # )

            # Уведомляем отправителя
            try:
                await context.bot.send_message(
                    chat_id=document["sender_id"],
                    text=(
                        f"Ваш документ отклонен\n"
                        f"ID: #{doc_id}\n"
                        f"Файл: {document['file_name']}\n"
                        f"Согласующий: {approver_data['name']}\n"
                        f"Комментарий: {comment}\n"
                        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    ),
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить отправителя: {e}")

            await update.message.reply_text(
                "Комментарий сохранен, отправитель уведомлен."
            )

            # Очищаем временные данные
            context.user_data.clear()

        elif "comment_doc_id" in context.user_data:
            # Комментарий для последующего решения
            context.user_data["pending_comment"] = comment
            await update.message.reply_text(
                "Комментарий сохранен. Теперь выберите действие выше."
            )

        return ConversationHandler.END

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Показ статуса документов"""
        # user = update.effective_user

        # Получаем документы пользователя
        # documents = db.get_user_documents(user.id)

        # if not documents:
        #     await update.message.reply_text(
        #         "У вас пока нет отправленных документов."
        #     )
        #     return

        # Формируем сообщение
        # message_lines = ["Ваши документы:\n"]

        # for doc in documents[:10]:  # Ограничиваем 10 документами
        #     status_emoji = {
        #         "pending": "pending",
        #         "approved": "approved",
        #         "rejected": "rejected",
        #     }.get(doc["status"], "")

        #     line = (
        #         f"{status_emoji} Документ #{doc['id']}\n"
        #         f"{doc['file_name']}\n"
        #         f"{doc['created_at']}\n"
        #         f"Статус: {doc['status']}\n"
        #     )

        #     if doc["comment"]:
        #         line += f"Комментарий: {doc['comment'][:50]}...\n"

        #     message_lines.append(line + "─" * 30 + "\n")

        # await update.message.reply_text("".join(message_lines)[:4000])

    async def pending_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Показ документов на согласование (для согласующих)"""
        user = update.effective_user

        if user.id != settings.APPROVER_ID:
            await update.message.reply_text(
                "У вас нет прав для просмотра документов на согласование."
            )
            return

        # Получаем ожидающие документы
        # documents = db.get_pending_documents()

        # if not documents:
        #     await update.message.reply_text(
        #         "Нет документов, ожидающих согласования."
        #     )
        #     return

        # await update.message.reply_text(
        #     f"Документов на согласование: {len(documents)}\n"
        #     "Для согласования перейдите в чат с ботом."
        # )

    async def my_documents_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Команда для просмотра своих документов"""
        return await self.status_command(update, context)

    async def cancel_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Отмена текущего действия"""
        await update.message.reply_text(
            "Действие отменено.", reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Помощь"""
        help_text = """
*Руководство по использованию бота*

*Основные команды:*
/start - начать работу с ботом
/help - показать это сообщение
/status - статус ваших документов
/my_docs - мои документы (аналогично /status)
/cancel - отменить текущее действие

*Для согласующих:*
/pending - показать количество документов на согласование

*Как отправить документ:*
1. Нажмите /start или просто отправьте документ
2. Отправьте файл боту (поддерживаются PDF, DOC, DOCX, XLS, XLSX, JPG, PNG)
3. Документ будет отправлен всем согласующим
4. Вы получите уведомление о решении

*Процесс согласования:*
1. Согласующий получает документ с кнопками
2. Возможные действия:
   - Подтвердить - сразу подтвердить
   - Отклонить - отклонить с указанием причины
   - С комментарием - добавить комментарий перед решением

*Поддерживаемые форматы:*
- Документы: PDF, DOC, DOCX, XLS, XLSX, TXT
- Изображения: JPG, JPEG, PNG
- Максимальный размер: 50 MB
        """

        await update.message.reply_text(
            help_text, parse_mode=ParseMode.MARKDOWN
        )

    async def handle_document_outside_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Обработка документа вне диалога"""
        return await self.receive_document(update, context)

    async def receive_photo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Прием фото"""
        # Обрабатываем как документ
        return await self.receive_document(update, context)

    async def receive_text_document(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Any:
        """Прием текстового сообщения в состоянии отправки документа"""
        await update.message.reply_text(
            "Пожалуйста, отправьте документ для согласования.\n"
            "Или нажмите /cancel для отмены."
        )
        return SEND_DOCUMENT

    async def handle_text_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Обработка текстовых сообщений вне диалога"""
        await update.message.reply_text(
            "Для отправки документа на согласование просто отправьте его мне."
            "\nИли используйте команду /help для справки."
        )

    def run(self) -> None:
        """Запуск бота"""
        logger.info("Запуск бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
