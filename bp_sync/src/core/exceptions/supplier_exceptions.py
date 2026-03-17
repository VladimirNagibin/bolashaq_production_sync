class ImportError(Exception):
    pass


class FileProcessingError(Exception):
    pass


class DataMappingError(Exception):
    pass


class DatabaseError(Exception):
    pass


class NameNotFoundError(Exception):
    """Ошибка при отсутствии доступного менеджера."""

    pass
