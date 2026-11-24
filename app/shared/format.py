from datetime import date, datetime

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


def jp_date(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return value
    if not isinstance(value, date):
        return str(value)
    return "{}年{}月{}日（{}）".format(value.year, value.month, value.day, WEEKDAYS[value.weekday()])


def short_date(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return value
    if not isinstance(value, date):
        return str(value)
    return "{}/{}".format(value.month, value.day)


def yen(amount):
    try:
        return "{:,}".format(int(amount))
    except (TypeError, ValueError):
        return str(amount)
