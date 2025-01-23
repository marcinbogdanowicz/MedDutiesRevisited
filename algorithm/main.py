from typing import Any

from algorithm.doctor import Doctor
from algorithm.duty_setter import DutySetter
from algorithm.serializers import InputSerializer


def validate_data(data: dict[str, Any]) -> dict[str, Any]:
    serializer = InputSerializer.model_validate(data)
    return serializer.model_dump()


def create_duty_setter(validated_data: dict[str, Any]) -> DutySetter:
    year = validated_data["year"]
    month = validated_data["month"]

    doctors_data = validated_data.pop("doctors")
    duties_data = validated_data.pop("duties")

    duty_setter = DutySetter(**validated_data)
    schedule = duty_setter.schedule

    for doctor_data in doctors_data:
        preferences = doctor_data.pop("preferences")

        doctor = Doctor(**doctor_data)
        doctor.init_preferences(month=month, year=year, **preferences)

        duty_setter.add_doctor(doctor)

    for duty_data in duties_data:
        doctor_pk = duty_data.pop("doctor_pk")
        day = duty_data.pop("day")
        position = duty_data.pop("position")

        doctor = duty_setter.get_doctor(doctor_pk)
        schedule[day, position].update(doctor, **duty_data)

    return duty_setter


def main(data: dict[str, Any]) -> dict[str, Any]:
    validated_data = validate_data(data)

    duty_setter = create_duty_setter(validated_data)
    duty_setter.set_duties()
    result = duty_setter.get_result()

    return result.to_dict()
