from datetime import date, datetime, timedelta


class DateService:
    """Сервис для работы с датами и рабочими днями"""

    # Константы для дней недели
    SATURDAY = 5
    SUNDAY = 6
    DAYS_IN_WEEK = 7

    @staticmethod
    def normalize_to_date(dt: datetime | date) -> date:
        """
        Приводит datetime к date, игнорируя время.

        Args:
            dt: Дата и время или просто дата

        Returns:
            Дата без времени
        """
        return dt.date() if isinstance(dt, datetime) else dt

    @staticmethod
    def is_weekend(target_date: datetime | date) -> bool:
        """
        Проверяет, является ли день выходным (суббота или воскресенье).

        Args:
            target_date: Дата для проверки

        Returns:
            True если выходной, False если рабочий день
        """
        date_obj = DateService.normalize_to_date(target_date)
        return date_obj.weekday() in (DateService.SATURDAY, DateService.SUNDAY)

    @staticmethod
    def is_workday(target_date: datetime | date) -> bool:
        """
        Проверяет, является ли день рабочим.

        Args:
            target_date: Дата для проверки

        Returns:
            True если рабочий день, False если выходной
        """
        return not DateService.is_weekend(target_date)

    @staticmethod
    def add_working_days(
        start_date: datetime | date,
        working_days: int,
        preserve_time: bool = False,
    ) -> datetime:
        """
        Добавляет указанное количество рабочих дней к дате.

        Args:
            start_date: Начальная дата
            working_days: Количество рабочих дней для добавления
            preserve_time: Сохранять ли исходное время

        Returns:
            Новая дата с добавленными рабочими днями

        Raises:
            ValueError: Если working_days отрицательное
        """
        if working_days < 0:
            raise ValueError(
                "Количество рабочих дней не может быть отрицательным"
            )

        current_date = DateService.normalize_to_date(start_date)

        if working_days == 0:
            if isinstance(start_date, datetime):
                if preserve_time:
                    return start_date
            return datetime.combine(current_date, datetime.min.time())

        days_added = 0

        while days_added < working_days:
            current_date += timedelta(days=1)
            if DateService.is_workday(current_date):
                days_added += 1

        # Сохраняем исходное время если нужно и если start_date был datetime
        if preserve_time and isinstance(start_date, datetime):
            return datetime.combine(current_date, start_date.time())

        return datetime.combine(current_date, datetime.min.time())

    @staticmethod
    def get_working_days_count(
        start_date: datetime | date,
        end_date: datetime | date,
        include_start: bool = False,
        include_end: bool = True,
    ) -> int:
        """
        Вычисляет количество рабочих дней между двумя датами.

        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            include_start: Включать ли начальную дату в подсчет
            include_end: Включать ли конечную дату в подсчет

        Returns:
            Количество рабочих дней в периоде
        """
        start = DateService.normalize_to_date(start_date)
        end = DateService.normalize_to_date(end_date)

        if start > end:
            start, end = end, start

        working_days = 0
        current_date = start

        while current_date <= end:
            if DateService.is_workday(current_date):
                # Проверяем нужно ли включать граничные даты
                if (
                    (current_date == start and include_start)
                    or (current_date == end and include_end)
                    or (current_date != start and current_date != end)
                ):
                    working_days += 1
            current_date += timedelta(days=1)

        return working_days

    @staticmethod
    def get_calendar_days_count(
        start_date: datetime | date,
        end_date: datetime | date,
        include_both: bool = False,
    ) -> int:
        """
        Вычисляет разницу в календарных днях между двумя датами.

        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            include_both: Включать ли обе граничные даты в подсчет

        Returns:
            Количество календарных дней
        """
        start = DateService.normalize_to_date(start_date)
        end = DateService.normalize_to_date(end_date)

        if start > end:
            start, end = end, start

        days_diff = (end - start).days

        return days_diff + 1 if include_both else days_diff

    @staticmethod
    def get_next_workday(target_date: datetime | date) -> datetime:
        """
        Возвращает следующий рабочий день.

        Args:
            target_date: Дата от которой ищется следующий рабочий день

        Returns:
            Следующий рабочий день
        """
        current_date = DateService.normalize_to_date(target_date)

        while True:
            current_date += timedelta(days=1)
            if DateService.is_workday(current_date):
                break

        if isinstance(target_date, datetime):
            return datetime.combine(current_date, target_date.time())

        return datetime.combine(current_date, datetime.min.time())

    @staticmethod
    def get_previous_workday(target_date: datetime | date) -> datetime:
        """
        Возвращает предыдущий рабочий день.

        Args:
            target_date: Дата от которой ищется предыдущий рабочий день

        Returns:
            Предыдущий рабочий день
        """
        current_date = DateService.normalize_to_date(target_date)

        while True:
            current_date -= timedelta(days=1)
            if DateService.is_workday(current_date):
                break

        if isinstance(target_date, datetime):
            return datetime.combine(current_date, target_date.time())

        return datetime.combine(current_date, datetime.min.time())

    @staticmethod
    def create_date_range(
        start_date: datetime | date,
        end_date: datetime | date,
        only_workdays: bool = False,
    ) -> list[date]:
        """
        Создает список дат в указанном диапазоне.

        Args:
            start_date: Начальная дата диапазона
            end_date: Конечная дата диапазона
            only_workdays: Включать только рабочие дни

        Returns:
            Список дат в диапазоне
        """
        start = DateService.normalize_to_date(start_date)
        end = DateService.normalize_to_date(end_date)

        if start > end:
            return []

        date_range: list[date] = []
        current_date = start

        while current_date <= end:
            if not only_workdays or DateService.is_workday(current_date):
                date_range.append(current_date)
            current_date += timedelta(days=1)

        return date_range
