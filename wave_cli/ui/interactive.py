"""
Modo interactivo para Wave CLI
"""

import difflib
import importlib
import shlex
import sys
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt

from ..commands.mqtt_commands import MqttCommands
from ..commands.lora_commands import LoRaCommands
from ..commands.general_commands import GeneralCommands
from .theme import styled_panel, ICON, COLORS, friendly_error
from .formatters import format_duration

console = Console()


class InteractiveMode:
    """Gestor del modo interactivo del CLI"""
    
    def __init__(self, config):
        self.config = config
        self.command_history = []
        self.command_timestamps = []
        self.max_history = max(10, int(getattr(config.ui, 'max_messages', 1000)))
        self._prompt_session = None
        self._session_start = datetime.now()
        
        # Inicializar comandos
        self.mqtt_commands = MqttCommands(config)
        self.lora_commands = LoRaCommands(config)
        self.general_commands = GeneralCommands(config)
        
        # Mapeo de comandos
        self.command_map = {
            # MQTT Commands
            'connect': lambda params: self.mqtt_commands.connect(params),
            'monitor': lambda params: self.mqtt_commands.monitor(params),
            'messages': lambda params: self.mqtt_commands.messages(params),
            'subscribe': lambda params: self.mqtt_commands.subscribe(params),
            
            # LoRa Commands
            'send': lambda params: self.lora_commands.send(params),
            'listen': lambda params: self.lora_commands.listen(params),
            'status': lambda params: self.lora_commands.status(params),
            
            # General Commands
            'config': lambda params: self.general_commands.config(params),
            'help': self.show_help,
            'guide': self.show_guide,
            'history': self.show_history,
            'clear': self.clear_screen,
            # Namespaces simplificados
            'mqtt': self._execute_mqtt_namespace,
            'lora': self._execute_lora_namespace,
        }

        self.mqtt_namespace_commands = {'connect', 'monitor', 'messages', 'subscribe'}
        self.lora_namespace_commands = {'send', 'listen', 'status'}

        self.alias_map = {
            'c': 'connect',
            'conn': 'connect',
            'mon': 'monitor',
            'msg': 'messages',
            'msgs': 'messages',
            'sub': 'subscribe',
            'tx': 'send',
            'rx': 'listen',
            'stat': 'status',
            'cfg': 'config',
            'h': 'help',
            'hist': 'history',
            'cls': 'clear',
            'start': 'guide',
        }

        self._completion_words = sorted({
            *self.command_map.keys(),
            *self.alias_map.keys(),
            '--topic', '--filter', '--port', '--limit', '--device', '--timeout',
            '--channel', '--range-start', '--range-end', '--step', '--power', '--frequency'
        })

    def _get_prompt_session(self):
        """Crea sesión de prompt con autocompletado/sugerencias cuando esté disponible"""
        if self._prompt_session is not None:
            return self._prompt_session

        if not sys.stdin.isatty():
            return None

        try:
            prompt_toolkit = importlib.import_module('prompt_toolkit')
            completion_module = importlib.import_module('prompt_toolkit.completion')
            history_module = importlib.import_module('prompt_toolkit.history')
            auto_suggest_module = importlib.import_module('prompt_toolkit.auto_suggest')
        except ImportError:
            return None

        completer = completion_module.WordCompleter(self._completion_words, ignore_case=True, sentence=True)
        history = history_module.InMemoryHistory()
        self._prompt_session = prompt_toolkit.PromptSession(
            completer=completer,
            auto_suggest=auto_suggest_module.AutoSuggestFromHistory(),
            history=history,
        )
        return self._prompt_session

    def _read_user_input(self) -> str:
        """Lee input con autocompletado si está disponible"""
        session = self._get_prompt_session()
        if session is not None:
            return session.prompt("wave> ").strip()

        return Prompt.ask(
            "[bold cyan]wave[/bold cyan]",
            console=console
        ).strip()

    def _normalize_command(self, command: str) -> str:
        """Resuelve aliases a comando canónico"""
        return self.alias_map.get(command, command)

    def _suggest_commands(self, command: str):
        """Sugiere comandos cercanos al input del usuario"""
        candidates = sorted({*self.command_map.keys(), *self.alias_map.keys()})
        return difflib.get_close_matches(command, candidates, n=3, cutoff=0.5)

    def _execute_mqtt_namespace(self, params):
        """Ejecuta comando dentro del namespace mqtt"""
        if not params:
            console.print(friendly_error(
                "Falta el subcomando",
                "mqtt <connect|monitor|messages|subscribe>"
            ))
            return

        subcommand = self._normalize_command(params[0].lower())
        subparams = params[1:]
        if subcommand not in self.mqtt_namespace_commands:
            console.print(friendly_error(
                f"Subcomando desconocido: {subcommand}",
                "Opciones: connect, monitor, messages, subscribe"
            ))
            return

        self._execute_command(subcommand, subparams)

    def _execute_lora_namespace(self, params):
        """Ejecuta comando dentro del namespace lora"""
        if not params:
            console.print(friendly_error(
                "Falta el subcomando",
                "lora <send|listen|scan|status>"
            ))
            return

        subcommand = self._normalize_command(params[0].lower())
        subparams = params[1:]
        if subcommand not in self.lora_namespace_commands:
            console.print(friendly_error(
                f"Subcomando desconocido: {subcommand}",
                "Opciones: send, listen, status"
            ))
            return

        self._execute_command(subcommand, subparams)
    
    def start(self):
        """Inicia el modo interactivo"""
        console.print(f"  {ICON['ok']} Listo. Escribe un comando.\n")
        
        while True:
            try:
                # Prompt personalizado
                user_input = self._read_user_input()
                
                if not user_input:
                    continue
                
                # Agregar al historial
                self.command_history.append(user_input)
                self.command_timestamps.append(datetime.now())
                if len(self.command_history) > self.max_history:
                    del self.command_history[:-self.max_history]
                    del self.command_timestamps[:-self.max_history]
                
                # Parsear comando
                try:
                    args = shlex.split(user_input)
                except ValueError:
                    console.print(friendly_error("Comando mal formateado"))
                    continue
                
                if not args:
                    continue
                
                command = args[0].lower()
                command = self._normalize_command(command)
                params = args[1:]
                
                # Comandos especiales de control
                if command in ['exit', 'quit', 'q']:
                    self._show_session_outro()
                    break
                
                # Ejecutar comando
                self._execute_command(command, params)
                
            except KeyboardInterrupt:
                console.print()
                self._show_session_outro()
                break
            except EOFError:
                console.print()
                self._show_session_outro()
                break
    
    def _execute_command(self, command: str, params: list):
        """Ejecuta un comando específico"""
        if command in self.command_map:
            try:
                self.command_map[command](params)
            except Exception as e:
                console.print(friendly_error(f"Error: {e}"))
        else:
            suggestions = self._suggest_commands(command)
            if suggestions:
                suggestion_text = ', '.join(suggestions)
                console.print(friendly_error(
                    f"Comando desconocido: {command}",
                    f"Quizás: {suggestion_text}"
                ))
            else:
                console.print(friendly_error(
                    f"Comando desconocido: {command}",
                    'Escribe "help" para ver comandos'
                ))
    
    def show_help(self, params=None):
        """Muestra ayuda compacta del modo interactivo"""
        help_text = """
  [bold cyan]MQTT[/bold cyan]
    [cyan]connect[/cyan] <broker>           Conectar al broker       [dim]connect mqtt://localhost[/dim]
    [cyan]monitor[/cyan]                    Streaming en tiempo real  [dim]monitor --filter dev01[/dim]
    [cyan]messages[/cyan]                   Mensajes recientes        [dim]messages --limit 20[/dim]
    [cyan]subscribe[/cyan] <topic>          Suscribirse a tópico      [dim]subscribe sensors/#[/dim]

  [bold cyan]LORA[/bold cyan]
    [cyan]send[/cyan] <mensaje>             Enviar mensaje            [dim]send "hola" --power 20[/dim]
    [cyan]listen[/cyan]                     Escuchar mensajes         [dim]listen --timeout 60[/dim]
    [cyan]status[/cyan]                     Estado del módulo         [dim]status[/dim]

  [bold cyan]GENERAL[/bold cyan]
    [cyan]config[/cyan]                     Ver/cambiar configuración [dim]config mqtt[/dim]
    [cyan]help[/cyan]                       Esta ayuda
    [cyan]guide[/cyan]                      Guía de inicio rápido
    [cyan]clear[/cyan]                      Limpiar pantalla
    [cyan]exit[/cyan]                       Salir                     [dim]exit, quit, q[/dim]

  [dim]Aliases: c=connect  mon=monitor  msg=messages  tx=send  rx=listen  cfg=config[/dim]"""
        console.print(help_text)
    
    def show_guide(self, params=None):
        """Muestra guía de inicio rápido paso a paso"""
        guide_text = """
  [bold white]INICIO RÁPIDO[/bold white]

  [bold]1.[/bold] Conectar al broker MQTT:
     [cyan]connect mqtt://broker.emqx.io[/cyan]

  [bold]2.[/bold] Monitorear mensajes en tiempo real:
     [cyan]monitor[/cyan]

  [bold]3.[/bold] Ver mensajes recientes:
     [cyan]messages --limit 10[/cyan]

  [bold]4.[/bold] Enviar un mensaje LoRa:
     [cyan]send "Hola mundo" --power 20[/cyan]

  [bold]5.[/bold] Ver estado del sistema:
     [cyan]status[/cyan]

  [dim]Tip: usa Tab para autocompletar comandos[/dim]"""
        console.print(guide_text)
    
    def show_history(self, params=None):
        """Muestra el historial de comandos"""
        if not self.command_history:
            console.print(f"  {ICON['warn']} No hay comandos en el historial")
            return
        
        entries = list(zip(self.command_history, self.command_timestamps))[-10:]
        console.print()
        for i, (cmd, ts) in enumerate(entries, 1):
            console.print(f"  [dim]{i:2d}.[/dim] {cmd}  [dim]{ts.strftime('%H:%M:%S')}[/dim]")
        console.print()
    
    def clear_screen(self, params=None):
        """Limpia la pantalla"""
        console.clear()

    def _show_session_outro(self):
        """Muestra resumen de sesión al salir"""
        elapsed = datetime.now() - self._session_start
        total_seconds = int(elapsed.total_seconds())
        n_cmds = len(self.command_history)
        console.print(f"\n  [dim]Sesión: {format_duration(total_seconds)} · {n_cmds} comando{'s' if n_cmds != 1 else ''} · ¡Hasta luego![/dim]\n")