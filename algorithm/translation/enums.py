from enum import StrEnum


class Locale(StrEnum):
    EN = "en"
    PL = "pl"

    def __str__(self) -> str:
        return self.value
