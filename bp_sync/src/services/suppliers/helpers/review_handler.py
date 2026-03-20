from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from starlette.datastructures import FormData

from core.exceptions.supplier_exceptions import NameNotFoundError
from core.logger import logger
from core.settings import settings
from schemas.enums import BrandEnum
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

    # Префиксы для полей формы
    FIELD_PREFIX = "field_"
    UPDATE_PREFIX = "update_"

    def __init__(
        self,
        product_client: ProductClient,
        product_section_client: ProductsectionClient,
    ):
        self.product_client = product_client
        self.product_section_client = product_section_client
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
            Кортеж (простые поля, комплексные поля)
        """
        try:
            review_data = self._prepare_simple_fields(
                transformed_logs, product
            )
            review_data.extend(
                self._prepare_complex_fields(transformed_logs, product)
            )
            review_special_data = self._prepare_special_fields(
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
            field_data = self._get_value_special_fields(
                field_name,
                transformed_logs,
                preprocessed_data,
                product,
                supplier_product,
            )
            review_special_data.extend(field_data)
        return review_special_data

    def _get_value_special_fields(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        if field_name == "brend":
            return self._get_brand(
                field_name, transformed_logs, product, supplier_product
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
            return self._get_list_items(field_name, preprocessed_data, product)

        elif field_name == "description":
            return self._get_description(
                field_name,
                transformed_logs,
                preprocessed_data,
                product,
                supplier_product,
            )
        elif field_name == "detail_picture":
            return self._get_detail_picture(
                field_name,
                transformed_logs,
                preprocessed_data,
                product,
                supplier_product,
            )
        elif field_name == "more_photos":
            return self._get_more_photos(
                field_name,
                transformed_logs,
                preprocessed_data,
                product,
                supplier_product,
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
            current_val = self._get_complex_product_value(product, field_name)

            return [
                {
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "current_product_value": current_val,
                    "value_type": "str",
                }
            ]
        except Exception:
            return result

    def _transform_items(
        self, items: list[Any] | None, field_name: str, field_type: str
    ) -> str | None:
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
                result = None
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
        return "\n".join(items_list)

    def _get_complex_product_value(
        self, product: ProductCreate | None, field_name: str
    ) -> str | None:
        try:
            current_data = getattr(product, field_name, None)
            if current_data:
                current_field = current_data.value
                if current_field:
                    return str(current_field.text_field)
            return None
        except Exception:
            return None

    def _get_description(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        # TODO: upd
        return result

    def _get_detail_picture(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        # TODO: upd
        return result

    def _get_more_photos(
        self,
        field_name: str,
        transformed_logs: dict[str, dict[str, Any]],
        preprocessed_data: dict[str, dict[str, Any]],
        product: ProductCreate | None,
        supplier_product: SupplierProductDetail,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        # TODO: upd
        return result

    async def handle_submission(
        self,
        supplier_product: SupplierProductDetail,
        form_data: FormData,
        preprocessed_data: dict[str, dict[str, Any]],
    ) -> tuple[UUID | None, int | None]:
        """
        Обрабатывает отправленную форму.
        Возвращает: external_id_or_None
        """
        try:
            # Получаем существующий продукт или создаем новый
            product = await self._get_product_or_none(supplier_product)
            section_id = getattr(product, "section_id", None)
            # Подготавливаем данные для обновления
            product_update = await self._prepare_product_update(
                product, form_data
            )

            if not product_update:
                return None, section_id

            new_section_id = getattr(product_update, "section_id", None)
            # Сохраняем в CRM
            return (
                await self._save_to_crm(product, product_update),
                new_section_id or section_id,
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
        if not supplier_product.product_id:
            return None

        return await self.product_client.repo.get_by_id(
            supplier_product.product_id
        )

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
        field_key = f"{self.FIELD_PREFIX}{field_name}"
        update_key = f"{self.UPDATE_PREFIX}{field_name}"

        return field_key in form_data and form_data.get(update_key) == "on"

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

        if typed_value is None or not typed_value:
            return False

        current = getattr(existing_product, field_name, None)
        current_value = current.value if current else None

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
        # TODO: реализовать логику для специальных полей
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
            current_value = current.value if current else None
        except Exception:
            logger.warning("Exception getting current value")
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
        existing_product: Any | None,
        field_name: str,
        form_data: FormData,
    ) -> bool:
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        # Если значение не передано в форме - ничего не делаем
        if form_value is None:
            logger.debug("No value for section field in form")
            return False
        current_field_name = "section_id"
        current_value = getattr(existing_product, current_field_name, None)
        current_value = self._to_int_or_none(current_value)
        form_value = str(form_value).strip()
        if not form_value:
            if current_value:
                # TODO: Если раздел заполнен - обнулить ?
                return True
            return False
        section_value = form_data.get(f"{self.FIELD_PREFIX}supplier_category")
        subsection_value = form_data.get(
            f"{self.FIELD_PREFIX}supplier_subcategory"
        )
        section_value = self._to_int_or_none(section_value)
        subsection_value = self._to_int_or_none(subsection_value)
        section_new_id = (
            await self.product_section_client.handle_section_review(
                form_value, current_value, section_value, subsection_value
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
        form_value = form_data.get(f"{self.FIELD_PREFIX}{field_name}")
        # Если значение не передано в форме - ничего не делаем
        if form_value is None:
            logger.debug("No value for section field in form")
            return False
        current_value = self._get_complex_product_value(
            existing_product, field_name
        )
        form_value = str(form_value).strip()
        if not form_value:
            if current_value:
                # TODO: Если значение заполнено - обнулить ?
                return True
            return False
        new_value = None
        if current_value != form_value:
            new_value = self._create_complex_product_value(form_value)

        if new_value:
            setattr(product_update, field_name, new_value)
            return True
        return False

    def _create_complex_product_value(self, value: str) -> FieldValue | None:
        try:
            complex_value = FieldText(text_field=value, type_field="HTML")
            return FieldValue(value=complex_value)
        except Exception:
            return None

    async def _save_to_crm(
        self,
        existing_product: ProductCreate | None,
        product_update: ProductUpdate,
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
