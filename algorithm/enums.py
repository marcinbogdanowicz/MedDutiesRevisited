from enum import IntEnum


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
    TWO_DAYS_APART = 30
    THREE_DAYS_APART = 20
    FOUR_DAYS_APART = 10
    JOIN_FRIDAY_WITH_SUNDAY = -60
    AVOID_SATURDAY_AFTER_THURSDAY = 30
    DONT_STEAL_SUNDAYS = 100
    THURSDAY_IS_ORDINARY = 10
    NEW_WEEKEND = 200
    DUTY_LEFT = -10
