from bot.locales import ru, uz

_LOCALES = {
    "ru": ru.TEXTS,
    "uz": uz.TEXTS,
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    texts = _LOCALES.get(lang, _LOCALES["ru"])
    text = texts.get(key, _LOCALES["ru"].get(key, key))
    if kwargs:
        return text.format(**kwargs)
    return text
