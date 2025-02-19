from pydantic import BaseModel

from algorithm.translation.enums import Locale


class LocaleSerializer(BaseModel):
    locale: Locale = Locale.EN
