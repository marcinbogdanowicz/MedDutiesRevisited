from pydantic import BaseModel, field_validator, model_validator
from typing_extensions import Self

from algorithm.utils import get_max_number_of_duties_for_month, get_number_of_days_in_month, recursive_getattr


class DutySerializer(BaseModel):
    pk: int | None = None
    day: int
    position: int
    doctor_pk: int
    strain_points: int
    set_by_user: bool


class PreferencesSerializer(BaseModel):
    exceptions: list[int]
    preferred_days: list[int]
    preferred_weekdays: list[int]
    preferred_positions: list[int]
    maximum_accepted_duties: int

    @field_validator('preferred_weekdays')
    @classmethod
    def validate_preferred_weekdays(cls, value: list[int]) -> list[int]:
        valid_weekdays = range(7)
        if invalid_weekdays := [elem for elem in value if elem not in valid_weekdays]:
            raise ValueError(f'Invalid preferred weekdays specified: {invalid_weekdays}')

        return value


class DoctorSerializer(BaseModel):
    pk: int
    name: str
    preferences: PreferencesSerializer
    last_month_duties: list[int]
    next_month_duties: list[int]


class InputSerializer(BaseModel):
    year: int
    month: int
    doctors_per_duty: int
    doctors: list[DoctorSerializer]
    duties: list[DutySerializer]

    @field_validator('month', mode='after')
    @classmethod
    def validate_month(cls, value: int) -> int:
        if value < 1 or value > 12:
            raise ValueError(f'{value} is not a valid month number.')

        return value

    @model_validator(mode='after')
    def validate_preferred_positions(self) -> Self:
        errors = ''

        existing_positions = range(1, self.doctors_per_duty + 1)
        for doctor in self.doctors:
            preferred_positions = doctor.preferences.preferred_positions
            if any(position not in existing_positions for position in preferred_positions):
                errors += f'Invalid preferred positions for {doctor.name}: {preferred_positions}. '

        if errors:
            errors += f'Accepted positions: {list(existing_positions)}'
            raise ValueError(errors)

        return self

    @model_validator(mode='after')
    def validate_last_month_duties(self) -> Self:
        month = self.month - 1
        year = self.year

        if month == 0:
            month = 12
            year -= 1

        self._validate_provided_dates_are_within_months_length(month, year, date_list_doctor_attr='last_month_duties')
        return self

    @model_validator(mode='after')
    def validated_next_month_duties(self) -> Self:
        month = self.month + 1
        year = self.year

        if month == 13:
            month = 1
            year += 1

        self._validate_provided_dates_are_within_months_length(month, year, date_list_doctor_attr='next_month_duties')
        return self

    @model_validator(mode='after')
    def validate_exceptions(self) -> Self:
        self._validate_provided_dates_are_within_months_length(
            self.month, self.year, date_list_doctor_attr='preferences.exceptions'
        )
        return self

    @model_validator(mode='after')
    def validate_preferred_days(self) -> Self:
        self._validate_provided_dates_are_within_months_length(
            self.month, self.year, date_list_doctor_attr='preferences.preferred_days'
        )
        return self

    def _validate_provided_dates_are_within_months_length(
        self, month: int, year: int, date_list_doctor_attr: str
    ) -> None:
        errors = ''
        month_length = get_number_of_days_in_month(month, year)

        def is_a_valid_day_number(number: int) -> bool:
            return 0 < number <= month_length

        for doctor in self.doctors:
            provided_days_list = recursive_getattr(doctor, date_list_doctor_attr)
            if invalid_days := [day for day in provided_days_list if not is_a_valid_day_number(day)]:
                attr_name = date_list_doctor_attr.split('.')[-1]
                errors += f'Invalid {attr_name} for doctor {doctor.name}: {invalid_days}. '

        if errors:
            errors += f'Valid days for {month}/{year} are in range 1 - {month_length}.'
            raise ValueError(errors)

    @model_validator(mode='after')
    def validate_duties(self) -> Self:
        month_length = get_number_of_days_in_month(self.month, self.year)

        def is_a_valid_day_number(number: int) -> bool:
            return 0 < number <= month_length

        if invalid_days := [duty.day for duty in self.duties if not is_a_valid_day_number(duty.day)]:
            raise ValueError(
                f'Invalid duty days: {invalid_days}. Valid days for {self.month}/{self.year} are in range '
                f'1 - {month_length}.'
            )

        return self

    @model_validator(mode='after')
    def adjust_maximum_accepted_duties(self) -> Self:
        max_number_of_duties = get_max_number_of_duties_for_month(self.month, self.year)
        for doctor in self.doctors:
            preferences = doctor.preferences
            if preferences.maximum_accepted_duties > max_number_of_duties:
                preferences.maximum_accepted_duties = max_number_of_duties

        return self
