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
from schemas.deal_schemas import DealUpdate
from schemas.enums import DealStagesEnum, DealStatusEnum

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealWebhookHandler:
    """
    Обработчик, который обработывает входящие вебхуки сделок.
    """

    def __init__(self, deal_client: "DealClient") -> None:
        self.deal_client = deal_client

    async def handle_deal_without_offer(
        self,
        user_id: str,
        deal_id: int,
    ) -> None:
        """
        Обработчик входящего вебхука сделки без КП.
        """
        repo = self.deal_client.repo
        contract_stage_id = await repo.get_external_id_by_sort_order_stage(
            DealStagesEnum.CONTRACT_CONCLUSION,
        )
        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "without_offer": True,
            "moved_date": date.today(),
            "status_deal": DealStatusEnum.OFFER_NO,
            "stage_id": contract_stage_id,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)

    async def _update_local_deal(
        self, deal_id: int, deal_update: DealUpdate
    ) -> None:
        """Update deal in local database with error handling"""
        try:
            await self.deal_client.repo.update_entity(deal_update)
            logger.info(f"Deal {deal_id} source updated in local database")

        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                logger.info(
                    f"Deal {deal_id} not found locally, importing from Bitrix"
                )
                await self.deal_client.import_from_bitrix(deal_id)
                await self.deal_client.repo.update_entity(deal_update)
            else:
                raise
        except Exception as e:
            logger.error(f"Failed to update local deal {deal_id}: {str(e)}")
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
        logger.info(f"Deal {deal_id} set products string field :{products}")
        products_list_as_string = self._get_products_list_as_string(
            products,
        )
        if products_list_as_string == html.unescape(products_origin).strip():
            logger.info(
                f"Deal {deal_id} products list as string is the same: "
                f"{products_list_as_string}"
            )
            return

        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "products_list_as_string": products_list_as_string,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)

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
    ) -> None:
        """
        Устанавливает стадии и статус сделки.
        Args:
            deal_id: ID сделки.
            deal_stage: ID стадии.
            deal_status: Статус сделки.
            user_id: ID пользователя.
            doc_update: Флаг обновления документа(1-обновление, 0-нет).
            doc_id: ИД документа.
        Returns:
            None
        """
        logger.info(
            f"Deal {deal_id} set stage: {deal_stage}, status: {deal_status}"
        )
        repo = self.deal_client.repo
        stage_id = await repo.get_external_id_by_sort_order_stage(
            deal_stage,
        )
        status_enum = DealStatusEnum.get_deal_status_by_name(deal_status)
        logger.info(
            f"Deal {deal_id} set stage: {stage_id}, status: {status_enum}"
        )
        data_deal: dict[str, Any] = {
            "external_id": deal_id,
            "status_deal": status_enum,
            "stage_id": stage_id,
        }
        deal_update = DealUpdate(**data_deal)

        await self._update_local_deal(deal_id, deal_update)
        await self.deal_client.bitrix_client.update(deal_update)
        fields: dict[str, Any] = {}
        if doc_update == 1 and doc_id:
            doc_data = await self.download_doc_from_id(doc_id)
            if not doc_data:
                return
            fields["UF_CRM_1764217378"] = {
                "fileData": [
                    doc_data["filename"],
                    doc_data["content"],
                ]
            }

            payload: dict[str, Any] = {"id": deal_id, "fields": fields}
            method = "crm.deal.update"
            bitrix_client = self.deal_client.bitrix_client.bitrix_client
            response = await bitrix_client.call_api(
                method=method, params=payload
            )
            if response.get("result"):
                logger.debug(f"Successfully updated deal {deal_id}")
                return
            else:
                logger.error(
                    "Bitrix API error updating product "
                    f"{deal_id}: {response}"
                )
                raise Exception

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

        except Exception as e:
            print(f"❌ Error downloading from {doc_id}: {e}")
            return None

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
        self, company_id: int, email: str, response_due_date: date
    ) -> None:
        """
        Установка стадии и статуса сделки.
        """
        print(
            f"company: {company_id}, email: {email}, date: {response_due_date}"
            "++++++++++++=============="
        )
