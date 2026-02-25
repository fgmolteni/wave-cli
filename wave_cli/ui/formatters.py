"""
Utilidades de formato compartidas para Wave CLI.

Centraliza helpers reutilizados entre comandos MQTT, LoRa y la UI interactiva.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def format_timestamp(timestamp_value: Any) -> str:
    """Convierte timestamps ISO (incluyendo nanosegundos) a HH:MM:SS"""
    raw = str(timestamp_value or '').strip()
    if not raw:
        return '--:--:--'

    candidate = raw.replace('Z', '+00:00')

    if '.' in candidate:
        dot_index = candidate.find('.')
        tz_index = len(candidate)
        for tz_sep in ('+', '-'):
            idx = candidate.find(tz_sep, dot_index + 1)
            if idx != -1:
                tz_index = min(tz_index, idx)

        fractional = candidate[dot_index + 1:tz_index]
        if len(fractional) > 6:
            candidate = (
                candidate[:dot_index + 1]
                + fractional[:6]
                + candidate[tz_index:]
            )

    try:
        return datetime.fromisoformat(candidate).strftime('%H:%M:%S')
    except ValueError:
        return '--:--:--'


def parse_options(
    params: list,
    option_types: Dict[str, type],
    start_index: int = 0,
) -> Dict[str, Any]:
    """Parsea opciones con flags tipo --key valor desde una lista de params."""
    values: Dict[str, Any] = {key: None for key in option_types}
    i = start_index
    while i < len(params):
        token = params[i]
        caster = option_types.get(token)
        if caster is not None and i + 1 < len(params):
            values[token] = caster(params[i + 1])
            i += 2
        else:
            i += 1
    return values


def parse_message_with_options(
    params: list,
    option_types: Dict[str, type],
) -> Tuple[Dict[str, Any], List[str]]:
    """Parsea opciones separando argumentos posicionales de flags."""
    values: Dict[str, Any] = {key: None for key in option_types}
    positionals: List[str] = []
    i = 0
    while i < len(params):
        token = params[i]
        caster = option_types.get(token)
        if caster is not None and i + 1 < len(params):
            values[token] = caster(params[i + 1])
            i += 2
        else:
            positionals.append(token)
            i += 1
    return values, positionals


def truncate_payload(payload: str, max_length: int = 67) -> str:
    """Trunca un payload con elipsis si excede el largo máximo."""
    if len(payload) <= max_length:
        return payload
    return f"{payload[:max_length]}..."


def format_duration(total_seconds: int) -> str:
    """Formatea una duración en segundos a MM:SS o HH:MM:SS."""
    total_seconds = max(0, int(total_seconds))
    if total_seconds >= 3600:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"
