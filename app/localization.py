"""
Localization module - Multi-language support for School Bell Scheduler.
Supports: English, Russian, Kyrgyz.
"""
import json
import os

from PySide6.QtCore import QObject, Signal


class Localization(QObject):
    language_changed = Signal()

    LANGUAGES = {
        'en': 'English',
        'ru': 'Русский',
        'kg': 'Кыргызча',
    }

    def __init__(self, locales_path):
        super().__init__()
        self.locales_path = locales_path
        self.current_language = 'en'
        self.translations = {}
        self._load_all()

    def _load_all(self):
        for lang_code in self.LANGUAGES:
            filepath = os.path.join(self.locales_path, f'{lang_code}.json')
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            else:
                self.translations[lang_code] = {}

    def set_language(self, lang_code):
        if lang_code in self.LANGUAGES:
            self.current_language = lang_code
            self.language_changed.emit()

    def tr(self, key, **kwargs):
        text = self.translations.get(self.current_language, {}).get(key, '')
        if not text:
            text = self.translations.get('en', {}).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text

    def get_language_name(self, lang_code):
        return self.LANGUAGES.get(lang_code, lang_code)

    def get_available_languages(self):
        return list(self.LANGUAGES.items())
