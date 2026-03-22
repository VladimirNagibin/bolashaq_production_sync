from typing import Any

from core.logger import logger
from core.settings import settings
from schemas.enums import ImageType
from schemas.product_image_schemas import ProductImageCreate

from ..file_download_service import FileDownloadService
from ..products.product_data_raw import ProductRawDataService

DETAIL_PICTURE = ImageType.DETAIL_PICTURE.name


class ProductImageService:

    def __init__(
        self,
        product_data_raw: ProductRawDataService,
        file_download_service: FileDownloadService,
    ) -> None:
        self.product_data_raw = product_data_raw
        self.file_download_service = file_download_service

    async def set_detail_picture(
        self,
        product_id: int,
        picture_url: str,
        skip_if_exists: bool = True,
    ) -> tuple[int | None, bool]:
        """Установка детальной картинки"""
        try:
            if skip_if_exists:
                detail_picture_id = await self.get_detail_picture_id(
                    product_id
                )
                if detail_picture_id:
                    logger.info(
                        f"Product_id {product_id} detail_picture already "
                        "exists"
                    )
                    return detail_picture_id, False

            # Скачиваем изображение
            logger.debug(f"Downloading gallery image from {picture_url}")
            image_data = await self.file_download_service.download_file(
                picture_url
            )
            if image_data:
                logger.info(
                    f"Successfully downloaded gallery image for product "
                    f"{product_id}: {image_data['filename']} "
                    f"({image_data['file_size']} bytes)"
                )
            else:
                logger.debug(
                    f"Detail picture not download {picture_url} "
                    f"for product {product_id}"
                )
                return None, False

            # Формируем данные для загрузки
            picture_update_data = {
                DETAIL_PICTURE: {
                    "fileData": [image_data["filename"], image_data["content"]]
                }
            }
            logger.info(f"Updating image for product {product_id}")
            success = await self.product_data_raw.update(
                product_id, picture_update_data
            )
            if not success:
                logger.error(
                    f"Failed to update image for product {product_id}"
                )
                return None, False
            return await self.get_detail_picture_id(product_id), True
        except Exception as e:
            logger.error(
                "Fail to set detail_picture to product_id "
                f"{product_id} from {picture_url} :{str(e)}"
            )
            return None, False

    async def delete_detail_picture(self, product_id: int) -> bool:
        """Удаление детальной картинки"""
        try:
            detail_picture_id = await self.get_detail_picture_id(product_id)
            if not detail_picture_id:
                return False

            return await self.delete_picture_by_id(
                product_id, detail_picture_id
            )
        except Exception as e:
            logger.error(
                "Failed to delete detail_picture from product_id "
                f"{product_id} :{str(e)}"
            )
            return False

    async def get_detail_picture_id(
        self, product_id: int, image_type: ImageType = ImageType.DETAIL_PICTURE
    ) -> int | None:
        """Получение id детальной картинки"""
        try:
            exists_detail_picture = await self.product_data_raw.get_field(
                product_id, image_type.name
            )
            if (
                exists_detail_picture
                and isinstance(exists_detail_picture, dict)
                and int(exists_detail_picture.get("id", 0)) > 0
            ):
                return int(exists_detail_picture.get("id"))
            return None
        except Exception as e:
            logger.error(
                "Failed to get id detail_picture from product_id "
                f"{product_id} :{str(e)}"
            )
            return None

    async def delete_picture_by_id(
        self, product_id: int, picture_id: int
    ) -> bool:
        """Удаление детальной картинки"""
        try:
            payload = {"productId": product_id, "id": picture_id}
            response = await self.product_data_raw.call_api(
                "catalog.productImage.delete", params=payload
            )
            if response:
                logger.info(
                    f"Successfully deleted image {picture_id} "
                    f"from product {product_id}"
                )
                return True
            else:
                return False
        except Exception as e:
            logger.error(
                "Failed to delete detail_picture fron product_id "
                f"{product_id} :{str(e)}"
            )
            return False

    async def add_to_gallery(
        self, product_id: int, picture_url: str
    ) -> int | None:
        """Добавление изображения в галерею"""
        try:
            # Скачиваем изображение
            logger.debug(f"Downloading gallery image from {picture_url}")
            image_data = await self.file_download_service.download_file(
                picture_url
            )
            if image_data:
                logger.info(
                    f"Successfully downloaded gallery image for product "
                    f"{product_id}: {image_data['filename']} "
                    f"({image_data['file_size']} bytes)"
                )
            else:
                logger.debug(
                    f"Detail picture not download {picture_url} "
                    f"for product {product_id}"
                )
                return None

            # Формируем данные для загрузки
            picture_update_data: dict[str, Any] = {
                "fields": {
                    "productId": product_id,
                    "type": ImageType.MORE_PHOTO.name,
                },
                "fileContent": [image_data["filename"], image_data["content"]],
            }

            logger.info(f"Add image for product {product_id} in galery")
            response = await self.product_data_raw.call_api(
                "catalog.productImage.add",
                picture_update_data,
            )
            if not response:
                logger.error(
                    f"Failed to add image for product {product_id} in galery"
                )
                return None
            product_image = response.get("productImage", {})
            image_id = int(product_image.get("id", 0))
            if image_id > 0:
                return image_id
            return None

        except Exception as e:
            logger.error(
                f"Failed to add image for product {product_id} in galery "
                f":{str(e)}"
            )
            return None

    def get_download_image_url(
        self, product_id: int, image_id: int, image_type: str
    ) -> str:
        """Получение URL для скачивания изображения"""
        base_url = settings.BITRIX_PORTAL.rstrip("/")
        webhook_path = settings.WEB_HOOK_TOKEN.lstrip("/")

        return (
            f"{base_url}/{webhook_path}"
            f"catalog.product.download?"
            f"fields%5BfieldName%5D={image_type}&"
            f"fields%5BfileId%5D={image_id}&"
            f"fields%5BproductId%5D={product_id}"
        )

    async def get_pictures_by_product_id(
        self, product_id: int
    ) -> list[ProductImageCreate]:
        try:
            payload = {"productId": product_id}
            response = await self.product_data_raw.call_api(
                "catalog.productImage.list", params=payload
            )
            if response:
                images = response.get("productImages", [])
                return [ProductImageCreate(**image) for image in images]
        except Exception as e:
            logger.error(
                "Failed to get detail_picture from product_id "
                f"{product_id} :{str(e)}"
            )
        return []
