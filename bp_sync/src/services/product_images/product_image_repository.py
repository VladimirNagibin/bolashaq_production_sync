from models.product_images_models import ProductImage as ProductImageDB
from schemas.enums import EntityType
from schemas.product_image_schemas import (
    ProductImageCreate,
    ProductImageUpdate,
)

from ..base_repositories.base_repository import BaseRepository


class ProductImageRepository(
    BaseRepository[ProductImageDB, ProductImageCreate, ProductImageUpdate, int]
):

    model = ProductImageDB
    entity_type = EntityType.PRODUCT_IMAGE
    schema_update_class = ProductImageUpdate
