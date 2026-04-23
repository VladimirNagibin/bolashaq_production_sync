from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.v1.schemas.response_schemas import TokenData
from core.exceptions.supplier_exceptions import NameNotFoundError
from core.logger import logger
from core.settings import settings
from schemas.enums import BrandEnum, SourcesProductEnum
from schemas.fields import FIELD_LABELS_RU
from schemas.productsection_schemas import Productsection
from schemas.supplier_schemas import SupplierProductUpdate
from services.dependencies.dependencies import (
    get_product_service,
    get_productsection_service,
)
from services.dependencies.dependencies_suppliers import (
    get_supplier_product_repo,
    get_supplier_service,
)
from services.products.product_services import ProductClient
from services.productsections.productsection_services import (
    ProductsectionClient,
)
from services.suppliers.repositories.supplier_product_repo import (
    SupplierProductRepository,
)
from services.suppliers.supplier_services import SupplierClient

supplier_product_review = APIRouter()
templates = Jinja2Templates(directory=f"{settings.BASE_DIR}/templates")


@supplier_product_review.get(  # type: ignore[misc]
    "/", response_class=HTMLResponse
)
async def read_root(
    request: Request,
) -> HTMLResponse:
    """Выбор источника данных"""
    try:
        # Получаем список возможных источников из Enum
        sources = [e.value for e in SourcesProductEnum]
        logger.debug(f"Available sources: {sources}")
        return templates.TemplateResponse(
            "index.html", {"request": request, "sources": sources}
        )
    except Exception as e:
        logger.error(f"Failed to load index page: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load page",
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
    logger.info(f"Fetching products for source: {source}")
    try:
        source_products = SourcesProductEnum(source)
    except ValueError:
        logger.error(f"Invalid source: {source}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid source",
        )
    try:
        products = await supplier_product_repo.get_supplier_products_by_source(
            source_products
        )
        logger.debug(f"Found {len(products)} products for source {source}")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    product_section_service: ProductsectionClient = Depends(
        get_productsection_service
    ),
) -> HTMLResponse:
    """
    Страница редактирования.
    Загружает SupplierProduct, его логи (не обработанные) и связанный Product.
    """
    logger.info(f"Loading review page for product: {supp_product_id}")
    try:
        # Получаем данные для ревью
        supplier_product, transformed_logs, preprocessed_data = (
            await supplier_service.get_supplier_product_review_data(
                supp_product_id
            )
        )
        # Получаем связанный продукт
        product = None
        if product_id := supplier_product.product_id:
            product = await product_service.repo.get_by_id(product_id)
            logger.debug(f"Found linked product: {product_id}")

        # Получаем доступные продукты для привязки
        available_products = []
        if not product:
            available_products = await product_service.repo.get_entities(
                ["id", "name", "article"]
            )
            logger.debug(f"Found {len(available_products)} available products")

        # Подготавливаем данные для отображения
        review_data, review_complex_data = (
            await supplier_service.get_review_context(
                supplier_product,
                transformed_logs,
                preprocessed_data,
                product,
            )
        )

        ai_data = await supplier_service.get_ai_context(
            preprocessed_data,
        )
        sections_review_data = (
            await product_section_service.get_sections_review_data(
                review_complex_data
            )
        )
        # Обработка ошибок
        error_message = None
        if request.query_params.get("error") == "name_required":
            error_message = (
                "Для заведения нового товара в Битрикс необходимо, "
                "чтобы было заполнено поле Name."
            )
        return templates.TemplateResponse(
            "edit.html",
            {
                "request": request,
                "supplier_product": supplier_product,
                "product": product,
                "review_data": review_data,
                "available_products": available_products,
                "review_complex_data": review_complex_data,
                "brand_options": BrandEnum.to_dict(),
                "error_message": error_message,
                "category_roots": (
                    sections_review_data.get("category_roots", [])
                ),
                "category_children_map": (
                    sections_review_data.get("category_children_map", [])
                ),
                "selected_root_id": (
                    sections_review_data.get("selected_root_id")
                ),
                "selected_child_id": (
                    sections_review_data.get("selected_child_id")
                ),
                "selected_child_name": (
                    sections_review_data.get("selected_child_name")
                ),
                "selected_root_name": (
                    sections_review_data.get("selected_root_name")
                ),
                "field_labels": FIELD_LABELS_RU,
                "ai_data": ai_data,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to load review page: {e}",
            extra={"product_id": str(supp_product_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to load review page"
        )


@supplier_product_review.post(  # type: ignore[misc]
    "/review/{supp_product_id}"
)
async def process_review(
    request: Request,
    supp_product_id: UUID,
    supplier_service: SupplierClient = Depends(get_supplier_service),
) -> RedirectResponse:
    """
    Обработка формы.
    Обновляет Product, отмечает логи как обработанные,
    снимает флаг needs_review.
    """
    logger.info(f"Processing review for product: {supp_product_id}")

    try:
        token_data: TokenData = request.state.user
        form_data = await request.form()
        source = await supplier_service.process_review(
            supp_product_id,
            form_data,
            token_data,
        )
        logger.info(
            "Review processed successfully for product: " f"{supp_product_id}"
        )

        # Перенаправляем обратно к списку товаров этого источника
        return RedirectResponse(
            url=f"/api/v1/suppliers/products/?source={source}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except NameNotFoundError:
        logger.warning(f"Name required for product: {supp_product_id}")
        return RedirectResponse(
            url=(
                f"/api/v1/suppliers/review/{supp_product_id}"
                "?error=name_required"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logger.error(
            f"Failed to process review: {e}",
            extra={"product_id": str(supp_product_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process review",
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
    logger.info(f"Linking product to: {supp_product_id}")

    try:
        form_data = await request.form()
        product_id_str = str(form_data.get("product_id"))

        if not product_id_str:
            logger.warning(
                f"No product selected for linking to {supp_product_id}"
            )
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
            logger.error(f"Invalid product ID format: {product_id_str}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат ID продукта",
            )

        await supplier_service.supplier_product_repo.update(
            supp_product_id,
            SupplierProductUpdate(
                product_id=target_product_id, should_export_to_crm=True
            ),
        )
        logger.info(f"Product {supp_product_id} linked to {target_product_id}")

        return RedirectResponse(
            url=f"/api/v1/suppliers/review/{supp_product_id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to link product: {e}",
            extra={"product_id": str(supp_product_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link product",
        )


@supplier_product_review.post("/create_root_section")  # type: ignore[misc]
async def create_root_section(
    name: str = Form(...),
    product_section_service: ProductsectionClient = Depends(
        get_productsection_service
    ),
) -> dict[str, Any]:
    """
    Создает новый корневой раздел.
    """
    try:
        section_data: dict[str, Any] = {"name": name}
        new_section = Productsection(**section_data)

        new_product_section = (
            await product_section_service.create_in_bitrix_and_db(new_section)
        )
        if new_product_section:
            return {
                "id": new_product_section.external_id,
                "name": new_product_section.name,
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create section",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to create section: {e}",
            extra={"section_name": name},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create section: {e}",
        )
