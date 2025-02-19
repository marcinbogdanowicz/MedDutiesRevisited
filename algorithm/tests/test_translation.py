from unittest import TestCase

from babel.messages.pofile import read_po
from babel.support import Translations

from algorithm.translation.utils import current_translations, init_locale


class TranslationTests(TestCase):
    def test_init_locale(self):
        data = {'locale': 'pl'}
        init_locale(data)

        translations = current_translations.get()
        self.assertIsInstance(translations, Translations)
        self.assertEqual(translations.domain, 'messages')
        self.assertEqual(translations.info()['language'], 'pl')

    def test_init_locale_empty_data_fallbacks_to_english(self):
        data = {}
        init_locale(data)

        translations = current_translations.get()
        self.assertEqual(translations.domain, 'messages')
        self.assertEqual(translations.info()['language'], 'en')

    def test_init_locale_with_invalid_locale(self):
        data = {'locale': 'invalid'}
        with self.assertRaises(ValueError):
            init_locale(data)

    def test_polish_translations_are_provided(self):
        with open('algorithm/translation/locales/pl/LC_MESSAGES/messages.po') as file:
            catalog = read_po(file)

        for message in catalog:
            if message.id:
                self.assertGreater(len(message.string), 0)
                self.assertNotEqual(message.id, message.string)
