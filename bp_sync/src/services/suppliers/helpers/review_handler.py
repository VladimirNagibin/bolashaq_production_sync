import base64
import binascii
import hashlib
import mimetypes
import re
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from starlette.datastructures import FormData

from core.exceptions.supplier_exceptions import NameNotFoundError
from core.logger import logger
from core.settings import settings
from schemas.enums import BrandEnum, ImageType
from schemas.fields import FIELDS_SUPPLIER_PRODUCT
from schemas.product_schemas import (
    FieldText,
    FieldValue,
    ProductCreate,
    ProductUpdate,
)
from schemas.supplier_schemas import SupplierProductDetail
from services.products.product_services import ProductClient
from services.productsections.productsection_services import (
    ProductsectionClient,
)

from .data_transformer import DataTransformer


class ReviewHandler:
    """Обрабатывает логику ревью: подготовка данных и сохранение формы."""

    # Поля, которые всегда должны присутствовать
    REQUIRED_FIELDS = {"name"}

    # Константы для имен полей формы
    FIELD_PREFIX = "field_"
    UPDATE_PREFIX = "update_"
    VALUE_ON = "on"

    # Маппинг сложных полей
    MAPPING_FIELDS: dict[str, str] = {
        "characteristics": "specifications",
        "complects": "configuration",
    }

    def __init__(
        self,
        product_client: ProductClient,
        product_section_client: ProductsectionClient,
    ):
        self.product_client = product_client
        self.product_section_client = product_section_client
        self.transformer = DataTransformer()

    # === Подготовка данных для отображения в шаблоне. ===

    async def prepare_review_context(
        self,
        supplier_product: SupplierProductDetail,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Готовит данные для отображения в шаблоне.

        Returns:
            Кортеж (простые поля, комплексные поля)
        """
        try:
            review_data = self._prepare_simple_fields(
                transformed_logs, product
            )
            review_data.extend(
                self._prepare_complex_fields(transformed_logs, product)
            )
            review_special_data = await self._prepare_special_fields(
                supplier_product, transformed_logs, preprocessed_data, product
            )
            return review_data, review_special_data

        except Exception as e:
            logger.error(
                f"Failed to prepare review context: {e}",
                extra={"product_id": str(supplier_product.id)},
                exc_info=True,
            )
            return [], []

    def _prepare_simple_fields(
        self,
        transformed_logs: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> list[dict[str, Any]]:
        """Подготавливает простые поля для отображения."""
        review_data: list[dict[str, Any]] = []
        simple_fields = FIELDS_SUPPLIER_PRODUCT.get("simple_fields", [])

        for field_name, value_type in simple_fields:
            if field_name not in transformed_logs:
                continue

            field_data = transformed_logs[field_name]
            review_data.append(
                {
                    "field_name": field_name,
                    "old_value": field_data.get("old_value"),
                    "new_value": field_data.get("new_value"),
                    "current_product_value": getattr(
                        product, field_name, None
                    ),
                    "value_type": value_type,
                }
            )

        return review_data

    def _prepare_complex_fields(
        self,
        transformed_logs: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> list[dict[str, Any]]:
        """Подготавливает сложные поля для отображения."""
        review_data: list[dict[str, Any]] = []
        complex_fields = FIELDS_SUPPLIER_PRODUCT.get("complex_fields", [])

        for field_name, value_type in complex_fields:
            if field_name not in transformed_logs:
                continue

            field_data = transformed_logs[field_name]
            current = getattr(product, field_name, None)
            current_val = (
                current.value
                if current and hasattr(current, "value")
                else None
            )
            review_data.append(
                {
                    "field_name": field_name,
                    "old_value": field_data.get("old_value"),
                    "new_value": field_data.get("new_value"),
                    "current_product_value": current_val,
                    "value_type": value_type,
                }
            )

        return review_data

    async def _prepare_special_fields(
        self,
        supplier_product: SupplierProductDetail,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> list[dict[str, Any]]:
        """Подготавливает специальные поля для отображения."""
        review_special_data: list[dict[str, Any]] = []
        special_fields = FIELDS_SUPPLIER_PRODUCT.get("individual_fields", ())
        for field_name, _ in special_fields:
            field_data = await self._get_value_special_fields(
                field_name,
                transformed_logs,
                preprocessed_data,
                product,
                supplier_product,
            )
            review_special_data.extend(field_data)
        return review_special_data

    async def _get_value_special_fields(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        try:
            if field_name == "brend":
                return self._get_brand(
                    field_name,
                    transformed_logs,
                    product,
                    supplier_product,
                )
            elif field_name == "internal_section_id":
                return self._get_section(
                    field_name,
                    transformed_logs,
                    preprocessed_data,
                    product,
                    supplier_product,
                )
            elif field_name in ["characteristics", "complects"]:
                return self._get_list_items(
                    field_name, preprocessed_data, product
                )

            elif field_name == "description":
                return self._get_description(
                    field_name,
                    transformed_logs,
                    preprocessed_data,
                    product,
                )
            elif field_name == "detail_picture":
                return await self._get_detail_picture(
                    field_name,
                    transformed_logs,
                    preprocessed_data,
                    product,
                    supplier_product,
                )
            elif field_name == "more_photos":
                return await self._get_more_photos(
                    field_name,
                    transformed_logs,
                    preprocessed_data,
                    product,
                    supplier_product,
                )
            return []
        except Exception as e:
            logger.warning(
                f"Error getting special field '{field_name}': {e}",
                extra={"product_id": str(supplier_product.id)},
            )
            return []

    def _get_brand(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        try:
            current_val = None
            field_data = transformed_logs.get(field_name, {})
            if not field_data:
                old_value = supplier_product.brend
            else:
                old_value = field_data.get("old_value")

            current = getattr(product, field_name, None)
            if current and hasattr(current, "value"):
                try:
                    current_val_key = int(current.value)
                    current_val = BrandEnum.get_display_name(current_val_key)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        "Product missing extract brand",
                        extra={
                            "product_id": getattr(product, "id", None),
                            "error": str(e),
                        },
                    )
            return [
                {
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": field_data.get("new_value"),
                    "current_product_value": current_val,
                    "value_type": "str",
                }
            ]
        except Exception:
            return []

    def _get_section(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            for name in ["supplier_category", "supplier_subcategory"]:
                result.append(
                    self._get_category_data(
                        name, transformed_logs, supplier_product
                    )
                )
            field_data = preprocessed_data.get(field_name, {})
            old_value = field_data.get("old_value")
            if not field_data:
                old_value = getattr(supplier_product, field_name, None)

            current = getattr(product, "section_id", None)

            result.append(
                {
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": field_data.get("new_value"),
                    "current_product_value": current,
                    "value_type": "int",
                }
            )
            return result
        except Exception:
            return []

    def _get_category_data(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        supplier_product: SupplierProductDetail,
    ) -> dict[str, Any]:
        if field_name in transformed_logs:
            field_data = transformed_logs.get(field_name, {})
            old_value = field_data.get("old_value")
            new_value = field_data.get("new_value")
        else:
            old_value = getattr(supplier_product, field_name, None)
            new_value = None
        return {
            "field_name": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "current_product_value": None,
            "value_type": "str",
        }

    def _get_list_items(
        self,
        field_name: str,
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            field_data = preprocessed_data.get(field_name)
            if field_data is None:
                return result

            old_value = self._transform_items(
                field_data.get("old_value"), field_name, "old"
            )
            new_value = self._transform_items(
                field_data.get("new_value"), field_name, "new"
            )
            current_val = self._get_list_complex_product_value(
                product, field_name
            )

            return [
                {
                    "field_name": field_name,
                    "old_value": (self._transform_data_list(old_value)),
                    "new_value": (self._transform_data_list(new_value)),
                    "current_product_value": (
                        self._transform_data_list(current_val)
                    ),
                    "value_type": "str",
                    "new_value_list": new_value,
                }
            ]
        except Exception:
            return result

    def _transform_items(
        self, items: list[Any] | None, field_name: str, field_type: str
    ) -> list[str] | None:
        if items is None or not items:
            return None
        items_list: list[str] = []
        for item in items:
            result = None
            if field_name == "characteristics":
                # Преобразование SupplierCharacteristicCreate и
                # ProductCharacteristic в строку для Битрикса
                result = (
                    f"{item.name}: {item.value} "
                    f"{item.unit if item.unit else ''}"
                )
            if field_name == "complects":
                # Преобразование SupplierComplectCreate и KitItem
                # в строку для Битрикса
                specifications = None
                if field_type == "old":  # SupplierComplectCreate
                    specifications = item.specifications
                elif field_type == "new":  # KitItem
                    specifications = self.transformer.transform_specifications(
                        item.specifications
                    )
                complects: list[str] = []
                if item.code:
                    complects.append(f"{item.code}: ")
                complects.append(f"{item.name}.")
                if item.description:
                    complects.append(f" {item.description}.")
                if specifications:
                    complects.append(f" {specifications}.")
                if complects:
                    result = "".join(complects)
            if result:
                items_list.append(result.strip())
        return items_list

    def _get_complex_product_value(
        self, product: ProductCreate | None, field_name: str
    ) -> str | None:
        try:
            if not product:
                return None
            current_data = getattr(product, field_name, None)
            if current_data and hasattr(current_data, "value"):
                current_field = current_data.value
                if current_field and hasattr(current_field, "text_field"):
                    return str(current_field.text_field)
            return None
        except Exception:
            return None

    def _get_list_complex_product_value(
        self, product: ProductCreate | None, field_name: str
    ) -> list[str] | None:
        try:
            if not product:
                return None
            current_field_name = self.MAPPING_FIELDS.get(field_name)
            if not current_field_name:
                return None
            current_data = getattr(product, current_field_name, None)
            data_list: list[str] = []
            if current_data:
                for data in current_data:
                    val = getattr(data, "value", None)
                    if val:
                        data_list.append(val)
                if data_list:
                    return data_list
            return None
        except Exception:
            return None

    def _transform_data_list(self, data_list: list[str] | None) -> str | None:
        if not data_list:
            return None
        return "\n---------\n".join(data_list)

    def _get_description(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            if field_name not in transformed_logs:
                return result

            field_data = transformed_logs[field_name]
            result.append(
                {
                    "field_name": field_name,
                    "old_value": field_data.get("old_value"),
                    "new_value": field_data.get("new_value"),
                    "current_product_value": getattr(
                        product, field_name, None
                    ),
                    "value_type": "str",
                }
            )

            mapping = {
                "preview_for_offer": "additional_description",
                "description_for_offer": "description_for_print",
            }
            for name in ["preview_for_offer", "description_for_offer"]:
                field_data = preprocessed_data.get(name, {})
                result.append(
                    {
                        "field_name": name,
                        "old_value": field_data.get("old_value"),
                        "new_value": field_data.get("new_value"),
                        "current_product_value": (
                            self._get_complex_product_value(
                                product, mapping[name]
                            )
                        ),
                        "value_type": "str",
                    }
                )
            return result
        except Exception:
            return []

    async def _get_detail_picture(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            field_name_process = f"{field_name}_process"
            if (
                field_name not in transformed_logs
                and field_name_process not in preprocessed_data
            ):
                return result
            field_data = None
            old_value = None
            if field_name in transformed_logs:
                field_data = transformed_logs[field_name]
                old_value = field_data.get("old_value")
            elif field_name_process in preprocessed_data:
                field_data = preprocessed_data[field_name_process]
                old_value = supplier_product.detail_picture
            if not field_data:
                return result

            result.append(
                {
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": field_data.get("new_value"),
                    "current_product_value": (
                        await self._get_current_image_data(product)
                    ),
                    "value_type": "str",
                }
            )
            return result
        except Exception:
            return []

    async def _get_current_image_data(
        self, product: ProductCreate | None
    ) -> dict[str, Any] | None:
        try:
            if not product or not product.external_id:
                return None
            image_repo = self.product_client.image_client.repo
            current_image = await image_repo.get_detail_by_product_id(
                int(product.external_id)
            )
            if not current_image:
                return None
            return {
                "detail_url": current_image.detail_url,
                "source": current_image.source,
                "supplier_image_url": current_image.supplier_image_url,
            }
        except Exception:
            return None

    async def _get_more_photos(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        try:
            field_name_process = "more_photo_process"
            if field_name_process not in preprocessed_data:
                return result
            field_data = preprocessed_data.get(field_name_process, {})
            if not field_data:
                return result

            old_value = None
            if supplier_product.more_photo_process:
                try:
                    old_value = supplier_product.more_photo_process.split(";")
                except Exception:
                    logger.warning("Failed to split more_photo_process")

            result.append(
                {
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": field_data.get("new_value"),
                    "current_product_value": (
                        await self._get_current_more_image_data(product)
                    ),
                    "value_type": "str",
                }
            )
            return result
        except Exception as e:
            logger.info({f"Exception more photo processing: {e}"})
            return []

    async def _get_current_more_image_data(
        self, product: ProductCreate | None
    ) -> list[dict[str, Any]] | None:
        try:
            if not product or not product.external_id:
                return None
            image_repo = self.product_client.image_client.repo
            current_images = await image_repo.get_images(
                image_type=ImageType.MORE_PHOTO.name,
                product_id=int(product.external_id),
            )
            if not current_images:
                return None
            return [
                {
                    "detail_url": current_image.detail_url,
                    "source": current_image.source,
                    "supplier_image_url": current_image.supplier_image_url,
                    "image_id": current_image.external_id,
                }
                for current_image in current_images
            ]
        except Exception:
            return None

    # === Обработка отправленной формы. ===

    async def handle_submission(
        self,
        supplier_product: SupplierProductDetail,
        form_data: FormData,
        preprocessed_data: dict[str, dict[str, Any]],
    ) -> tuple[UUID | None, int | None, dict[str, Any], dict[str, Any]]:
        """
        Обрабатывает отправленную форму.
        Возвращает: product_id_or_None, section_id_or_None,
                    словарь с данными обновления в Битрикс,
                    словарь со старыми данными в Битрикс
        """
        try:
            # Получаем существующий продукт или None
            product = await self._get_product_or_none(supplier_product)
            section_id = (
                getattr(product, "section_id", None) if product else None
            )

            # Подготавливаем данные для обновления
            product_update = await self._prepare_product_update(
                product, form_data
            )
            if not product_update:
                return None, section_id, {}, {}

            clean_dict = product_update.model_dump(exclude_none=True)
            old_bitrix_dict: dict[str, Any] = {}
            if product:
                old_bitrix_dict = product.model_dump(exclude_none=True)

            new_section_id = getattr(product_update, "section_id", None)

            # Сохраняем в CRM
            db_product_id, bitrix_product_id = await self._save_to_crm(
                product, product_update
            )

            # Получаем старые картинки для логов
            old_bitrix_dict.update(
                await self._fetch_old_image_data(bitrix_product_id)
            )

            # Обрабатываем новые картинки
            detail_picture, more_photo = await self._handle_image_fields(
                supplier_product,
                form_data,
                preprocessed_data,
                bitrix_product_id,
            )
            if detail_picture:
                clean_dict["detail_picture"] = detail_picture
            if more_photo:
                clean_dict["more_photo"] = more_photo

            return (
                db_product_id,
                new_section_id or section_id,
                clean_dict,
                old_bitrix_dict,
            )

        except NameNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to handle submission: {e}",
                extra={"product_id": str(supplier_product.id)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process review submission",
            )

    async def _get_product_or_none(
        self,
        supplier_product: SupplierProductDetail,
    ) -> ProductCreate | None:
        """Получает существующий продукт или возвращает None."""
        try:
            if not supplier_product.product_id:
                return None

            return await self.product_client.repo.get_by_id(
                supplier_product.product_id
            )
        except Exception as e:
            logger.warning(
                f"Failed to fetch product {supplier_product.product_id}: {e}"
            )
            return None

    async def _fetch_old_image_data(
        self, bitrix_product_id: int
    ) -> dict[str, Any]:
        """Вспомогательный метод для сбора старых данных изображений."""
        old_data: dict[str, Any] = {}
        try:
            image_repo = self.product_client.image_client.repo

            old_detail = await image_repo.get_detail_by_product_id(
                bitrix_product_id
            )
            if old_detail:
                link = old_detail.supplier_image_url or old_detail.detail_url
                if link:
                    old_data["detail_picture"] = link

            old_more = await image_repo.get_images(
                image_type=ImageType.MORE_PHOTO.name,
                product_id=bitrix_product_id,
            )
            if old_more:
                more_list = [
                    img.supplier_image_url or img.detail_url
                    for img in old_more
                    if (img.supplier_image_url or img.detail_url)
                ]
                if more_list:
                    old_data["more_photo"] = "; ".join(more_list)
        except Exception as e:
            logger.warning(f"Failed to fetch old image data for logs: {e}")
        return old_data

    async def _prepare_product_update(
        self, product: ProductCreate | None, form_data: FormData
    ) -> ProductUpdate | None:
        """
        Подготавливает данные для обновления продукта в CRM.

        Returns:
            ProductUpdate или None, если нет изменений
        """
        # Для нового продукта проверяем обязательные поля
        if not product:
            self._validate_required_fields(form_data)
            product_update = self._create_new_product_data(form_data)
        else:
            product_bitrix_data: dict[str, Any] = {
                "external_id": product.external_id
            }
            product_update = ProductUpdate(**product_bitrix_data)
        # Обновляем поля
        has_changes = await self._update_product_fields(
            product_update, product, form_data
        )
        # Fix common Bitrix validator (crutch)
        if has_changes and not self._should_update_field(form_data, "active"):
            product_update.active = None

        return product_update if has_changes else None

    def _validate_required_fields(self, form_data: FormData) -> None:
        """Проверяет наличие обязательных полей."""
        name = form_data.get(f"{self.FIELD_PREFIX}name")
        if not name:
            logger.warning("Name field is required but missing")
            raise NameNotFoundError("Name of product not found")

    def _create_new_product_data(self, form_data: FormData) -> ProductUpdate:
        """Создает данные для нового продукта."""
        product_bitrix_data: dict[str, Any] = {
            "name": form_data.get(f"{self.FIELD_PREFIX}name"),
            "vat_id": settings.DEFAULT_TAX_RATE_ID,
            "vat_included": True,
            "measure": settings.DEFAULT_MEASURE,
            "active": True,
        }
        return ProductUpdate(**product_bitrix_data)

    async def _update_product_fields(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        form_data: FormData,
    ) -> bool:
        """
        Обновляет поля продукта на основе данных формы.

        Returns:
            True если были изменения
        """
        has_changes = False

        # Простые поля
        simple_fields = FIELDS_SUPPLIER_PRODUCT.get("simple_fields", [])
        for field_name, value_type in simple_fields:
            if self._should_update_field(form_data, field_name):
                if self._update_simple_field(
                    product_update,
                    existing_product,
                    field_name,
                    value_type,
                    form_data,
                ):
                    has_changes = True
        # Сложные поля
        complex_fields = FIELDS_SUPPLIER_PRODUCT.get("complex_fields", [])
        for field_name, value_type in complex_fields:
            if self._should_update_field(form_data, field_name):
                if self._update_complex_field(
                    product_update,
                    existing_product,
                    field_name,
                    value_type,
                    form_data,
                ):
                    has_changes = True
        # Специальные поля
        special_fields = FIELDS_SUPPLIER_PRODUCT.get("individual_fields", [])
        for field_name, value_type in special_fields:
            if self._should_update_field(form_data, field_name):
                if field_name in ["detail_picture", "more_photos"]:
                    has_changes = True
                else:
                    if await self._update_special_field(
                        product_update,
                        existing_product,
                        field_name,
                        value_type,
                        form_data,
                    ):
                        has_changes = True
        return has_changes

    def _should_update_field(
        self, form_data: FormData, field_name: str
    ) -> bool:
        """Проверяет, нужно ли обновлять поле."""
        try:
            if field_name == "detail_picture":
                return bool(form_data.get("pic_upload_choice"))
            elif field_name == "more_photos":
                return bool("gallery_block_active" in form_data)
            elif field_name == "description":
                field_key = f"{self.FIELD_PREFIX}{field_name}"
                update_key = f"{self.UPDATE_PREFIX}{field_name}"
                return (
                    (
                        field_key in form_data
                        and form_data.get(update_key) == self.VALUE_ON
                    )
                    or "upload_description" in form_data
                    or "upload_add_description" in form_data
                )
            elif field_name in ["characteristics", "complects"]:
                need_upd = form_data.get(f"{self.UPDATE_PREFIX}{field_name}")
                return bool(need_upd == self.VALUE_ON)
            else:
                field_key = f"{self.FIELD_PREFIX}{field_name}"
                update_key = f"{self.UPDATE_PREFIX}{field_name}"
                return (
                    field_key in form_data
                    and form_data.get(update_key) == self.VALUE_ON
                )
        except Exception as e:
            logger.error(f"Exception should update field: {e}")
            return False

    def _update_simple_field(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        value_type: str,
        form_data: FormData,
    ) -> bool:
        """Обновляет простое поле."""
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        typed_value = self.transformer.cast_value(form_value, value_type)

        if typed_value is None or not typed_value:
            return False

        current_value = getattr(existing_product, field_name, None)
        if current_value != typed_value:
            setattr(product_update, field_name, typed_value)
            return True

        return False

    def _update_complex_field(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        value_type: str,
        form_data: FormData,
    ) -> bool:
        """Обновляет сложное поле."""
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        typed_value = self.transformer.cast_value(form_value, value_type)

        if not typed_value:
            return False

        current = getattr(existing_product, field_name, None)
        current_value = (
            current.value if current and hasattr(current, "value") else None
        )

        if current_value != typed_value:
            field_data = {"value": typed_value}
            setattr(product_update, field_name, FieldValue(**field_data))
            return True

        return False

    async def _update_special_field(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        value_type: str,
        form_data: FormData,
    ) -> bool:
        """Обновляет специальное поле."""
        if field_name == "brend":
            return self._handle_field_brand(
                product_update, existing_product, field_name, form_data
            )
        elif field_name == "internal_section_id":
            return await self._handle_field_section(
                product_update, existing_product, field_name, form_data
            )
        elif field_name in ["characteristics", "complects"]:
            return await self._handle_field_items(
                product_update, existing_product, field_name, form_data
            )
        elif field_name == "description":
            return self._handle_field_description(
                product_update, existing_product, field_name, form_data
            )
        return False

    def _handle_field_brand(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        form_data: FormData,
    ) -> bool:
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        # Если значение не передано в форме - ничего не делаем
        if form_value is None:
            logger.debug("No value for brand field in form")
            return False
        current_value = None
        try:
            current = getattr(existing_product, field_name, None)
            current_value = (
                current.value
                if current and hasattr(current, "value")
                else None
            )
        except Exception:
            logger.warning(f"Exception getting current value {field_name}")

        typed_value = self._determine_brand_value(form_value, current_value)
        if typed_value is not None:
            field_data = {"value": typed_value}
            setattr(product_update, field_name, FieldValue(**field_data))
            return True
        return False

    def _determine_brand_value(
        self, form_value: Any, current_value: Any
    ) -> str | None:
        """
        Определяет значение бренда для установки.

        Returns:
            - Пустую строку если нужно удалить бренд
            - Строковое представление ID если бренд изменился
            - None если изменений нет
        """
        if (
            not form_value or form_value.strip() == ""
        ) and current_value is not None:
            return ""
        if not form_value:
            return None
        # Пытаемся преобразовать в int для сравнения
        try:
            form_int_value = int(form_value)

            # Если текущее значение существует и совпадает с новым -
            # без изменений
            if current_value is not None:
                try:
                    current_int = int(current_value)
                    if current_int == form_int_value:
                        return None
                except (ValueError, TypeError):
                    pass  # Текущее значение не является числом

            # Значение изменилось или текущего нет
            return str(form_int_value)

        except ValueError:
            # Форма передала нечисловое значение
            logger.warning(f"Brand form value is not a number: {form_value}")
            return None

    async def _handle_field_section(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        form_data: FormData,
    ) -> bool:
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        # Если значение не передано в форме - ничего не делаем
        if form_value is None:
            logger.debug("No value for section field in form")
            return False

        current_field_name = "section_id"
        current_val = getattr(existing_product, current_field_name, None)
        current_value = self._to_int_or_none(current_val)

        form_value_str = str(form_value).strip()
        if not form_value_str:
            if current_value:
                # TODO: Если раздел заполнен - обнулить ?
                return True
            return False

        section_value = form_data.get(f"{self.FIELD_PREFIX}supplier_category")
        subsection_value = form_data.get(
            f"{self.FIELD_PREFIX}supplier_subcategory"
        )
        section_int = self._to_int_or_none(section_value)
        subsection_int = self._to_int_or_none(subsection_value)
        section_new_id = (
            await self.product_section_client.handle_section_review(
                form_value_str, current_value, section_int, subsection_int
            )
        )
        if section_new_id:
            setattr(product_update, current_field_name, section_new_id)
            return True
        return False

    def _to_int_or_none(self, value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    async def _handle_field_items(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        form_data: FormData,
    ) -> bool:
        form_values = form_data.getlist(f"{self.FIELD_PREFIX}{field_name}[]")
        clean_values: list[str] = [
            str(val).strip() for val in form_values if str(val).strip()
        ]
        current_field_name = self.MAPPING_FIELDS.get(field_name)
        if not current_field_name:
            return False

        current_values = self._get_list_complex_product_value(
            existing_product, field_name
        )
        new_value: list[Any] | None = None

        if not clean_values:
            # обнуляем если заполнено
            new_value = [] if current_values else None
        else:
            if current_values != clean_values:
                new_value = self._create_list_complex_product_value(
                    clean_values
                )
        if new_value is not None:
            setattr(product_update, current_field_name, new_value)
            return True
        return False

    def _create_complex_product_value(
        self, value: str, type_field: str = "HTML"
    ) -> FieldValue | None:
        try:
            complex_value = FieldText(text_field=value, type_field=type_field)
            return FieldValue(value=complex_value)
        except Exception:
            return None

    def _create_list_complex_product_value(
        self, values: list[str]
    ) -> list[FieldValue] | None:
        try:
            return [FieldValue(value=value) for value in values]
        except Exception:
            return None

    def _handle_field_description(
        self,
        product_update: ProductUpdate,
        existing_product: ProductCreate | None,
        field_name: str,
        form_data: FormData,
    ) -> bool:
        need_update = False
        # Обновляем description если проставлена галка
        if "upload_description" in form_data:
            new_description = form_data.get("new_description", "")
            if new_description:
                old_description = getattr(existing_product, field_name, None)
                if old_description != new_description:
                    setattr(product_update, field_name, new_description)
                    need_update = True

        # Обновляем additional_description если проставлена галка
        if "upload_add_description" in form_data:
            add_description_field = "additional_description"
            new_add_description = form_data.get("new_add_description", "")
            if new_add_description:
                old_add_description = self._get_complex_product_value(
                    existing_product, add_description_field
                )
                if old_add_description != new_add_description:
                    setattr(
                        product_update,
                        add_description_field,
                        self._create_complex_product_value(
                            new_add_description
                        ),
                    )
                    need_update = True

        # Обновление описания для печати (description_for_print)
        field_key = f"{self.FIELD_PREFIX}{field_name}"
        update_key = f"{self.UPDATE_PREFIX}{field_name}"

        if not (
            field_key in form_data
            and form_data.get(update_key) == self.VALUE_ON
        ):
            return need_update

        form_value = form_data.get(field_key)
        # Если значение не передано в форме - ничего не делаем
        if form_value is None:
            logger.debug("No value for description field in form")
            return need_update

        form_value = str(form_value).strip()
        current_field_name = "description_for_print"
        current_value = self._get_complex_product_value(
            existing_product, current_field_name
        )
        if not form_value:
            if current_value:
                new_empty_value = self._create_complex_product_value("", "")
                setattr(product_update, current_field_name, new_empty_value)
                return True
            return need_update

        if current_value != form_value:
            type_form_field = form_data.get("editor_mode")
            if type_form_field and type_form_field == "text":
                type_field = "TEXT"
            else:
                type_field = "HTML"
            new_value = self._create_complex_product_value(
                form_value, type_field
            )
            if new_value:
                setattr(product_update, current_field_name, new_value)
                return True

        return need_update

    async def _save_to_crm(
        self,
        existing_product: ProductCreate | None,
        product_update: ProductUpdate,
    ) -> tuple[UUID | None, int]:
        """Сохраняет продукт в CRM и возвращает локальный ID."""
        bitrix_client = self.product_client.bitrix_client
        external_id = None

        try:
            if existing_product:
                await bitrix_client.update(product_update)
                external_id = existing_product.external_id
            else:
                external_id = await bitrix_client.create(product_update)

            if not external_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create/update product in Bitrix",
                )

            # Импортируем из Bitrix обратно
            imported, _ = await self.product_client.import_from_bitrix(
                int(external_id)
            )
            return imported.id if imported else None, int(external_id)

        except Exception as e:
            logger.error(f"Failed to save to CRM: {e}", exc_info=True)
            raise

    async def _handle_image_fields(
        self,
        supplier_product: SupplierProductDetail,
        form_data: FormData,
        preprocessed_data: dict[str, dict[str, Any]],
        product_id: int,
    ) -> tuple[str | None, str | None]:
        """
        Обрабатывает переданные картинки.
        """

        try:
            detail_image = await self._handle_detail_image(
                supplier_product,
                form_data,
                preprocessed_data,
                product_id,
            )
            more_images = await self._handle_more_images(
                supplier_product,
                form_data,
                preprocessed_data,
                product_id,
            )
            return detail_image, more_images
        except Exception as e:
            logger.error(f"Error loading pictures: {e}")
            return None, None

    async def _handle_detail_image(
        self,
        supplier_product: SupplierProductDetail,
        form_data: FormData,
        preprocessed_data: dict[str, dict[str, Any]],
        bitrix_product_id: int,
    ) -> str | None:
        """
        Обрабатывает детальную картинку.
        """

        try:
            # --- НАЧАЛО БЛОКА ОБРАБОТКИ ДЕТАЛЬНОЙ КАРТИНКИ ---

            # Получаем выбор пользователя
            pic_upload_choice = form_data.get("pic_upload_choice")
            if not pic_upload_choice:
                logger.info(
                    "Не выбран вариант изображения. "
                    "Пропускаем обновление картинки."
                )
                return None

            if pic_upload_choice in ["old", "new"]:
                # Переменная для хранения результата, который пойдет в Битрикс
                image_to_update = None

                # Получаем значения старой и новой картинки (из скрытых полей)
                pic_old_value = form_data.get("pic_old_value")
                pic_new_value = form_data.get("pic_new_value")

                # Получаем данные из 3-й колонки
                pic_current_source = form_data.get("pic_current_source")
                pic_current_supplier_url = form_data.get(
                    "pic_current_supplier_url"
                )

                if pic_upload_choice == "old" and pic_old_value:
                    image_to_update = pic_old_value
                elif pic_upload_choice == "new" and pic_new_value:
                    image_to_update = pic_new_value

                if image_to_update:
                    # Проверяем, не совпадает ли с текущим
                    if (
                        image_to_update == pic_current_supplier_url
                        and supplier_product.source.value == pic_current_source
                    ):
                        return None

                    image_client = self.product_client.image_client
                    supplier_picture_data: dict[str, Any] = {
                        "source": supplier_product.source,
                        "supplier_image_url": str(image_to_update),
                    }
                    await image_client.create_product_picture_from_url(
                        bitrix_product_id,
                        str(image_to_update),
                        ImageType.DETAIL_PICTURE,
                        supplier_picture_data,
                    )
                    await image_client.import_from_bitrix_by_product_id(
                        bitrix_product_id
                    )
                    return str(image_to_update)
            elif pic_upload_choice == "custom":
                # --- ВАРИАНТ 3: Загрузка своего файла ---
                # Получаем данные из 4-й колонки (загрузка файла)
                raw_base64 = form_data.get("pic_custom_base64", "")
                filename = form_data.get("pic_custom_name", "")

                if raw_base64 and filename:
                    logger.info(f"Подготовка файла к загрузке: {filename}")
                    try:
                        raw_base64 = str(raw_base64)
                        filename = str(filename)

                        file_info = self.build_file_data(raw_base64, filename)
                        if not file_info:
                            return None

                        image_client = self.product_client.image_client
                        await image_client.create_product_picture_from_dict(
                            bitrix_product_id,
                            file_info,
                            ImageType.DETAIL_PICTURE,
                        )
                        await image_client.import_from_bitrix_by_product_id(
                            bitrix_product_id
                        )
                        logger.info(
                            "Base64 отправлен "
                            f"(длина: {file_info.get('file_size', '-')})."
                        )
                        return filename  # type: ignore[no-any-return]
                    except Exception as e:
                        logger.error(
                            f"Failed to upload custom detail image: {e}"
                        )
        except Exception as e:
            logger.error(f"Error loading detail pictures: {e}")
            return None
        return None

    def build_file_data(
        self, raw_base64: str, filename: str
    ) -> dict[str, Any]:
        try:
            # Очистка строки от пробелов и переносов
            raw_base64 = (
                raw_base64.replace(" ", "").replace("\n", "").replace("\r", "")
            )

            # 1. Извлекаем content_type из заголовка Data URI
            # (если он есть)
            # Формат строки: "data:image/png;base64,iVBORw0KGgo..."
            content_type = "application/octet-stream"
            clean_base64 = raw_base64

            if "," in raw_base64:
                header, payload = raw_base64.split(",", 1)
                # Парсим заголовок "data:image/png;base64"
                # Разбиваем по ";" чтобы отделить mime-type от
                # encoding
                header_parts = header.split(";")
                if header_parts and header_parts[0].startswith("data:"):
                    content_type = header_parts[0].replace("data:", "")

                # Чистый Base64 без заголовка для декодирования
                clean_base64 = payload
            else:
                # Если заголовка нет (строка пришла чистой),
                # пробуем угадать тип по имени файла
                guessed_type, _ = mimetypes.guess_type(filename)
                if guessed_type:
                    content_type = guessed_type

            # 2. Декодируем Base64 в байты (raw_bytes)
            file_bytes = base64.b64decode(clean_base64)

            # 3. Вычисляем размер файла (file_size)
            total_size = len(file_bytes)
            if total_size > settings.MAX_FILE_SIZE:
                logger.error(
                    f"File too large (header): {total_size} bytes,"
                    f" max allowed: {settings.MAX_FILE_SIZE} bytes"
                )
                raise ValueError("File size exceeds limit")

            # 4. Вычисляем SHA256 хэш (file_hash)
            sha256_hash = hashlib.sha256()
            sha256_hash.update(file_bytes)

            # 5. Формируем итоговый словарь file_info
            file_info: dict[str, Any] = {
                "content": clean_base64,
                "filename": filename,
                "content_type": content_type,
                "file_size": total_size,
                "raw_bytes": file_bytes,
                "file_hash": sha256_hash.hexdigest(),
            }

            logger.info(
                f"Файл обработан. Размер: {total_size} байт, "
                f"Тип: {content_type}, "
                f"Хэш: {file_info['file_hash'][:8]}..."
            )
            return file_info

        except (binascii.Error, ValueError) as e:
            logger.error(f"Base64 decode error for {filename}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error processing file {filename}: {e}")
            return {}

    async def _handle_more_images(
        self,
        supplier_product: SupplierProductDetail,
        form_data: FormData,
        preprocessed_data: dict[str, dict[str, Any]],
        bitrix_product_id: int,
    ) -> str | None:
        """
        Обрабатывает переданные картинки.
        """
        # --- ШАГ 1: Анализ текущих изображений (Столбец 3) ---

        # Собираем ID, которые были отображены в форме
        # (чтобы понять, что удалили)
        # Ключи в форме: curr_img_123_source, curr_img_456_source ...
        current_ids_on_screen: set[int] = set()
        pattern = re.compile(r"curr_img_(\d+)_source")
        for key in form_data.keys():
            # match = re.match(r"curr_img_(\d+)_source", key)
            match = pattern.match(key)
            if match:
                try:
                    current_ids_on_screen.add(int(match.group(1)))
                except ValueError:
                    continue

        # Собираем ID, которые пользователь оставил отмеченными
        # (чекбоксы "Оставить")
        # name="more_pics_current_ids"
        keep_ids_str = form_data.getlist("more_pics_current_ids")
        keep_ids = {int(id_str) for id_str in keep_ids_str if id_str.isdigit()}

        # Вычисляем ID для удаления (те, что были на экране, но галку сняли)
        ids_to_delete = current_ids_on_screen - keep_ids

        # Удаляем в Битриксе
        image_client = self.product_client.image_client
        if ids_to_delete:
            logger.info(f"Deleting images IDs: {ids_to_delete}")
            for img_id in ids_to_delete:
                try:
                    await image_client.bitrix_client.delete_picture_by_id(
                        bitrix_product_id, img_id
                    )
                except Exception as e:
                    print(f"Error deleting image {img_id}: {e}")
            await image_client.import_from_bitrix_by_product_id(
                bitrix_product_id
            )

        # --- ШАГ 2: Сбор ссылок для добавления (Столбцы 1 и 2) ---
        # с проверкой уникальности
        kept_urls: set[str] = set()
        try:
            images = await image_client.repo.get_images(
                product_id=bitrix_product_id,
                source=supplier_product.source,
            )
            for image in images:
                if image.supplier_image_url:
                    kept_urls.add(image.supplier_image_url)
        except Exception as e:
            logger.warning(
                f"Failed to fetch existing images for deduplication: {e}"
            )

        urls_to_upload: list[str] = []

        for url_key in ["more_pics_old_urls", "more_pics_new_urls"]:
            # Столбец 1: Старые значения (name="more_pics_old_urls")
            # Столбец 2: Новые значения (name="more_pics_new_urls")
            for url in form_data.getlist(url_key):
                if url and url not in kept_urls:
                    url = str(url)
                    urls_to_upload.append(url)
                    kept_urls.add(url)

        # Убираем дубликаты внутри самих списков old/new
        # (если вдруг пришли дубли)
        urls_to_upload = list(set(urls_to_upload))
        more_pictures: list[str] = []

        # Загружаем по ссылкам
        if urls_to_upload:
            logger.info(f"Uploading {len(urls_to_upload)} images by URL...")
            for url in urls_to_upload:
                try:
                    supplier_picture_data: dict[str, Any] = {
                        "source": supplier_product.source,
                        "supplier_image_url": url,
                    }

                    await image_client.create_product_picture_from_url(
                        bitrix_product_id,
                        url,
                        ImageType.MORE_PHOTO,
                        supplier_picture_data,
                    )
                    more_pictures.append(url)
                except Exception as e:
                    print(f"Failed to upload URL {url}: {e}")

            await image_client.import_from_bitrix_by_product_id(
                bitrix_product_id
            )

        # --- ШАГ 3: Загрузка пользовательского файла (Столбец 4) ---

        if form_data.get("more_pics_custom_check"):
            raw_base64 = form_data.get("more_pics_custom_base64")
            filename = form_data.get("more_pics_custom_name")

            if raw_base64 and filename:
                logger.info(f"Uploading custom file: {filename}")
                try:
                    raw_base64 = str(raw_base64)
                    filename = str(filename)

                    file_info = self.build_file_data(raw_base64, filename)
                    if not file_info:
                        return None

                    await image_client.create_product_picture_from_dict(
                        bitrix_product_id,
                        file_info,
                        ImageType.MORE_PHOTO,
                    )
                    more_pictures.append(filename)
                    await image_client.import_from_bitrix_by_product_id(
                        bitrix_product_id
                    )
                    logger.info(
                        "Base64 отправлен "
                        f"(длина: {file_info.get('file_size', '-')})."
                    )
                except Exception as e:
                    logger.error(f"Error loading castom more photo: {e}")

        return "; ".join(more_pictures) if more_pictures else None
