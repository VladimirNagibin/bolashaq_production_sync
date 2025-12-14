import base64
import html
import mimetypes
import re
from datetime import date
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

import requests  # type: ignore[import-untyped]
from fastapi import HTTPException, status

from core.logger import logger
from schemas.base_schemas import CommunicationChannel
from schemas.company_schemas import CompanyUpdate
from schemas.deal_schemas import DealUpdate
from schemas.enums import DealStagesEnum, DealStatusEnum

from ..exceptions import (
    CompanyClientNotInitializedError,
    DealNotFoundError,
    DealProcessingError,
    DocumentProcessingError,
)

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealWebhookHandler:
    """
    Обработчик, который обработывает входящие вебхуки сделок.
    """

    def __init__(self, deal_client: "DealClient") -> None:
        self.deal_client = deal_client

    async def handle_deal_without_stage(
        self,
        user_id: str,
        deal_id: int,
        stage_id: DealStagesEnum,
    ) -> None:
        """
        Обработчик входящего вебхука сделки без Стадии.
        """
        logger.info(
            (
                f"Handling deal without stage for deal_id={deal_id}, "
                f"stage_id={stage_id}"
            ),
            extra={"deal_id": deal_id, "stage_id": stage_id.value},
        )
        deal_data: dict[str, Any] = {}
        repo = self.deal_client.repo

        try:
            # without Offer stage
            if stage_id == DealStagesEnum.OFFER_PREPARE:
                new_stage_id = await repo.get_external_id_by_sort_order_stage(
                    DealStagesEnum.CONTRACT_CONCLUSION,
                )
                deal_data = {
                    "external_id": deal_id,
                    "without_offer": True,
                    "moved_date": date.today(),
                    "status_deal": DealStatusEnum.OFFER_NO,
                    "stage_id": new_stage_id,
                }
            # without contract stage
            elif stage_id == DealStagesEnum.CONTRACT_CONCLUSION:
                new_stage_id = await repo.get_external_id_by_sort_order_stage(
                    DealStagesEnum.PREPAYMENT_INVOICE,
                )
                deal_data = {
                    "external_id": deal_id,
                    "without_contract": True,
                    "moved_date": date.today(),
                    "status_deal": DealStatusEnum.CONTRACT_NO,
                    "stage_id": new_stage_id,
                }
            if not deal_data:
                logger.warning(
                    (
                        f"No processing logic defined for "
                        f"stage_id={stage_id.value} in deal {deal_id}"
                    ),
                    extra={"deal_id": deal_id, "stage_id": stage_id.value},
                )
                return

            deal_update = DealUpdate(**deal_data)

            await self._update_local_deal(deal_id, deal_update)
            await self.deal_client.bitrix_client.update(deal_update)
            logger.info(
                (
                    f"Successfully processed deal {deal_id} for stage "
                    f"{stage_id.value}"
                ),
                extra={"deal_id": deal_id, "stage_id": stage_id.value},
            )

        except Exception as e:
            logger.exception(
                f"Failed to handle deal without stage for deal_id={deal_id}",
                extra={"deal_id": deal_id, "stage_id": stage_id.value},
                exc_info=True,
            )
            raise DealProcessingError(
                f"Error processing deal {deal_id}"
            ) from e

    async def _update_local_deal(
        self, deal_id: int, deal_update: DealUpdate
    ) -> None:
        """Update deal in local database with error handling"""
        try:
            await self.deal_client.repo.update_entity(deal_update)
            logger.info(
                f"Deal {deal_id} source updated in local database",
                extra={"deal_id": deal_id},
            )

        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                logger.warning(
                    (
                        f"Deal {deal_id} not found locally, attempting to "
                        "import from Bitrix."
                    ),
                    extra={"deal_id": deal_id},
                )
                try:
                    await self.deal_client.import_from_bitrix(deal_id)
                    await self.deal_client.repo.update_entity(deal_update)
                    logger.info(
                        f"Deal {deal_id} imported and updated.",
                        extra={"deal_id": deal_id},
                    )
                except Exception as import_e:
                    logger.exception(
                        f"Failed to import and update deal {deal_id}",
                        extra={"deal_id": deal_id},
                        exc_info=True,
                    )
                    raise DealNotFoundError(
                        f"Deal {deal_id} not found and import failed"
                    ) from import_e
            else:
                logger.error(
                    f"HTTP error updating local deal {deal_id}: {e.detail}",
                    extra={"deal_id": deal_id, "status_code": e.status_code},
                )
                raise
        except Exception:
            logger.exception(
                (
                    "An unexpected error occurred while updating local deal "
                    f"{deal_id}"
                ),
                extra={"deal_id": deal_id},
                exc_info=True,
            )
            raise

    async def set_products_string_field(
        self,
        user_id: str,
        deal_id: int,
        products: str,
        products_origin: str,
    ) -> None:
        """
        Обработчик входящего вебхука сделки установка списка товаров в
        строковое поле.
        """
        logger.info(
            f"Setting products string field for deal {deal_id}",
            extra={"deal_id": deal_id},
        )
        products_list_as_string = self._get_products_list_as_string(
            products,
        )
        original_products = html.unescape(products_origin).strip()

        if products_list_as_string == original_products:
            logger.info(
                (
                    f"Products list for deal {deal_id} is unchanged. "
                    "Skipping update."
                ),
                extra={"deal_id": deal_id},
            )
            return

        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "products_list_as_string": products_list_as_string,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)
        logger.info(
            f"Successfully updated products string field for deal {deal_id}",
            extra={"deal_id": deal_id},
        )

    def _get_products_list_as_string(self, table_string: str) -> str:
        """
        Преобразует BBCode-таблицу в форматированный текст.

        Args:
            table_string: Строка с таблицей в формате BBCode.

        Returns:
            Отформатированная строка с данными из таблицы.
        """
        # Регулярное выражение для поиска пар [td]...[/td][td]...[/td]
        # (.*?) - ленивый захват любого текста внутри тегов
        pattern = re.compile(r"\[td\](.*?)\[/td\]\[td\](.*?)\[/td\]")

        # Находим все совпадения в строке
        # Результатом будет список кортежей:
        # [('Товар1', 'Цена1'), ('Товар2', 'Цена2')]
        matches = pattern.findall(table_string)

        lines: list[str] = []
        # 2. Проходим по каждой найденной паре (товар, цена)
        for product, price in matches:
            # 3. Декодируем HTML-сущности и убираем лишние пробелы
            clean_product = html.unescape(product).strip()
            clean_price = html.unescape(price).strip()

            if clean_product and clean_price:
                # 4. Формируем строку из очищенных данных
                lines.append(f"{clean_product}: {clean_price}")

        # Соединяем все строки в единый текст с переносом строки
        return "\n".join(lines)

    async def set_stage_status_deal(
        self,
        deal_id: int,
        deal_stage: int,
        deal_status: str,
        user_id: str | None = None,
        doc_update: int | None = None,
        doc_id: int | None = None,
        response_due_date: date | None = None,
    ) -> None:
        """
        Устанавливает стадии и статус сделки и прикрепляет документ при
        необходимости.
        Args:
            deal_id: ID сделки.
            deal_stage: ID стадии.
            deal_status: Статус сделки.
            user_id: ID пользователя.
            doc_update: Флаг обновления документа(1-обновление, 0-нет).
            doc_id: ИД документа.
            response_due_date: Дата ожидаемого ответа клиента.
        Returns:
            None
        """
        logger.info(
            (
                f"Setting stage/status for deal {deal_id}. "
                f"Stage: {deal_stage}, Status: {deal_status}"
            ),
            extra={
                "deal_id": deal_id,
                "deal_stage": deal_stage,
                "deal_status": deal_status,
            },
        )
        try:
            repo = self.deal_client.repo
            stage_id = await repo.get_external_id_by_sort_order_stage(
                deal_stage,
            )
            status_enum = DealStatusEnum.get_deal_status_by_name(deal_status)
            if not status_enum or not stage_id:
                raise DealProcessingError(
                    "Invalid deal status or stage: "
                    f"{deal_status}, {deal_stage}"
                )
            logger.debug(
                f"Deal {deal_id} set stage: {stage_id}, status: {status_enum}"
            )
            deal_update_data: dict[str, Any] = {
                "external_id": deal_id,
                "status_deal": status_enum,
                "stage_id": stage_id,
            }
            if response_due_date:
                deal_update_data["date_answer_client"] = response_due_date
            deal_update = DealUpdate(**deal_update_data)

            await self._update_local_deal(deal_id, deal_update)
            await self.deal_client.bitrix_client.update(deal_update)

            if doc_update == 1 and doc_id:
                await self._attach_document_to_deal(
                    deal_id, doc_id, status_enum
                )

        except Exception as e:
            logger.exception(
                f"Failed to set stage/status for deal {deal_id}",
                extra={"deal_id": deal_id},
                exc_info=True,
            )
            raise DealProcessingError(
                f"Error setting stage/status for deal {deal_id}"
            ) from e

    async def _attach_document_to_deal(
        self, deal_id: int, doc_id: int, status_enum: DealStatusEnum
    ) -> None:
        """Скачивает документ и прикрепляет его к сделке."""
        logger.info(
            f"Attaching document {doc_id} to deal {deal_id}",
            extra={"deal_id": deal_id, "doc_id": doc_id},
        )

        doc_data = await self.download_doc_from_id(doc_id)
        if not doc_data:
            raise DocumentProcessingError(
                f"Could not download document {doc_id} for deal {deal_id}"
            )

        fieldname_map = {
            DealStatusEnum.OFFER_APPROVED_SUPERVISOR: "UF_CRM_1764217378",
            DealStatusEnum.DRAFT_CONTRACT_APPROVED_SUPERVISOR: (
                "UF_CRM_1765532097"
            ),
        }

        fieldname = fieldname_map.get(status_enum)
        if not fieldname:
            logger.warning(
                (
                    f"No field mapped for status {status_enum.name}. "
                    "Cannot attach document {doc_id}."
                ),
                extra={
                    "deal_id": deal_id,
                    "doc_id": doc_id,
                    "status_enum": status_enum.name,
                },
            )
            raise ValueError(f"No field mapped for status {status_enum.name}")

        fields = {
            fieldname: {
                "fileData": [doc_data["filename"], doc_data["content"]]
            }
        }

        payload: dict[str, Any] = {"id": deal_id, "fields": fields}
        bitrix_client = self.deal_client.bitrix_client.bitrix_client
        response = await bitrix_client.call_api("crm.deal.update", payload)

        if response.get("result"):
            logger.info(
                f"Successfully attached document {doc_id} to deal {deal_id}",
                extra={"deal_id": deal_id},
            )
        else:
            error_desc = response.get(
                "error_description", "Unknown Bitrix API error"
            )
            logger.error(
                (
                    "Bitrix API error attaching document to deal "
                    f"{deal_id}: {error_desc}"
                ),
                extra={"deal_id": deal_id, "response": response},
            )
            raise DocumentProcessingError(f"Bitrix API error: {error_desc}")

    async def download_doc_from_id(self, doc_id: int) -> dict[str, Any] | None:
        """
        Скачивает документ по URL и возвращает данные для загрузки

        Returns:
            dict: {'content': base64, 'filename': str, 'content_type': str}
        """
        try:
            bitrix_client = self.deal_client.bitrix_client.bitrix_client
            method = "disk.file.get"
            params = {"id": doc_id}
            response_doc = await bitrix_client.call_api(method, params)
            doc_url = response_doc.get("result", {}).get("DOWNLOAD_URL")

            if not doc_url:
                raise DocumentProcessingError(
                    f"Could not get DOWNLOAD_URL for document {doc_id}"
                )

            response = requests.get(doc_url, timeout=30)
            response.raise_for_status()
            # Определяем тип контента и расширение файла
            content_type: str = response.headers.get(
                "content-type",
                (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
            extension = mimetypes.guess_extension(content_type) or ".docx"
            filename = (
                self._extract_filename_from_response(response, doc_url)
                or f"offer{extension}"
            )

            # Если в имени файла нет расширения, добавляем его
            if "." not in filename:
                filename += extension

            # Кодируем в base64
            file_content_base64 = base64.b64encode(response.content).decode(
                "utf-8"
            )

            return {
                "content": file_content_base64,
                "filename": filename,
                "content_type": content_type,
                "file_size": len(response.content),
            }

        except requests.RequestException as e:
            logger.error(
                f"Network error downloading document {doc_id}: {e}",
                extra={"doc_id": doc_id},
            )
            raise DocumentProcessingError(
                f"Network error for document {doc_id}"
            ) from e
        except Exception as e:
            logger.exception(
                f"Unexpected error downloading document {doc_id}",
                extra={"doc_id": doc_id},
                exc_info=True,
            )
            raise DocumentProcessingError(
                f"Unexpected error for document {doc_id}"
            ) from e

    def _extract_filename_from_response(
        self, response: requests.Response, fallback_url: str
    ) -> str | None:
        """
        Извлекает имя файла из HTTP response

        Приоритет:
        1. Content-Disposition header (filename*)
        2. Content-Disposition header (filename)
        3. URL path
        """
        headers = response.headers

        # 1. Пробуем извлечь из Content-Disposition (filename*)
        content_disposition = headers.get("Content-Disposition", "")
        if content_disposition:
            # Ищем filename* (с кодировкой)
            match = re.search(
                r"filename\*=([^;]+)", content_disposition, re.IGNORECASE
            )
            if match:
                filename = match.group(1).strip()
                filename = filename.strip("\"'")
                if filename.lower().startswith("utf-8''"):
                    return unquote(filename[7:])
                return unquote(filename)

            # Ищем обычный filename
            match = re.search(
                r"filename=([^;]+)", content_disposition, re.IGNORECASE
            )
            if match:
                filename = match.group(1).strip()
                filename = filename.strip("\"'")
                return unquote(filename)

        # 2. Пробуем извлечь из URL
        # parsed_url = urlparse(fallback_url)
        # url_filename = parsed_url.path.split("/")[-1]
        # if url_filename and "." in url_filename:
        #    return url_filename

        return None

    async def company_set_work_email(
        self, company_id: int, email: str
    ) -> None:
        """
        Устанавливает/обновляет рабочий email для компании.
        """
        logger.info(
            f"Setting work email for company {company_id}",
            extra={"company_id": company_id},
        )

        company_client = self.deal_client.repo.company_client
        if not company_client or not company_client.bitrix_client:
            logger.error(
                "Company client or its Bitrix client is not initialized."
            )
            raise CompanyClientNotInitializedError(
                "Company client is not available"
            )
        try:
            company = await company_client.bitrix_client.get(company_id)
            current_emails: list[CommunicationChannel] = company.email or []

            work_email_exists = False
            company_need_update = False
            for email_channel in current_emails:
                if email_channel.value == email:
                    if email_channel.value_type != "WORK":
                        email_channel.value_type = "WORK"
                        logger.info(
                            (
                                f"Updated existing email {email} to WORK type "
                                f"for company {company_id}"
                            ),
                            extra={"company_id": company_id},
                        )
                        company_need_update = True
                    work_email_exists = True
                elif email_channel.value_type == "WORK":
                    email_channel.value_type = "OTHER"
                    company_need_update = True
            if not work_email_exists:
                company_need_update = True
                email_date: dict[str, Any] = {
                    "type_id": "EMAIL",
                    "value_type": "WORK",
                    "value": email,
                }
                current_emails.append(CommunicationChannel(**email_date))
                logger.info(
                    f"Added new work email {email} for company {company_id}",
                    extra={"company_id": company_id},
                )
            if not company_need_update:
                logger.info(
                    f"No changes needed for company {company_id}",
                    extra={"company_id": company_id},
                )
                return

            company_update_data: dict[str, Any] = {
                "external_id": company_id,
                "email": current_emails,
            }
            company_update = CompanyUpdate(**company_update_data)

            await company_client.bitrix_client.update(company_update)
            logger.info(
                (
                    "Successfully updated work email for company "
                    f"{company_id}"
                ),
                extra={"company_id": company_id},
            )
        except Exception as e:
            logger.exception(
                f"Failed to set work email for company {company_id}",
                extra={"company_id": company_id},
                exc_info=True,
            )
            raise DealProcessingError(
                f"Error setting work email for company {company_id}"
            ) from e
