# from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from redis.asyncio import Redis

# from core.logger import logger
from core.settings import settings
from db.redis import get_redis
from schemas.enums import SourcesProductEnum
from schemas.supplier_schemas import SupplierProductUpdate
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
    redis_client: Redis = Depends(get_redis),
) -> HTMLResponse:
    """
    Страница редактирования.
    Загружает SupplierProduct, его логи (не обработанные) и связанный Product.
    """
    supplier_result = await supplier_service.get_supplier_product_review_data(
        supp_product_id, redis_client
    )
    supp_product, transformed_logs, preprocessed_data = supplier_result
    product = None
    if product_id := supp_product.product_id:
        product = await product_service.repo.get_by_id(product_id)
    available_products = []
    if not product:
        available_products = await product_service.repo.get_entities(
            ["id", "name", "article"]
        )
    review_data, review_complex_data = await supplier_service.get_review_data(
        supp_product, transformed_logs, preprocessed_data, product
    )

    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "supplier_product": supp_product,
            "product": product,
            "review_data": review_data,
            "available_products": available_products,
            "review_complex_data": review_complex_data,
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
    redis_client: Redis = Depends(get_redis),
) -> RedirectResponse:
    """
    Обработка формы.
    Обновляет Product, отмечает логи как обработанные,
    снимает флаг needs_review.
    """
    form_data = await request.form()

    source = await supplier_service.process_review(
        supp_product_id,
        product_service,
        form_data,
        redis_client,
    )

    # Перенаправляем обратно к списку товаров этого источника
    return RedirectResponse(
        url=f"/api/v1/suppliers/products/?source={source}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@supplier_product_review.post(  # type: ignore[misc]
    "/link_product/{supp_product_id}"
)
async def link_product(
    supp_product_id: UUID,
    request: Request,
    supplier_service: SupplierClient = Depends(get_supplier_service),
) -> RedirectResponse:
    """
    Отдельный эндпоинт для быстрой привязки товара.
    Обновляет product_id и перезагружает страницу.
    """
    form_data = await request.form()
    product_id_str = str(form_data.get("product_id"))

    if not product_id_str:
        return RedirectResponse(
            url=(
                f"/api/v1/suppliers/review/{supp_product_id}"
                "?error=no_product_selected"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        target_product_id = UUID(product_id_str)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Неверный формат ID продукта"
        )

    await supplier_service.supplier_product_repo.update(
        supp_product_id,
        SupplierProductUpdate(
            product_id=target_product_id, should_export_to_crm=True
        ),
    )

    return RedirectResponse(
        url=f"/api/v1/suppliers/review/{supp_product_id}", status_code=303
    )
