from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from starlette.datastructures import FormData

from core.exceptions.supplier_exceptions import NameNotFoundError
from core.logger import logger
from core.settings import settings
from schemas.fields import FIELDS_SUPPLIER_PRODUCT
from schemas.product_schemas import FieldValue, ProductCreate, ProductUpdate
from schemas.supplier_schemas import SupplierProductDetail
from services.products.product_services import ProductClient

from .data_transformer import DataTransformer


class ReviewHandler:
    """Обрабатывает логику ревью: подготовка данных и сохранение формы."""

    # Поля, которые всегда должны присутствовать
    REQUIRED_FIELDS = {"name"}

    # Префиксы для полей формы
    FIELD_PREFIX = "field_"
    UPDATE_PREFIX = "update_"

    def __init__(self, product_client: ProductClient):
        self.product_client = product_client
        self.transformer = DataTransformer()

    def prepare_review_context(
        self,
        supplier_product: SupplierProductDetail,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Готовит данные для отображения в шаблоне.

        Returns:
            Кортеж (простые поля, сложные поля)
        """
        try:
            review_data = self._prepare_simple_fields(
                transformed_logs, product
            )
            review_data.extend(
                self._prepare_complex_fields(transformed_logs, product)
            )
            review_special_data = self._prepare_special_fields(
                preprocessed_data, product
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
        self, transformed_logs: dict[str, dict[str, Any]], product: Any | None
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
        self, transformed_logs: dict[str, dict[str, Any]], product: Any | None
    ) -> list[dict[str, Any]]:
        """Подготавливает сложные поля для отображения."""
        review_data: list[dict[str, Any]] = []
        complex_fields = FIELDS_SUPPLIER_PRODUCT.get("complex_fields", [])

        for field_name, value_type in complex_fields:
            if field_name not in transformed_logs:
                continue

            field_data = transformed_logs[field_name]
            current = getattr(product, field_name, None)
            current_val = current.value if current else None

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

    def _prepare_special_fields(
        self, preprocessed_data: dict[str, dict[str, Any]], product: Any | None
    ) -> list[dict[str, Any]]:
        """Подготавливает простые поля для отображения."""
        review_special_data: list[dict[str, Any]] = []
        special_fields = FIELDS_SUPPLIER_PRODUCT.get("individual_fields", ())
        logger.info(special_fields)
        # TODO: add data to review_special_data

        return review_special_data

    async def handle_submission(
        self,
        supplier_product: SupplierProductDetail,
        form_data: FormData,
        preprocessed_data: dict[str, dict[str, Any]],
    ) -> UUID | None:
        """
        Обрабатывает отправленную форму.
        Возвращает: external_id_or_None
        """
        try:
            # Получаем существующий продукт или создаем новый
            product = await self._get_product_or_none(supplier_product)

            # Подготавливаем данные для обновления
            product_update = await self._prepare_product_update(
                product, form_data
            )

            if not product_update:
                return None

            # Сохраняем в CRM
            return await self._save_to_crm(product, product_update)

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
    ) -> Any | None:
        """Получает существующий продукт или возвращает None."""
        if not supplier_product.product_id:
            return None

        return await self.product_client.repo.get_by_id(
            supplier_product.product_id
        )

    def _validate_required_fields(self, form_data: FormData) -> None:
        """Проверяет наличие обязательных полей."""
        name = form_data.get(f"{self.FIELD_PREFIX}name")
        if not name:
            logger.warning("Name field is required but missing")
            raise NameNotFoundError("Name of product not found")

    async def _prepare_product_update(
        self, product: Any | None, form_data: FormData
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

        return product_update if has_changes else None

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
        existing_product: Any | None,
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
                if self._update_special_field(
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
        field_key = f"{self.FIELD_PREFIX}{field_name}"
        update_key = f"{self.UPDATE_PREFIX}{field_name}"

        return field_key in form_data and form_data.get(update_key) == "on"

    def _update_simple_field(
        self,
        product_update: ProductUpdate,
        existing_product: Any | None,
        field_name: str,
        value_type: str,
        form_data: FormData,
    ) -> bool:
        """Обновляет простое поле."""
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        typed_value = self.transformer.cast_value(form_value, value_type)

        if typed_value is None:
            return False

        current_value = getattr(existing_product, field_name, None)
        if current_value != typed_value:
            setattr(product_update, field_name, typed_value)
            return True

        return False

    def _update_complex_field(
        self,
        product_update: ProductUpdate,
        existing_product: Any | None,
        field_name: str,
        value_type: str,
        form_data: FormData,
    ) -> bool:
        """Обновляет сложное поле."""
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        typed_value = self.transformer.cast_value(form_value, value_type)

        if typed_value is None:
            return False

        current = getattr(existing_product, field_name, None)
        current_value = current.value if current else None

        if current_value != typed_value:
            field_data = {"value": typed_value}
            setattr(product_update, field_name, FieldValue(**field_data))
            return True

        return False

    def _update_special_field(
        self,
        product_update: ProductUpdate,
        existing_product: Any | None,
        field_name: str,
        value_type: str,
        form_data: FormData,
    ) -> bool:
        """Обновляет специальное поле."""
        # TODO: реализовать логику для специальных полей
        # form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        # typed_value = self.transformer.cast_value(form_value, value_type)

        # if typed_value is None:
        #     return False

        # current_value = getattr(existing_product, field_name, None)
        # if current_value != typed_value:
        #     setattr(product_update, field_name, typed_value)
        #     return True

        return False

    async def _save_to_crm(
        self, existing_product: Any | None, product_update: ProductUpdate
    ) -> UUID | None:
        """Сохраняет продукт в CRM и возвращает локальный ID."""
        bitrix_client = self.product_client.bitrix_client

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

            return imported.id if imported else None

        except Exception as e:
            logger.error(f"Failed to save to CRM: {e}", exc_info=True)
            raise
