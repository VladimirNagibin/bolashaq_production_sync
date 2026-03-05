import re
from typing import Any

from core.logger import logger
from schemas.product_schemas import (
    FieldText,
    FieldValue,
    ProductCreate,
)

from ..exceptions import ProductTransformationError
from ..file_download_service import FileDownloadService


class ProductTransformationService:
    """
    Сервис для трансформации полей товара
    Отвечает за преобразование текстовых полей в HTML и обработку изображений
    """

    def __init__(self, file_download_service: FileDownloadService):
        self.file_download_service = file_download_service
        self.logger = logger

        # Маппинг полей для трансформации
        self.fields_mapping = [
            {
                "source": "characteristics",
                "target": "characteristics_for_print",
                "title": "Технические характеристики",
                "description": "технических характеристик",
            },
            {
                "source": "complect",
                "target": "complect_for_print",
                "title": "Комплект поставки",
                "description": "комплекта поставки",
            },
        ]

        # Конфигурация изображений
        self.image_config: dict[str, Any] = {
            "source_property": "property101",  # Галерея изображений
            "target_field": "DETAIL_PICTURE",  # Детальная картинка
            "property_id": 101,
            "description": "основного изображения",
        }

    async def transform_product_fields(
        self,
        product_data: ProductCreate,
        product_id: int,
        product_data_dict: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Трансформирует поля товара

        Args:
            product_data: Данные товара
            product_id: ID товара в Bitrix24

        Returns:
            tuple: (text_fields_update, image_fields_update)

        Raises:
            ProductTransformationError: при критических ошибках
        """
        try:
            self.logger.info(
                f"Starting fields transformation for product {product_id}"
            )

            # Трансформация текстовых полей
            text_fields = await self._transform_text_fields(product_data)

            # Трансформация изображений
            image_fields = await self._transform_image_fields(
                product_data_dict, product_id
            )

            transformed_count = len(text_fields) + (1 if image_fields else 0)
            self.logger.info(
                f"Transformed {transformed_count} fields for product "
                f"{product_id}"
            )

            return text_fields, image_fields

        except Exception as e:
            error_msg = f"Failed to transform product {product_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ProductTransformationError(error_msg) from e

    async def _transform_text_fields(
        self, product_data: ProductCreate
    ) -> dict[str, Any]:
        """
        Трансформирует текстовые поля в HTML формат

        Args:
            product_data: Данные товара

        Returns:
            dict: Поля для обновления
        """
        update_fields: dict[str, Any] = {}

        for mapping in self.fields_mapping:
            try:
                field_update = self._transform_single_text_field(
                    product_data=product_data,
                    source_field=mapping["source"],
                    target_field=mapping["target"],
                    title=mapping["title"],
                    field_description=mapping["description"],
                )

                if field_update:
                    update_fields.update(field_update)
                    self.logger.debug(
                        f"Transformed field {mapping['source']} -> "
                        f"{mapping['target']}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Error transforming field {mapping['source']}: {str(e)}",
                    exc_info=True,
                )
                # Продолжаем обработку других полей
                continue

        return update_fields

    def _transform_single_text_field(
        self,
        product_data: ProductCreate,
        source_field: str,
        target_field: str,
        title: str,
        field_description: str,
    ) -> dict[str, Any]:
        """
        Трансформирует одно текстовое поле

        Args:
            product_data: Данные товара
            source_field: Исходное поле
            target_field: Целевое поле
            title: Заголовок для HTML
            field_description: Описание поля для логирования

        Returns:
            dict: Поля для обновления или пустой словарь
        """
        try:
            # Получаем значения полей
            source_value = self._get_field_text_value(
                product_data, source_field
            )
            target_value = self._get_field_text_value(
                product_data, target_field
            )

            update_data: dict[str, Any] = {}

            # Если исходное значение пустое, очищаем целевое поле
            if not source_value:
                if target_value:
                    self.logger.debug(
                        f"Clearing {field_description} - source is empty"
                    )
                    update_data[target_field] = FieldValue(
                        value=FieldText(text="", type="")
                    )
                return update_data

            # Парсим и преобразуем значение
            parsed_value = self._parse_text_to_html(source_value, title)

            # Обновляем только если значения отличаются
            if target_value is None or target_value != parsed_value:
                self.logger.debug(
                    f"Updating {field_description}: "
                    f"old length: {len(target_value or '')}, "
                    f"new length: {len(parsed_value)}"
                )

                update_data[target_field] = FieldValue(
                    value=FieldText(text=parsed_value, type="HTML")
                )

            return update_data

        except Exception as e:
            self.logger.error(
                f"Error processing field {source_field} -> "
                f"{target_field}: {str(e)}"
            )
            return {}

    def _get_field_text_value(
        self, product_data: ProductCreate, field_name: str
    ) -> str | None:
        """
        Получает текстовое значение поля из товара

        Args:
            product_data: Данные товара
            field_name: Имя поля

        Returns:
            str | None: Текстовое значение поля
        """
        try:
            field_attr = getattr(product_data, field_name, None)
            if field_attr and hasattr(field_attr, "value"):
                # if hasattr(field_attr.value, 'text'):
                #     return field_attr.value.text
                if hasattr(field_attr.value, "text_field"):
                    return str(field_attr.value.text_field)
            return None
        except Exception as e:
            self.logger.warning(f"Error getting field {field_name} value: {e}")
            return None

    def _parse_text_to_html(self, text: str, title: str) -> str:
        """
        Парсит текст и преобразует в HTML формат

        Args:
            text: Исходный текст
            title: Заголовок для блока

        Returns:
            str: HTML форматированный текст
        """
        if not text or not text.strip():
            return ""

        try:
            # Разбиваем текст на строки и очищаем
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            if not lines:
                return ""

            # Экранируем специальные HTML символы
            escaped_lines: list[str] = []
            for line in lines:
                # Удаляем существующие HTML теги кроме разрешенных
                line = re.sub(r"<[^>]*>", "", line)
                # line = line.replace("<br>", "")
                # Экранируем специальные символы
                escaped = (
                    line.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#39;")
                )
                escaped_lines.append(escaped)

            # Формируем HTML
            html_parts = [
                f"<strong>{title}</strong>",
                '<ul style="list-style: none; padding-left: 1;">',
                *[f"<li>{line}</li>" for line in escaped_lines],
                "</ul>",
            ]

            return "\n".join(html_parts)

        except Exception as e:
            self.logger.error(f"Error parsing text to HTML: {str(e)}")
            # Возвращаем простой HTML в случае ошибки
            escaped_text = text.replace("&", "&amp;").replace("<", "&lt;")
            return f"<strong>{title}</strong><p>{escaped_text}</p>"

    async def _transform_image_fields(
        self, product_data: dict[str, Any], product_id: int
    ) -> dict[str, Any]:
        """
        Трансформирует поля изображений

        Args:
            product_data: Данные товара
            product_id: ID товара

        Returns:
            dict: Поля для обновления изображений
        """
        try:
            # Проверяем, есть ли уже детальная картинка
            if self._has_detail_picture(product_data):
                self.logger.debug(
                    f"Product {product_id} already has detail picture"
                )
                return {}

            # Получаем изображение из галереи
            image_data = await self._get_first_gallery_image(
                product_data, product_id
            )

            if not image_data:
                self.logger.debug(
                    f"No gallery images found for product {product_id}"
                )
                return {}

            # Формируем данные для загрузки
            return {
                self.image_config["target_field"]: {
                    "fileData": [image_data["filename"], image_data["content"]]
                }
            }

        except Exception as e:
            self.logger.error(
                "Error transforming image fields for product "
                f"{product_id}: {e}",
                exc_info=True,
            )
            return {}

    def _has_detail_picture(self, product_data: dict[str, Any]) -> bool:
        """
        Проверяет наличие детальной картинки у товара

        Args:
            product_data: Данные товара

        Returns:
            bool: True если картинка есть
        """
        try:
            preview_pictures: dict[str, Any] | None = product_data.get(
                "DETAIL_PICTURE", {}
            )
            if isinstance(preview_pictures, dict):
                if int(preview_pictures.get("id", 0)) > 0:
                    return True
            return False

        except Exception as e:
            self.logger.warning(f"Error checking detail picture: {e}")
            return False

    async def _get_first_gallery_image(
        self, product_data: dict[str, Any], product_id: int
    ) -> dict[str, Any] | None:
        """
        Получает первое изображение из галереи

        Args:
            product_data: Данные товара
            product_id: ID товара

        Returns:
            dict | None: Данные изображения
        """
        try:
            # Получаем URL первого изображения из галереи
            image_url = self._build_gallery_image_url(product_data, product_id)

            if not image_url:
                return None

            # Скачиваем изображение
            self.logger.debug(f"Downloading gallery image from {image_url}")
            image_data = await self.file_download_service.download_file(
                image_url
            )

            if image_data:
                self.logger.info(
                    f"Successfully downloaded gallery image for product "
                    f"{product_id}: {image_data['filename']} "
                    "({image_data['file_size']} bytes)"
                )

            return image_data  # type:ignore[no-any-return]

        except Exception as e:
            self.logger.error(
                f"Error getting gallery image for product {product_id}: {e}"
            )
            return None

    def _build_gallery_image_url(
        self, product_data: dict[str, Any], product_id: int
    ) -> str | None:
        """
        Формирует URL для скачивания изображения из галереи

        Args:
            product_data: Данные товара
            product_id: ID товара

        Returns:
            str | None: URL изображения
        """
        try:
            from core.settings import settings

            # Получаем ID первого изображения из галереи
            image_id = self._get_first_gallery_image_id(product_data)

            if not image_id:
                return None

            # Формируем URL для скачивания
            base_url = settings.BITRIX_PORTAL.rstrip("/")
            webhook_path = settings.WEB_HOOK_TOKEN.lstrip("/")

            url = (
                f"{base_url}/{webhook_path}"
                f"catalog.product.download?"
                f"fields%5BfieldName%5D="
                f"{self.image_config['source_property']}&"
                f"fields%5BfileId%5D={image_id}&"
                f"fields%5BproductId%5D={product_id}"
            )

            return url

        except Exception as e:
            self.logger.error(f"Error building gallery image URL: {e}")
            return None

    def _get_first_gallery_image_id(
        self, product_data: dict[str, Any]
    ) -> int | None:
        """
        Получает ID первого изображения из галереи

        Args:
            product_data: Данные товара

        Returns:
            int | None: ID изображения
        """
        try:
            # Пытаемся получить из свойства PROPERTY_101
            gallery = product_data.get("PROPERTY_101", [])
            if gallery and isinstance(gallery, list):
                first_item = gallery[0]
                if isinstance(first_item, dict):
                    result = first_item.get("value", {}).get("id")
                    return result  # type:ignore[no-any-return]

            return None

        except Exception as e:
            self.logger.warning(f"Error getting gallery image ID: {e}")
            return None
