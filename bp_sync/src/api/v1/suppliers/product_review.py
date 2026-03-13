from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.logger import logger
from core.settings import settings
from schemas.enums import SourcesProductEnum
from services.dependencies.dependencies import get_product_service
from services.dependencies.dependencies_suppliers import (
    get_supplier_product_repo,
    get_supplier_service,
)
from services.products.product_services import ProductClient
from services.suppliers.repositories.supplier_product_repo import (
    SupplierProductRepository,
)
from services.suppliers.supplier_services import SupplierClient

# from ..schemas.response_schemas import SuccessResponse

supplier_product_review = APIRouter()
templates = Jinja2Templates(directory=f"{settings.BASE_DIR}/templates")


@supplier_product_review.get(  # type: ignore[misc]
    "/", response_class=HTMLResponse
)
async def read_root(request: Request) -> HTMLResponse:
    """Выбор источника данных"""
    # Получаем список возможных источников из Enum
    sources = [e.value for e in SourcesProductEnum]
    return templates.TemplateResponse(
        "index.html", {"request": request, "sources": sources}
    )


@supplier_product_review.get(  # type: ignore[misc]
    "/products/", response_class=HTMLResponse
)
async def get_products_list(
    request: Request,
    source: str,
    supplier_product_repo: SupplierProductRepository = Depends(
        get_supplier_product_repo
    ),
) -> HTMLResponse:
    """Список SupplierProduct для выбранного source, где needs_review=True"""
    try:
        source_products = SourcesProductEnum(source)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source")
    try:
        products = await supplier_product_repo.get_supplier_products_by_source(
            source_products
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Exception during fetching products",
        )
    return templates.TemplateResponse(
        "list.html",
        {"request": request, "source": source, "products": products},
    )


@supplier_product_review.get(  # type: ignore[misc]
    "/review/{supp_product_id}", response_class=HTMLResponse
)
async def review_product(
    request: Request,
    supp_product_id: UUID,
    supplier_service: SupplierClient = Depends(get_supplier_service),
    product_service: ProductClient = Depends(get_product_service),
) -> HTMLResponse:
    """
    Страница редактирования.
    Загружает SupplierProduct, его логи (не обработанные) и связанный Product.
    """
    supp_product = await supplier_service.get_supplier_product_data_for_review(
        supp_product_id
    )
    product = None
    if product_id := supp_product.product_id:
        logger.info(product_id)
        product = None  # await product_service.get_changes_b24_db()
    # Собираем данные для отображения
    # Формируем список словарей для удобства в шаблоне
    review_data: list[dict[str, Any]] = []
    # for log in logs:
    #     current_product_value = None
    #     if product:
    #         # Пытаемся получить текущее значение из Product
    #         current_product_value = safe_getattr(product, log.field_name)

    #     review_data.append({
    #         "log_id": log.id,
    #         "field_name": log.field_name,
    #         "old_value": log.old_value,
    #         "new_value": log.new_value,
    #         "current_product_value": current_product_value,
    #         "value_type": log.value_type
    #     })

    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "supplier_product": supp_product,
            "product": product,
            "review_data": review_data,
        },
    )


@supplier_product_review.post(  # type: ignore[misc]
    "/review/{supp_product_id}"
)
async def process_review(
    request: Request,
    supp_product_id: UUID,
    supplier_service: SupplierClient = Depends(get_supplier_service),
    product_service: ProductClient = Depends(get_product_service),
) -> RedirectResponse:
    """
    Обработка формы.
    Обновляет Product, отмечает логи как обработанные,
    снимает флаг needs_review.
    """
    # form_data = await request.form()
    supp_product = await supplier_service.get_supplier_product_data_for_review(
        supp_product_id
    )
    # # 1. Загружаем объекты снова
    # supp_prod_query = select(SupplierProduct).where(
    #     SupplierProduct.id == supplier_product_id
    # )
    # supp_prod_res = await db.execute(supp_prod_query)
    # supplier_product = supp_prod_res.scalar_one_or_none()

    # if not supplier_product:
    #     raise HTTPException(404, "Product not found")

    # product = None
    # if supplier_product.product_id:
    #     prod_query = select(Product).where(
    #         Product.id == supplier_product.product_id
    #     )
    #     prod_res = await db.execute(prod_query)
    #     product = prod_res.scalar_one_or_none()

    # # Если привязки к Product нет, мы не можем сохранить изменения в
    # # карточку товара.
    # # Логика может быть разной: либо создавать товар, либо игнорировать.
    # # Здесь предположим, что товар ДОЛЖЕН существовать,
    # # иначе просто отмечаем логи.

    # if product:
    #     # Проходимся по данным формы
    #     # Ключи в форме будут вида "field_{log_id}"
    #     for key, value in form_data.items():
    #         if key.startswith("field_"):
    #             log_id_str = key.replace("field_", "")
    #             try:
    #                 log_id = uuid.UUID(log_id_str)

    #                 # Находим лог, чтобы知道 какое поле обновляем
    #                 log_query = select(SupplierProductChangeLog).where(
    #                     SupplierProductChangeLog.id == log_id,
    #                     SupplierProductChangeLog.supplier_product_id
    #                      == supplier_product_id
    #                 )
    #                 log_res = await db.execute(log_query)
    #                 log = log_res.scalar_one_or_none()

    #                 if log:
    # Обновляем поле в Product
    # Примечание: Здесь нужна осторожность с типами данных.
    # form_data возвращает строки. Лучше привести к типу поля или
    # использовать Pydantic для валидации. Для простоты - setattr.
    # Можно добавить логику преобразования типов на основе log.value_type

    #                     final_value = value
    #                     if log.value_type == "int":
    #                         final_value = int(value) if value else None
    #                     elif log.value_type == "float":
    #                         final_value = float(value) if value else None
    #                     elif log.value_type == "bool":
    #                         final_value = (
    #                             value.lower() in ['true', '1', 'yes']
    #                         )

    #                     setattr(product, log.field_name, final_value)

    #                     # Помечаем лог как обработанный
    #                     log.is_processed = True
    #                     # (Опционально) можно заполнить кто и когда обработал
    #                     # log.processed_at = datetime.now()

    #             except ValueError:
    #                 continue # Неверный формат ID
    # else:
    #     # Если продукта нет, просто помечаем логи
    #     # как просмотренные/обработанные
    #     # чтобы они исчезли из списка задач
    #     pass

    # # Снимаем флаг needs_review с SupplierProduct
    # supplier_product.needs_review = False

    # await db.commit()

    # Перенаправляем обратно к списку товаров этого источника
    return RedirectResponse(
        url=f"/api/v1/suppliers/products/?source={supp_product.source}",
        status_code=303,
    )
