# import asyncio
import json
import os
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import (  # Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.logger import logger
from core.settings import settings

from .document_approval_bot import DocumentApprovalBot

# from database import Database
from .utils import (
    create_upload_folder,
    generate_unique_filename,
    get_file_hash,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
)

# Создаем папку для загрузок
create_upload_folder(settings.UPLOAD_FOLDER)

# Инициализация базы данных
# db = Database(Config.DB_PATH)

# Глобальная ссылка на бота для отправки файлов
bot_instance = None


class DocumentAPIServer:
    def __init__(self) -> None:
        self.app = FastAPI(
            title="Document Approval API",
            description=(
                "API для отправки документов на согласование в Telegram"
            ),
            version="1.0.0",
        )

        # Настройка CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # В продакшене указать конкретные домены
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.setup_routes()

    def setup_routes(self) -> None:
        """Настройка маршрутов API"""

        @self.app.get("/")  # type: ignore[misc]
        async def root() -> dict[str, str]:
            return {
                "service": "Document Approval API",
                "version": "1.0.0",
                "status": "running",
            }

        @self.app.get("/health")  # type: ignore[misc]
        async def health_check() -> dict[str, Any]:
            """Проверка здоровья сервиса"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                # "database": (
                #     "connected" if self.check_db_connection()
                #     else "disconnected"
                # )
            }

        @self.app.post("/api/v1/documents/upload")  # type: ignore[misc]
        async def upload_document(
            file: UploadFile = File(...),
            sender_name: str = Form(None),
            sender_id: int = Form(None),
            description: str = Form(""),
            metadata: str = Form("{}"),
            x_api_key: str = Header(None),
        ) -> JSONResponse:
            """
            Загрузка документа для отправки на согласование

            Параметры:
            - file: файл для отправки
            - sender_name: имя отправителя
            - sender_id: ID отправителя (опционально)
            - description: описание документа
            - metadata: дополнительные метаданные в JSON формате
            - x_api_key: API ключ для авторизации
            """
            try:
                # Проверка API ключа
                if x_api_key != settings.API_SECRET_KEY:
                    raise HTTPException(
                        status_code=403, detail="Invalid API key"
                    )

                # Валидация файла
                filename = sanitize_filename(file.filename)

                # Проверка расширения
                is_valid_ext, ext_error = validate_file_extension(
                    filename, settings.ALLOWED_EXTENSIONS
                )
                if not is_valid_ext:
                    raise HTTPException(status_code=400, detail=ext_error)

                # Проверка размера
                file_content = await file.read()
                file_size = len(file_content)
                is_valid_size, size_error = validate_file_size(
                    file_size, settings.MAX_FILE_SIZE
                )
                if not is_valid_size:
                    raise HTTPException(status_code=400, detail=size_error)

                # Генерация уникального имени файла
                unique_filename = generate_unique_filename(filename)
                file_path = os.path.join(
                    settings.UPLOAD_FOLDER, unique_filename
                )

                # Сохранение файла
                with open(file_path, "wb") as f:
                    f.write(file_content)

                # Вычисление хэша файла
                file_hash = get_file_hash(file_path)

                # Парсинг метаданных
                try:
                    ...
                    # metadata_dict = json.loads(metadata)
                except json.JSONDecodeError:
                    ...
                    # metadata_dict = {}

                # Подготовка данных документа
                # document_data = {
                #     "file_path": file_path,
                #     "original_filename": filename,
                #     "unique_filename": unique_filename,
                #     "file_size": file_size,
                #     "file_hash": file_hash,
                #     "sender_name": sender_name or "API User",
                #     "sender_id": sender_id or 0,
                #     "description": description,
                #     "metadata": metadata_dict,
                #     "uploaded_at": datetime.now().isoformat(),
                # }

                # Сохранение в базу данных
                # db_doc_data = {
                #     # Будет заполнен после отправки в Telegram
                #     "file_id": None,
                #     "file_name": filename,
                #     "file_type": file.content_type,
                #     "file_size": file_size,
                #     "sender_id": sender_id or 0,
                #     "sender_name": sender_name or "API User",
                #     "sender_username": "api",
                #     "chat_id": 0,
                #     "message_id": 0,
                #     "metadata": json.dumps(
                #         {
                #             "source": "api",
                #             "file_hash": file_hash,
                #             "original_metadata": metadata_dict,
                #             "description": description,
                #         }
                #     ),
                # }

                # doc_id = db.add_document(db_doc_data)
                doc_id = 0
                # Отправка файла на согласование через бота
                if bot_instance:
                    # Конвертируем в InputFile для Telegram
                    from telegram import InputFile

                    with open(file_path, "rb") as f:
                        input_file = InputFile(f, filename=filename)

                    # Отправляем через бота
                    sent_count = await bot_instance.send_document_to_approvers(
                        document=input_file,
                        doc_id=doc_id,
                        sender_name=sender_name or "API User",
                        file_name=filename,
                    )

                    if sent_count > 0:
                        logger.info(f"Документ #{doc_id} отправлен через API")

                        # Обновляем file_id в базе (если бот его вернул)
                        # В реальном сценарии нужно сохранить file_id из
                        # ответа Telegram

                        return JSONResponse(
                            {
                                "status": "success",
                                "message": "Document sent for approval",
                                "document_id": doc_id,
                                "sent_to_approvers": sent_count,
                                "file_info": {
                                    "original_name": filename,
                                    "size_bytes": file_size,
                                    "hash": file_hash,
                                    "uploaded_at": datetime.now().isoformat(),
                                },
                            }
                        )
                    else:
                        # Если не удалось отправить
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to send document to approvers",
                        )
                else:
                    # Бот не инициализирован
                    raise HTTPException(
                        status_code=503, detail="Bot service is not available"
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error uploading document: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )
            finally:
                # Закрываем файл
                await file.close()

        @self.app.get("/api/v1/documents/{document_id}")  # type: ignore[misc]
        async def get_document_status(
            document_id: int, x_api_key: str = Header(None)
        ) -> JSONResponse:
            """Получение статуса документа"""
            try:
                if x_api_key != settings.API_SECRET_KEY:
                    raise HTTPException(
                        status_code=403, detail="Invalid API key"
                    )

                # document = db.get_document(document_id)
                document = None
                if not document:
                    raise HTTPException(
                        status_code=404, detail="Document not found"
                    )

                # Форматируем ответ
                response = {
                    "document_id": document["id"],
                    "file_name": document["file_name"],
                    "status": document["status"],
                    "sender": document["sender_name"],
                    "created_at": document["created_at"],
                    "updated_at": document["updated_at"],
                }

                if document["status"] != "pending":
                    response.update(
                        {
                            "approver": document["approver_name"],
                            "decision_date": document["decision_date"],
                            "comment": document["comment"],
                        }
                    )

                # Получаем историю отправок согласующим
                # approvers = db.get_approvers_for_document(document_id)
                # response["approvers_sent"] = [
                #     {
                #         "approver_id": a["approver_id"],
                #         "sent_date": a["sent_date"],
                #         "status": a["status"]
                #     }
                #     for a in approvers
                # ]

                return response

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting document status: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        @self.app.get("/api/v1/documents")  # type: ignore[misc]
        async def list_documents(
            status: str | None = None,
            limit: int = 50,
            offset: int = 0,
            x_api_key: str = Header(None),
        ) -> dict[str, Any]:
            """Получение списка документов с фильтрацией"""
            try:
                if x_api_key != settings.API_SECRET_KEY:
                    raise HTTPException(
                        status_code=403, detail="Invalid API key"
                    )

                # Формируем запрос в зависимости от параметров
                query = "SELECT * FROM documents WHERE 1=1"
                params = []

                if status:
                    query += " AND status = ?"
                    params.append(status)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])  # type: ignore[list-item]

                # with db._get_connection() as conn:
                #     conn.row_factory = db._dict_factory
                #     cursor = conn.execute(query, params)
                #     documents = cursor.fetchall()

                total_query = "SELECT COUNT(*) as total FROM documents"
                if status:
                    total_query += " WHERE status = ?"
                    # total_params = [status] if status else []
                else:
                    ...
                    # total_params = []

                # with db._get_connection() as conn:
                #     cursor = conn.execute(total_query, total_params)
                #     total = cursor.fetchone()["total"]

                return {
                    # "documents": documents,
                    "pagination": {
                        # "total": total,
                        "limit": limit,
                        "offset": offset,
                        # "has_more": (offset + limit) < total,
                    },
                }

            except Exception as e:
                logger.error(f"Error listing documents: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

        @self.app.post("/api/v1/webhook/decision")  # type: ignore[misc]
        async def decision_webhook(
            payload: dict[str, Any], x_api_key: str = Header(None)
        ) -> dict[str, Any]:
            """
            Webhook для получения решений о документах
            Используется для интеграции с внешними системами
            """
            try:
                if x_api_key != settings.API_SECRET_KEY:
                    raise HTTPException(
                        status_code=403, detail="Invalid API key"
                    )

                # Валидация payload
                required_fields = ["document_id", "decision", "approver_name"]
                for field in required_fields:
                    if field not in payload:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Missing required field: {field}",
                        )

                document_id = payload["document_id"]
                decision = payload["decision"].lower()
                approver_name = payload["approver_name"]
                # comment = payload.get("comment", "")

                if decision not in ["approved", "rejected"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Decision must be 'approved' or 'rejected'",
                    )

                # Обновляем статус в базе
                # db.update_document_status(
                #     doc_id=document_id,
                #     status=decision,
                #     approver_data={
                #         "id": 0,  # Для внешних систем
                #         "name": approver_name,
                #         "username": "external_system"
                #     },
                #     comment=comment
                # )

                logger.info(
                    f"Document #{document_id} {decision} via webhook by "
                    f"{approver_name}"
                )

                return {
                    "status": "success",
                    "message": f"Document {document_id} marked as {decision}",
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

    # def check_db_connection(self) -> bool:
    #     """Проверка подключения к базе данных"""
    #     try:
    #         with db._get_connection() as conn:
    #             conn.execute("SELECT 1")
    #         return True
    #     except Exception:
    #         return False

    def set_bot_instance(self, bot: DocumentApprovalBot) -> None:
        """Установка ссылки на экземпляр бота"""
        global bot_instance
        bot_instance = bot

    async def send_document_via_bot(
        self, file_path: str, filename: str, sender_name: str, doc_id: int
    ) -> int:
        """
        Отправка документа через бота
        Возвращает количество успешно отправленных согласующим
        """
        if not bot_instance:
            return 0

        try:
            from telegram import InputFile

            with open(file_path, "rb") as f:
                input_file = InputFile(f, filename=filename)

            sent_count = await bot_instance.send_document_to_approvers(
                document=input_file,
                doc_id=doc_id,
                sender_name=sender_name,
                file_name=filename,
            )  # type: ignore[func-returns-value]

            return sent_count  # type: ignore[return-value]

        except Exception as e:
            logger.error(f"Error sending document via bot: {e}")
            return 0

    def run(self, host: str | None = None, port: int | None = None) -> None:
        """Запуск API сервера"""
        host = host or settings.APP_HOST
        port = port or settings.APP_PORT

        logger.info(f"Starting API server on {host}:{port}")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=settings.LOG_LEVEL.lower(),
        )


# Синглтон экземпляр
api_server = DocumentAPIServer()


def run_api_server() -> None:
    """Запуск API сервера в отдельном процессе"""
    api_server.run()


if __name__ == "__main__":
    run_api_server()
