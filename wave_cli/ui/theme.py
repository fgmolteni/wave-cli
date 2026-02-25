"""
Sistema de diseño brutalista centralizado para Wave CLI.

Todas las tablas, paneles e indicadores de la aplicación deben
usar estas constantes para mantener consistencia visual.
"""


from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

# ── Paleta semántica de colores ──────────────────────────────
COLORS = {
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "cyan",
    "muted": "dim",
    "accent": "magenta",
    "border": "bright_white",
    "heading": "bold white",
    "value": "green",
    "label": "cyan",
    "highlight": "bold cyan",
    "kpi_good": "bold green",
    "kpi_warn": "bold yellow",
    "kpi_bad": "bold red",
    # Estados de conexión
    "mqtt_on": "bold green",
    "mqtt_off": "bold red",
    "lora_sim": "bold yellow",
    "lora_core": "bold green",
}

# ── Estilo brutalista compartido ─────────────────────────────
BOX_STYLE = box.SQUARE

TABLE_KWARGS = {
    "box": BOX_STYLE,
    "padding": (0, 1),
    "show_lines": True,
    "border_style": COLORS["border"],
}

PANEL_KWARGS = {
    "box": BOX_STYLE,
    "padding": (1, 2),
    "border_style": COLORS["border"],
}

PANEL_COMPACT_KWARGS = {
    "box": BOX_STYLE,
    "padding": (0, 1),
    "border_style": COLORS["border"],
}

PANEL_CARD_KWARGS = {
    "box": BOX_STYLE,
    "padding": (1, 1),
    "border_style": COLORS["info"],
}

# ── Indicadores textuales (reemplazan emojis) ────────────────
ICON = {
    "ok": "[green][OK][/green]",
    "err": "[red][ERR][/red]",
    "warn": "[yellow][!!][/yellow]",
    "info": "[cyan][--][/cyan]",
    "live": "[green]● LIVE[/green]",
    "live_off": "[dim]○ LIVE[/dim]",
    "pause": "[yellow]|| PAUSADO[/yellow]",
    "play": "[green]>> EN VIVO[/green]",
    "connected": "[green]ON[/green]",
    "disconnected": "[red]OFF[/red]",
    "mqtt_on": "[bold green]■ MQTT[/bold green]",
    "mqtt_off": "[bold red]□ MQTT[/bold red]",
    "tip": "[cyan]»[/cyan]",
    "clock": "[dim]⏱[/dim]",
    "arrow_up": "↑",
    "arrow_down": "↓",
    "arrow_right": "→",
    "bullet": "·",
    "dash": "—",
    "block": "█",
    "section": "┃",
    "dot_sep": " · ",
}


# ── Helpers ──────────────────────────────────────────────────

def styled_table(title: str, **extra):
    """Crea una Rich Table con estilo brutalista."""
    return Table(title=title.upper(), **{**TABLE_KWARGS, **extra})


def styled_panel(content, title: str = "", **extra):
    """Crea un Rich Panel con estilo brutalista."""
    kwargs = {**PANEL_KWARGS, **extra}
    if title:
        kwargs["title"] = title.upper()
    return Panel(content, **kwargs)


def styled_panel_compact(content, title: str = "", **extra):
    """Crea un Rich Panel compacto con estilo brutalista."""
    kwargs = {**PANEL_COMPACT_KWARGS, **extra}
    if title:
        kwargs["title"] = title.upper()
    return Panel(content, **kwargs)


def styled_card(content, title: str = "", border_style: str = "", **extra):
    """Crea un Panel tipo card para KPIs y métricas."""
    kwargs = {**PANEL_CARD_KWARGS, **extra}
    if title:
        kwargs["title"] = f"[bold]{title.upper()}[/bold]"
    if border_style:
        kwargs["border_style"] = border_style
    return Panel(content, **kwargs)


def section_rule(label: str = "", style: str = "bright_white"):
    """Crea un separador visual entre secciones."""
    if label:
        return Rule(title=label.upper(), style=style, characters="─")
    return Rule(style=style, characters="─")


def status_badge(label: str, state: str = "ok") -> str:
    """Genera un badge textual con color semántico."""
    color_map = {
        "ok": COLORS["success"],
        "err": COLORS["error"],
        "warn": COLORS["warning"],
        "info": COLORS["info"],
        "muted": COLORS["muted"],
    }
    color = color_map.get(state, COLORS["muted"])
    return f"[{color}][{label.upper()}][/{color}]"


def kpi_value(value, threshold_warn=None, threshold_bad=None) -> str:
    """Formatea un valor KPI con color según umbrales."""
    style = COLORS["kpi_good"]
    numeric_value = None
    if isinstance(value, (int, float)):
        numeric_value = float(value)
    else:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = None

    if numeric_value is not None and threshold_warn is not None and numeric_value >= threshold_warn:
        style = COLORS["kpi_warn"]
    if numeric_value is not None and threshold_bad is not None and numeric_value >= threshold_bad:
        style = COLORS["kpi_bad"]

    return f"[{style}]{value}[/{style}]"


def friendly_error(message: str, hint: str = "") -> str:
    """Error amigable de una línea con sugerencia opcional."""
    line = f"  [red]✗[/red] {message}"
    if hint:
        line += f"  [dim]→ {hint}[/dim]"
    return line
