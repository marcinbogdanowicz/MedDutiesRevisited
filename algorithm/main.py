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
        doctor.init_preferences(year=year, month=month, **preferences)

        duty_setter.add_doctor(doctor)

    for duty_data in duties_data:
        day = duty_data.pop("day")
        position = duty_data.pop("position")

        if duty_data["set_by_user"]:
            doctor = duty_data.pop("doctor")
            doctor = duty_setter.get_doctor(doctor)
            schedule[day, position].update(doctor, **duty_data)
        else:
            schedule[day, position].update(None, pk=duty_data["pk"])  # Preserve duty pk for response

    return duty_setter


def set_duties(data: dict[str, Any]) -> dict[str, Any]:
    validated_data = validate_data(data)

    duty_setter = create_duty_setter(validated_data)
    duty_setter.set_duties()
    result = duty_setter.get_result()

    return result.to_dict()


def validate_duties_can_be_set(data: dict[str, Any]) -> dict[str, Any]:
    validated_data = validate_data(data)

    duty_setter = create_duty_setter(validated_data)
    duty_setter.check_if_duties_can_be_set()
    result = duty_setter.get_result()

    return {"errors": result.errors}
