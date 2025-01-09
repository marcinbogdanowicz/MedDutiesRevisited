from enum import IntEnum, StrEnum


class DayCategory(StrEnum):
    WEEKDAY = 'weekday'
    THURSDAY = 'thursday'
    WEEKEND = 'weekend'
    HOLIDAY = 'holiday'


class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def weekend(cls) -> list[int]:
        return [cls.FRIDAY, cls.SATURDAY, cls.SUNDAY]


class StrainPoints(IntEnum):
    WEEKDAY = 80
    THURSDAY = 70
    FRIDAY = 90
    SATURDAY = 110
    SUNDAY = 100
    HOLIDAY = 140
