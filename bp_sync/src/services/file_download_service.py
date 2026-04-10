import base64
import hashlib
import mimetypes
import re
from typing import Any
from urllib.parse import unquote, urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.logger import logger
from core.settings import settings

from .exceptions import FileDownloadError


class FileDownloadService:
    """Сервис для скачивания файлов"""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=self.timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )  # type: ignore[misc]
    async def download_file(
        self, file_url: str, extra_headers: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Скачивает файл по URL и возвращает данные для загрузки

        Args:
            file_url: URL файла для скачивания

        Returns:
            dict: {
                'content': base64_encoded_content,
                'filename': str,
                'content_type': str,
                'file_size': int
            } или None при ошибке

        Raises:
            FileDownloadError: при критических ошибках скачивания
        """
        try:
            logger.debug(f"Starting async file download from URL: {file_url}")

            parsed_url = urlparse(file_url)
            referer_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            headers = {
                "User-Agent": "Mozilla/5.0 ...",
                "Referer": referer_url,
            }
            if extra_headers:
                headers.update(extra_headers)

            # Используем stream=True, чтобы скачивать частями и
            # контролировать размер
            async with self.client.stream(
                "GET", file_url, headers=headers
            ) as response:
                response.raise_for_status()

                # 1. Проверяем Content-Length, если он есть
                content_length = response.headers.get("content-length")
                if (
                    content_length
                    and int(content_length) > settings.MAX_FILE_SIZE
                ):
                    logger.error(
                        f"File too large (header): {content_length} bytes, "
                        f"max allowed: {settings.MAX_FILE_SIZE} bytes"
                    )
                    return None

                # 2. Читаем файл кусками, проверяя реальный размер и считая хэш
                chunks: list[bytes] = []
                total_size = 0
                sha256_hash = hashlib.sha256()

                async for chunk in response.aiter_bytes(chunk_size=8192):
                    total_size += len(chunk)

                    if total_size > settings.MAX_FILE_SIZE:
                        logger.error(
                            "File too large (downloaded): "
                            f"{total_size} bytes, "
                            f"max allowed: {settings.MAX_FILE_SIZE} bytes"
                        )
                        return None

                    sha256_hash.update(chunk)
                    chunks.append(chunk)

                # Собираем байты
                file_bytes = b"".join(chunks)

                # 3. Готовим метаданные
                content_type = response.headers.get(
                    "content-type", "application/octet-stream"
                )
                extension = mimetypes.guess_extension(content_type) or ".bin"
                filename = self._extract_filename(
                    response, file_url, extension
                )

                # Base64 (для старой совместимости)
                file_content_base64 = base64.b64encode(file_bytes).decode(
                    "utf-8"
                )

                file_info: dict[str, Any] = {
                    # "Старые" данные
                    "content": file_content_base64,
                    "filename": filename,
                    "content_type": content_type,
                    "file_size": total_size,
                    # "Новые" данные для БД
                    "raw_bytes": file_bytes,
                    "file_hash": sha256_hash.hexdigest(),
                }

                logger.info(
                    f"Successfully downloaded file: {filename}, "
                    f"size: {total_size} bytes, "
                    f"hash: {file_info['file_hash']}"
                )

                return file_info

        except httpx.TimeoutException as e:
            logger.error(f"Timeout downloading file from {file_url}: {e}")
            raise FileDownloadError(f"Download timeout: {e}")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading file from {file_url}: {e}")
            raise FileDownloadError(f"HTTP error: {e}")

        except Exception as e:
            logger.error(
                f"Unexpected error downloading file from {file_url}: {e}",
                exc_info=True,
            )
            raise FileDownloadError(f"Unexpected error: {e}")

    def _extract_filename(
        self,
        response: httpx.Response,
        fallback_url: str,
        default_extension: str,
    ) -> str:
        """
        Извлекает имя файла из HTTP response

        Приоритет:
        1. Content-Disposition header (filename*)
        2. Content-Disposition header (filename)
        3. URL path
        4. Генерирует имя на основе timestamp
        """
        try:
            headers = response.headers

            # 1. Content-Disposition
            content_disposition = headers.get("Content-Disposition", "")
            if content_disposition:
                # filename*
                match = re.search(
                    r"filename\*=([^;]+)", content_disposition, re.IGNORECASE
                )
                if match:
                    filename = match.group(1).strip()
                    filename = filename.strip("\"'")
                    if filename.lower().startswith("utf-8''"):
                        filename = unquote(filename[7:])
                    return self._sanitize_filename(filename)

                # filename
                match = re.search(
                    r"filename=([^;]+)", content_disposition, re.IGNORECASE
                )
                if match:
                    filename = match.group(1).strip()
                    filename = filename.strip("\"'")
                    return self._sanitize_filename(unquote(filename))

            # 2. URL path
            parsed_url = urlparse(fallback_url)
            url_filename = parsed_url.path.split("/")[-1]
            if url_filename and "." in url_filename:
                return self._sanitize_filename(url_filename)

            # 3. Fallback timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"file_{timestamp}{default_extension}"

        except Exception as e:
            logger.warning(f"Error extracting filename: {e}")
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"file_{timestamp}{default_extension}"

    def _sanitize_filename(self, filename: str) -> str:
        """
        Очищает имя файла от недопустимых символов

        Args:
            filename: Исходное имя файла

        Returns:
            str: Очищенное имя файла
        """
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        if len(filename) > 255:
            name, ext = (
                filename.rsplit(".", 1) if "." in filename else (filename, "")
            )
            filename = f"{name[:250]}.{ext}" if ext else name[:255]
        return filename

    async def close(self) -> None:
        """Важно закрывать клиент при завершении работы"""
        await self.client.aclose()
