"""Reloj del sistema en un solo lugar.

Los servicios reciben `today` como parametro para que los tests puedan congelar
la fecha sin parchear `date.today` global.
"""

from datetime import date, datetime


def today() -> date:
    return date.today()


def now() -> datetime:
    return datetime.now()
