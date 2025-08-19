#!/usr/bin/env python3
"""
Wave CLI - Command Line Interface for LoRa operations
Con modo interactivo completo usando Click y Rich
"""

import click
import time
import sys
import shlex
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.text import Text

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

def print_banner():
    """Imprime el banner con Rich"""
    banner_text = Text(BANNER, style=banner)
    
    panel = Panel.fit(
        banner_text,
        title=f"[bold yellow]Wave CLI {version}[/bold yellow]",
        subtitle=f"[green]Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/green]",
        border_style="white"
    )
    
    console.print(panel)
    console.print("[yellow]Long Range Radio Communication Tool[/yellow]", justify="center")
    console.print("[dim]Escribe 'help' para ver comandos o 'exit' para salir[/dim]", justify="center")
    console.print()

# Configuración global simulada
config = {
    "frequency": 915.0,
    "power": 14,
    "bandwidth": 125,
    "spreading_factor": 7,
    "coding_rate": "4/5"
}

# Variable para controlar el modo interactivo
interactive_mode = False

# =============================================================================
# COMANDOS DEL CLI
# =============================================================================

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help='Mostrar versión')
@click.option('--interactive', '-i', is_flag=True, help='Modo interactivo')
def cli(ctx, version, interactive):
    """
    Wave CLI - Interfaz de línea de comandos para comunicaciones LoRa
    
    Herramienta para gestionar módulos LoRa, enviar/recibir mensajes
    y configurar parámetros de comunicación.
    """
    global interactive_mode
    
    if version:
        console.print("[bold green]Wave CLI v1.0[/bold green]")
        return
    
    if interactive or ctx.invoked_subcommand is None:
        interactive_mode = True
        start_interactive_mode()
    elif ctx.invoked_subcommand is None:
        print_banner()
        console.print("[cyan]Usa --help para ver todos los comandos disponibles[/cyan]")
        console.print("[cyan]Usa --interactive o -i para modo interactivo[/cyan]")


def start_interactive_mode():
    """Inicia el modo interactivo del CLI"""
    print_banner()
    
    console.print("[bold green]🚀 Modo interactivo activado[/bold green]")
    console.print("[dim]Comandos disponibles: send, listen, config, status, scan, help, clear, exit[/dim]")
    console.print()
    
    # Historial de comandos simple
    command_history = []
    
    while True:
        try:
            # Prompt personalizado con Rich
            user_input = Prompt.ask(
                "[bold cyan]Wave CLI[/bold cyan]",
                console=console
            ).strip()
            
            if not user_input:
                continue
            
            # Agregar al historial
            command_history.append(user_input)
            
            # Parsear comando
            try:
                args = shlex.split(user_input)
            except ValueError:
                console.print("[red]❌ Error: Comando mal formateado[/red]")
                continue
            
            if not args:
                continue
            
            command = args[0].lower()
            params = args[1:]
            
            # Comandos especiales del modo interactivo
            if command in ['exit', 'quit', 'q']:
                console.print("[yellow]👋 ¡Hasta luego![/yellow]")
                break
            
            elif command == 'clear':
                console.clear()
                print_banner()
                continue
            
            elif command == 'history':
                show_command_history(command_history)
                continue
            
            elif command == 'help':
                show_interactive_help()
                continue
            
            # Ejecutar comandos principales
            try:
                execute_command(command, params)
            except Exception as e:
                console.print(f"[red]❌ Error ejecutando comando: {e}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 ¡Hasta luego![/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]👋 ¡Hasta luego![/yellow]")
            break


def execute_command(command, params):
    """Ejecuta comandos en modo interactivo"""
    if command == 'send':
        if not params:
            console.print("[red]❌ Error: Falta el mensaje a enviar[/red]")
            console.print("[yellow]Uso: send <mensaje> [--power <valor>] [--frequency <valor>][/yellow]")
            return
        
        # Parsear parámetros opcionales
        message_parts = []
        power = None
        frequency = None
        
        i = 0
        while i < len(params):
            if params[i] == '--power' and i + 1 < len(params):
                power = int(params[i + 1])
                i += 2
            elif params[i] == '--frequency' and i + 1 < len(params):
                frequency = float(params[i + 1])
                i += 2
            else:
                message_parts.append(params[i])
                i += 1
        
        message = ' '.join(message_parts)
        interactive_send(message, power, frequency)
    
    elif command == 'listen':
        timeout = 30
        channel = None
        
        # Parsear parámetros
        i = 0
        while i < len(params):
            if params[i] == '--timeout' and i + 1 < len(params):
                timeout = int(params[i + 1])
                i += 2
            elif params[i] == '--channel' and i + 1 < len(params):
                channel = int(params[i + 1])
                i += 2
            else:
                i += 1
        
        interactive_listen(timeout, channel)
    
    elif command == 'config':
        if len(params) >= 2:
            interactive_config(params[0], params[1])
        elif len(params) == 0:
            interactive_config(None, None)
        else:
            console.print("[yellow]Uso: config [parámetro] [valor][/yellow]")
    
    elif command == 'status':
        interactive_status()
    
    elif command == 'scan':
        # Parsear parámetros opcionales
        range_start = 915.0
        range_end = 928.0
        step = 0.2
        
        i = 0
        while i < len(params):
            if params[i] == '--range-start' and i + 1 < len(params):
                range_start = float(params[i + 1])
                i += 2
            elif params[i] == '--range-end' and i + 1 < len(params):
                range_end = float(params[i + 1])
                i += 2
            elif params[i] == '--step' and i + 1 < len(params):
                step = float(params[i + 1])
                i += 2
            else:
                i += 1
        
        interactive_scan(range_start, range_end, step)
    
    else:
        console.print(f"[red]❌ Comando desconocido: {command}[/red]")
        console.print("[yellow]Escribe 'help' para ver comandos disponibles[/yellow]")


def show_interactive_help():
    """Muestra ayuda del modo interactivo"""
    table = Table(title="📚 Comandos Disponibles")
    table.add_column("Comando", style="cyan", width=15)
    table.add_column("Descripción", style="white")
    table.add_column("Ejemplo", style="dim")
    
    commands = [
        ("send", "Enviar mensaje LoRa", "send 'Hola mundo' --power 20"),
        ("listen", "Escuchar mensajes", "listen --timeout 60 --channel 5"),
        ("config", "Ver/cambiar configuración", "config frequency 915.5"),
        ("status", "Estado del módulo", "status"),
        ("scan", "Escanear canales", "scan --range-start 915 --range-end 920"),
        ("help", "Mostrar esta ayuda", "help"),
        ("clear", "Limpiar pantalla", "clear"),
        ("history", "Ver historial de comandos", "history"),
        ("exit", "Salir del CLI", "exit, quit, q"),
    ]
    
    for cmd, desc, example in commands:
        table.add_row(cmd, desc, example)
    
    console.print(table)


def show_command_history(history):
    """Muestra el historial de comandos"""
    if not history:
        console.print("[yellow]No hay comandos en el historial[/yellow]")
        return
    
    table = Table(title="📜 Historial de Comandos")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Comando", style="white")
    table.add_column("Tiempo", style="dim")
    
    for i, cmd in enumerate(history[-10:], 1):  # Últimos 10
        table.add_row(str(i), cmd, "hace unos momentos")
    
    console.print(table)


# =============================================================================
# IMPLEMENTACIONES INTERACTIVAS DE LOS COMANDOS
# =============================================================================

def interactive_send(message, power=None, frequency=None):
    """Versión interactiva del comando send"""
    tx_power = power if power is not None else config['power']
    tx_freq = frequency if frequency is not None else config['frequency']
    
    table = Table(title="📡 Información del Mensaje")
    table.add_column("Parámetro", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Mensaje", f'"{message}"')
    table.add_row("Frecuencia", f"{tx_freq} MHz")
    table.add_row("Potencia", f"{tx_power} dBm")
    table.add_row("Longitud", f"{len(message)} bytes")
    
    console.print(table)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Enviando mensaje...", total=None)
        time.sleep(2)
    
    console.print("[bold green]✅ Mensaje enviado correctamente[/bold green]")


def interactive_listen(timeout, channel=None):
    """Versión interactiva del comando listen"""
    console.print(f"[cyan]👂 Escuchando mensajes LoRa por {timeout} segundos...[/cyan]")
    
    if channel:
        console.print(f"[yellow]📻 Canal: {channel}[/yellow]")
    
    console.print("[dim]Presiona Ctrl+C para detener[/dim]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Escuchando...", total=None)
            
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < timeout:
                time.sleep(0.1)
                
                # Simular mensajes recibidos
                if time.time() - start_time > 3 and message_count == 0:
                    progress.stop()
                    console.print("[green]📨 Mensaje recibido: 'Hola desde nodo remoto'[/green]")
                    console.print(f"[dim]   RSSI: -75 dBm | SNR: 8.5 dB[/dim]")
                    message_count += 1
                    progress.start()
                    task = progress.add_task("Escuchando...", total=None)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]🔇 Escucha detenida por el usuario[/yellow]")
    else:
        console.print(f"[blue]⏰ Tiempo de escucha completado ({message_count} mensajes recibidos)[/blue]")


def interactive_config(parameter=None, value=None):
    """Versión interactiva del comando config"""
    if parameter is None:
        # Mostrar configuración actual
        table = Table(title="⚙️ Configuración Actual LoRa")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="green")
        table.add_column("Descripción", style="dim")
        
        descriptions = {
            "frequency": "Frecuencia de operación",
            "power": "Potencia de transmisión",
            "bandwidth": "Ancho de banda",
            "spreading_factor": "Factor de dispersión",
            "coding_rate": "Tasa de codificación"
        }
        
        for key, val in config.items():
            unit = ""
            if key == "frequency": unit = " MHz"
            elif key == "power": unit = " dBm"
            elif key == "bandwidth": unit = " kHz"
            
            table.add_row(
                key.replace("_", " ").title(),
                f"{val}{unit}",
                descriptions.get(key, "")
            )
        
        console.print(table)
    
    elif parameter and value:
        # Modificar configuración
        if parameter in config:
            old_value = config[parameter]
            
            try:
                if isinstance(old_value, (int, float)):
                    config[parameter] = type(old_value)(value)
                else:
                    config[parameter] = value
                
                console.print(f"[green]✅ {parameter} actualizado: {old_value} → {config[parameter]}[/green]")
            except ValueError:
                console.print(f"[red]❌ Error: '{value}' no es un valor válido para {parameter}[/red]")
        else:
            console.print(f"[red]❌ Parámetro desconocido: {parameter}[/red]")
            console.print("[yellow]Parámetros válidos: frequency, power, bandwidth, spreading_factor, coding_rate[/yellow]")


def interactive_status():
    """Versión interactiva del comando status"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Obteniendo estado...", total=None)
        time.sleep(1)
    
    table = Table(title="📊 Estado del Módulo LoRa")
    table.add_column("Parámetro", style="cyan")
    table.add_column("Estado", style="green")
    table.add_column("Detalles", style="dim")
    
    table.add_row("Conexión", "✅ Conectado", "Puerto: /dev/ttyUSB0")
    table.add_row("Señal", "📡 -65 dBm", "Buena intensidad")
    table.add_row("Temperatura", "🌡️ 25°C", "Normal")
    table.add_row("Voltaje", "🔋 3.3V", "Estable")
    table.add_row("Memoria", "💾 85% libre", "1.2MB disponible")
    table.add_row("Uptime", "⏱️ 02:34:12", "Desde último reinicio")
    
    console.print(table)


def interactive_scan(range_start, range_end, step):
    """Versión interactiva del comando scan"""
    console.print(f"[cyan]🔍 Escaneando rango: {range_start} - {range_end} MHz[/cyan]")
    
    channels = []
    freq = range_start
    while freq <= range_end:
        channels.append(freq)
        freq += step
    
    table = Table(title="📻 Resultados del Escaneo")
    table.add_column("Canal", justify="right", style="cyan")
    table.add_column("Frecuencia", justify="center", style="yellow")
    table.add_column("Estado", justify="center")
    table.add_column("RSSI", justify="right", style="dim")
    
    with Progress(console=console) as progress:
        task = progress.add_task("Escaneando...", total=len(channels))
        
        for i, freq in enumerate(channels):
            time.sleep(0.05)
            
            import random
            is_active = random.choice([True, False, False, False])
            rssi = random.randint(-95, -60) if is_active else None
            
            status_text = "[green]📡 Activo[/green]" if is_active else "[dim]⚫ Libre[/dim]"
            rssi_text = f"{rssi} dBm" if rssi else "-"
            
            table.add_row(
                str(i + 1),
                f"{freq:.1f} MHz",
                status_text,
                rssi_text
            )
            
            progress.update(task, advance=1)
    
    console.print(table)


if __name__ == '__main__':
    try:
        import rich
        import click
    except ImportError as e:
        print("❌ Faltan dependencias. Instala con:")
        print("pip install click rich")
        sys.exit(1)
    
    cli()