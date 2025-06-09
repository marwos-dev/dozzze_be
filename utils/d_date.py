from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Union

BASE_DATE = date(2022, 9, 12)


def get_ddate_id(_date: Union[str, date, datetime, None] = None) -> int:
    """
    Calcula el ID de la fecha basado en los días transcurridos desde BASE_DATE.

    :param _date: Fecha para calcular el ID. Puede ser un objeto date,
     datetime, un string 'YYYY-MM-DD', o None para usar la fecha actual.
    :return: Número entero representando el ID de la fecha.
    :raises ValueError: Si el tipo de entrada no es válido o el formato de la fecha es incorrecto.
    """
    if _date is None:
        return (date.today() - BASE_DATE).days + 1
    elif isinstance(_date, str):
        try:
            _date = datetime.strptime(_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                f"Formato de fecha inválido: {_date}. Use el formato 'YYYY-MM-DD'."
            )
    elif isinstance(_date, datetime):
        _date = _date.date()
    elif not isinstance(_date, date):
        raise ValueError(
            f"Tipo de entrada no válido: {type(_date)}. Use None, str, date, o datetime."
        )

    return _cached_get_ddate_id(_date)


@lru_cache(maxsize=128)
def _cached_get_ddate_id(_date: date) -> int:
    """
    Función auxiliar cacheada para calcular el ID de la fecha.

    :param _date: Objeto date para calcular el ID.
    :return: Número entero representando el ID de la fecha.
    """
    return (_date - BASE_DATE).days + 1


def get_ddate_text(ddate_id: Union[int, None] = None) -> str:
    """
    Convierte un ID de fecha en una representación de texto de la fecha.

    :param ddate_id: ID de la fecha. Si es None, se usa la fecha actual.
    :return: String representando la fecha en formato 'YYYY-MM-DD'.
    """
    if ddate_id is None:
        return date.today().isoformat()

    return _cached_get_ddate_text(ddate_id)


@lru_cache(maxsize=128)
def _cached_get_ddate_text(ddate_id: int) -> str:
    """
    Función auxiliar cacheada para convertir un ID de fecha en texto.

    :param ddate_id: ID de la fecha (debe ser un entero).
    :return: String representando la fecha en formato 'YYYY-MM-DD'.
    """
    return (BASE_DATE + timedelta(days=ddate_id - 1)).isoformat()
