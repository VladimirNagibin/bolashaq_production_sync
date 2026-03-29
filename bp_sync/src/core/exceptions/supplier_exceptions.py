from uuid import UUID


class SupplierServiceError(Exception):
    """Базовое исключение для сервиса поставщика."""

    pass


class ImportError(SupplierServiceError):
    pass


class FileProcessingError(SupplierServiceError):
    pass


class DataMappingError(SupplierServiceError):
    pass


class DatabaseError(SupplierServiceError):
    pass


class NameNotFoundError(SupplierServiceError):
    pass


class ImportConfigurationError(SupplierServiceError):
    """Ошибка конфигурации импорта."""

    def __init__(self, source: str, config_name: str | None = None):
        self.source = source
        self.config_name = config_name
        super().__init__(
            f"Configuration not found for source '{source}' "
            f"(config: {config_name})"
        )


class SupplierProductNotFoundError(SupplierServiceError):
    """Товар поставщика не найден."""

    def __init__(self, product_id: UUID):
        self.product_id = product_id
        super().__init__(f"SupplierProduct with ID {product_id} not found")


class ReviewProcessingError(SupplierServiceError):
    """Ошибка при обработке ревью."""

    pass
