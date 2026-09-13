"""System clock, kept in one place.

Services take `today` as a parameter so tests can freeze the date without
monkeypatching `date.today` globally.
"""

from datetime import date, datetime


def today() -> date:
    return date.today()


def now() -> datetime:
    return datetime.now()
