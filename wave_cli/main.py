#!/usr/bin/env python3
"""
Wave CLI - Command Line Interface for LoRa operations
Con modo interactivo completo usando Click y Rich
"""

import sys

import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from .config.settings import WaveConfig
from .ui.interactive import InteractiveMode
from .ui.theme import ICON, PANEL_KWARGS, BOX_STYLE
from .commands.mqtt_commands import MqttCommands
from .commands.lora_commands import LoRaCommands
from constant.info import version
from constant.colors import banner

# Inicializar consola Rich
console = Console()

# Banner ASCII para Wave CLI
BANNER = """
██╗    ██╗ █████╗ ██╗   ██╗███████╗     ██████╗██╗     ██╗
██║    ██║██╔══██╗██║   ██║██╔════╝    ██╔════╝██║     ██║
██║ █╗ ██║███████║██║   ██║█████╗      ██║     ██║     ██║
██║███╗██║██╔══██║╚██╗ ██╔╝██╔══╝      ██║     ██║     ██║
╚███╔███╔╝██║  ██║ ╚████╔╝ ███████╗    ╚██████╗███████╗██║
 ╚══╝╚══╝ ╚═╝  ╚═╝  ╚═══╝  ╚══════╝     ╚═════╝╚══════╝╚═╝
"""

def print_banner(config=None):
    """Imprime el banner con Rich y una línea de ayuda"""
    banner_text = Text(BANNER, style=banner)
    
    panel = Panel.fit(
        banner_text,
        title=f"[bold yellow]WAVE CLI {version}[/bold yellow]",
        subtitle=f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="bright_white",
        box=BOX_STYLE,
        padding=(0, 2),
    )
    
    console.print(panel)
    console.print()
    console.print('  [dim]"help" = comandos  ·  "guide" = inicio rápido  ·  Tab = autocompletado  ·  "q" = salir[/dim]')
    console.print()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', 'show_version', is_flag=True, help='Mostrar versión')
@click.option('--interactive', '-i', is_flag=True, help='Modo interactivo')
@click.option('--config', '-c', help='Archivo de configuración personalizado')
def cli(ctx, show_version, interactive, config):
    """
    Wave CLI - Interfaz de línea de comandos para comunicaciones LoRa
    
    Herramienta para gestionar módulos LoRa, enviar/recibir mensajes
    y configurar parámetros de comunicación.
    """
    if show_version:
        console.print(f"[bold green]Wave CLI {version}[/bold green]")
        return
    
    # Cargar configuración
    wave_config = WaveConfig(config_file=config)
    ctx.ensure_object(dict)
    ctx.obj["config"] = wave_config
    
    if interactive or ctx.invoked_subcommand is None:
        print_banner(config=wave_config)
        interactive_mode = InteractiveMode(wave_config)
        interactive_mode.start()


@cli.group()
@click.pass_context
def mqtt(ctx):
    """Comandos MQTT en modo no interactivo"""


@mqtt.command("connect")
@click.argument("broker_url")
@click.option("--port", type=int, default=None, help="Puerto MQTT")
@click.pass_context
def mqtt_connect(ctx, broker_url, port):
    """Conectar a broker MQTT"""
    wave_config = ctx.obj["config"]
    params = [broker_url]
    if port is not None:
        params.extend(["--port", str(port)])
    MqttCommands(wave_config).connect(params)


@mqtt.command("monitor")
@click.option("--topic", default="#", help="Tópico MQTT")
@click.option("--filter", "filter_text", default=None, help="Filtro de payload")
@click.pass_context
def mqtt_monitor(ctx, topic, filter_text):
    """Monitorear mensajes MQTT en tiempo real"""
    wave_config = ctx.obj["config"]
    params = ["--topic", topic]
    if filter_text:
        params.extend(["--filter", filter_text])
    MqttCommands(wave_config).monitor(params)


@mqtt.command("messages")
@click.option("--limit", type=int, default=10, help="Cantidad de mensajes")
@click.option("--device", default=None, help="Filtrar por dispositivo")
@click.pass_context
def mqtt_messages(ctx, limit, device):
    """Mostrar mensajes MQTT recientes"""
    wave_config = ctx.obj["config"]
    params = ["--limit", str(limit)]
    if device:
        params.extend(["--device", device])
    MqttCommands(wave_config).messages(params)


@mqtt.command("subscribe")
@click.argument("topic")
@click.pass_context
def mqtt_subscribe(ctx, topic):
    """Suscribirse a un tópico MQTT"""
    wave_config = ctx.obj["config"]
    MqttCommands(wave_config).subscribe([topic])


@cli.group()
@click.pass_context
def lora(ctx):
    """Comandos LoRa en modo no interactivo"""


@lora.command("send")
@click.argument("message")
@click.option("--power", type=int, default=None, help="Potencia TX")
@click.option("--frequency", type=float, default=None, help="Frecuencia TX")
@click.pass_context
def lora_send(ctx, message, power, frequency):
    """Enviar mensaje LoRa"""
    wave_config = ctx.obj["config"]
    params = [message]
    if power is not None:
        params.extend(["--power", str(power)])
    if frequency is not None:
        params.extend(["--frequency", str(frequency)])
    LoRaCommands(wave_config).send(params)


@lora.command("listen")
@click.option("--timeout", type=int, default=30, help="Tiempo de escucha")
@click.option("--channel", type=int, default=None, help="Canal")
@click.pass_context
def lora_listen(ctx, timeout, channel):
    """Escuchar mensajes LoRa"""
    wave_config = ctx.obj["config"]
    params = ["--timeout", str(timeout)]
    if channel is not None:
        params.extend(["--channel", str(channel)])
    LoRaCommands(wave_config).listen(params)


@lora.command("status")
@click.pass_context
def lora_status(ctx):
    """Mostrar estado LoRa"""
    wave_config = ctx.obj["config"]
    LoRaCommands(wave_config).status([])


def main():
    """Punto de entrada principal"""
    cli()


if __name__ == '__main__':
    main()