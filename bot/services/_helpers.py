from datetime import datetime, timezone

from bot.locales import t


def time_ago(dt: datetime, lang: str = "ru") -> str:
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    minutes = int(diff.total_seconds() / 60)

    if minutes < 60:
        return t("time_ago_minutes", lang, n=max(1, minutes))
    hours = minutes // 60
    if hours < 24:
        return t("time_ago_hours", lang, n=hours)
    days = hours // 24
    return t("time_ago_days", lang, n=days)


def format_offers_count(count: int, lang: str = "ru") -> str:
    if count == 0:
        return t("no_offers_text", lang)
    if count == 1:
        return t("offers_count_1", lang)
    if 2 <= count <= 4:
        return t("offers_count_2_4", lang, count=count)
    return t("offers_count", lang, count=count)
