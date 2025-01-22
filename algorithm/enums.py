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


class StrainModifier(IntEnum):
    DUTY_IMPOSSIBLE = 10000
    TWO_DAYS_APART = 30
    THREE_DAYS_APART = 20
    FOUR_DAYS_APART = 10
    JOIN_FRIDAY_WITH_SUNDAY = -60
    AVOID_SATURDAY_AFTER_THURSDAY = 30
    MORE_THAN_TWO_WEEKENDS = 100
    LESS_THAN_TWO_WEEKENDS = 50
    DONT_STEAL_SUNDAYS = 100
    THURSDAY_IS_ORDINARY = 10
    SATURDAY_IF_ONE_WEEKEND = -30
    NEW_WEEKEND = 200
    EACH_WEEKEND = 40
    DUTY_LEFT = -10
