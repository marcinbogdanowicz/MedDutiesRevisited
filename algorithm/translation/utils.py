import os
from contextvars import ContextVar

from babel.support import NullTranslations, Translations

from algorithm.translation.enums import Locale
from algorithm.translation.serializers import LocaleSerializer

current_translations = ContextVar('current_translations')


def init_locale(data: dict) -> None:
    serializer = LocaleSerializer.model_validate(data)
    translations = get_translations(serializer.locale)
    current_translations.set(translations)


def get_translations(locale: str = Locale.EN) -> NullTranslations:
    locale_dir = os.path.join(os.path.dirname(__file__), 'locales')
    return Translations.load(locale_dir, locales=locale)


def _(message: str, **kwargs) -> str:
    translations = current_translations.get()
    translated_message = translations.gettext(message)
    if kwargs:
        return translated_message.format(**kwargs)

    return translated_message
