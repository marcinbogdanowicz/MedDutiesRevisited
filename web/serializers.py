from pydantic import BaseModel

from algorithm.translation import Locale


class LocaleSerializer(BaseModel):
    locale: Locale
