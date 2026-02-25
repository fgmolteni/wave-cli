"""
Comandos MQTT para Wave CLI
"""

import sys
import select
import time
from urllib.parse import urlparse
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.text import Text

from ..ui.theme import (
    ICON, COLORS, styled_table, styled_panel_compact,
    friendly_error,
)
from ..ui.formatters import (
    format_timestamp, parse_options, truncate_payload, format_duration,
)

try:
    import termios
    import tty
except ImportError:
    termios = None
    tty = None

console = Console()


class MqttCommands:
    """Implementación de comandos MQTT"""
    
    def __init__(self, config):
        self.config = config

    @staticmethod
    @contextmanager
    def _raw_stdin_if_tty():
        """Activa modo raw de stdin si es posible (Linux/TTY)"""
        if termios is None or tty is None or not sys.stdin.isatty():
            yield False
            return

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            yield True
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    @staticmethod
    def _read_key_nonblocking(timeout=0.0):
        """Lee una tecla sin bloquear, retorna None si no hay entrada"""
        if not sys.stdin.isatty():
            return None
        readable, _, _ = select.select([sys.stdin], [], [], timeout)
        if not readable:
            return None
        return sys.stdin.read(1)

    @staticmethod
    def _extract_device_id(topic, payload):
        """Intenta inferir device_id desde tópico/payload"""
        topic_value = str(topic or '').strip()
        payload_value = str(payload or '').strip()

        parts = [p for p in topic_value.split('/') if p]
        if len(parts) >= 2 and parts[0].lower() in {'lora', 'device', 'devices', 'sensors', 'nodes'}:
            return parts[1]
        if parts:
            return parts[0]

        lowered = payload_value.lower()
        marker = 'device:'
        if marker in lowered:
            idx = lowered.find(marker)
            raw = payload_value[idx + len(marker):].strip()
            token = raw.split()[0] if raw else 'unknown'
            return token.strip(',;') or 'unknown'

        return 'unknown'

    @staticmethod
    def _build_messages_table(rows, available_width=0):
        """Tabla de mensajes recientes"""
        table = styled_table("MENSAJES")
        topic_width = 30 if available_width >= 160 else 22
        payload_width = 70
        if available_width and available_width < 160:
            payload_width = max(36, available_width - (10 + topic_width + 6 + 8))

        table.add_column("Hora", style="cyan", width=10)
        table.add_column("Tópico", style="yellow", width=topic_width)
        table.add_column("Payload", style="white", width=payload_width)
        table.add_column("QoS", justify="center", style="dim", width=5)

        for row in rows:
            table.add_row(row['time'], row['topic'], row['payload'], str(row['qos']))

        if not rows:
            table.add_row("--:--:--", "-", "Sin mensajes todavía", "-")

        return table

    @staticmethod
    def _build_devices_table(device_stats):
        """Tabla de dispositivos detectados"""
        table = styled_table("DISPOSITIVOS")
        table.add_column("Device", style="cyan", width=20)
        table.add_column("Msgs", justify="right", style="green", width=8)
        table.add_column("Último", style="yellow", width=10)

        if not device_stats:
            table.add_row("-", "0", "--:--:--")
            return table

        sorted_items = sorted(
            device_stats.items(),
            key=lambda item: item[1].get('count', 0),
            reverse=True,
        )[:10]

        for device_id, stats in sorted_items:
            table.add_row(
                device_id,
                str(stats.get('count', 0)),
                stats.get('last_seen', '--:--:--'),
            )

        return table

    @staticmethod
    def _build_monitor_view(
        topic,
        filter_text,
        message_count,
        rendered_count,
        msg_rate,
        start_time,
        rows,
        is_connected,
        paused=False,
        show_devices=False,
        device_stats=None,
    ):
        """Construye vista limpia: status line + mensajes (+dispositivos opcional)"""
        elapsed = max(0, int(time.time() - start_time))
        conn_icon = ICON['connected'] if is_connected else '[bold red]✗[/bold red]'
        conn_label = "conectado" if is_connected else "desconectado"
        pause_label = f"  {ICON['pause']} PAUSADO" if paused else ""
        filter_label = f"  filtro: {filter_text}" if filter_text else ""
        active_devices = len([d for d in (device_stats or {}).values() if d.get('count', 0) > 0])

        status_line = (
            f"  {conn_icon} {conn_label}  ·  "
            f"{message_count} msgs  ·  "
            f"{msg_rate:.1f} msg/s  ·  "
            f"{active_devices} devices  ·  "
            f"{format_duration(elapsed)}"
            f"{pause_label}{filter_label}"
        )

        header = styled_panel_compact(
            f"{status_line}\n"
            f"[dim]  {topic}  ·  p=pausa r=reanudar f=filtro d=devices q=salir[/dim]",
            title="MONITOR",
        )

        console_width = console.size.width
        messages_table = MqttCommands._build_messages_table(rows, available_width=console_width)

        parts = [header, Text(""), messages_table]

        if show_devices and device_stats:
            parts.append(Text(""))
            parts.append(MqttCommands._build_devices_table(device_stats))

        return Group(*parts)

    @staticmethod
    def _normalize_broker_target(raw_target, explicit_port=None):
        target = (raw_target or '').strip()
        if not target:
            return '', explicit_port

        host = target
        port = explicit_port

        if '://' in target:
            parsed = urlparse(target)
            host = parsed.hostname or ''
            if port is None and parsed.port is not None:
                port = parsed.port
        else:
            if target.startswith('['):
                closing = target.find(']')
                if closing != -1:
                    host = target[1:closing]
                    remainder = target[closing + 1:]
                    if port is None and remainder.startswith(':') and remainder[1:].isdigit():
                        port = int(remainder[1:])
            elif target.count(':') == 1:
                possible_host, possible_port = target.rsplit(':', 1)
                if possible_port.isdigit():
                    host = possible_host
                    if port is None:
                        port = int(possible_port)

        return host.strip(), port

    
    def connect(self, params):
        """Conectar a broker MQTT"""
        if not params:
            console.print(friendly_error(
                "Falta la URL del broker",
                "connect <broker_url> [--port <puerto>]"
            ))
            return
        
        broker_url = params[0]
        port = parse_options(params, {'--port': int}, start_index=1)['--port']
        broker_host, port = self._normalize_broker_target(broker_url, port)

        if not broker_host:
            console.print(f"{ICON['err']} Broker invalido")
            return
        
        client = self.config.get_mqtt_client()
        if client is None:
            console.print(friendly_error(
                "Cliente MQTT no disponible",
                "Compila el core Rust con: uvx maturin develop"
            ))
            return
        
        port_display = port if port else 1883
        console.print(f"[cyan]🔗 Conectando a {broker_host}:{port_display}...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Estableciendo conexión MQTT...", total=None)
            
            try:
                success = client.connect(broker_host, port)
                
                if success:
                    console.print(f"{ICON['ok']} Conectado exitosamente al broker MQTT")
                    console.print(f"[dim]Broker: {broker_host}:{port_display}[/dim]")
                    
                    # Actualizar configuración
                    self.config.update_mqtt_config(
                        broker_url=broker_host,
                        port=port_display
                    )
                else:
                    console.print(f"{ICON['err']} No se pudo conectar al broker")
                    console.print("[yellow]Verifica que el broker este activo y accesible[/yellow]")
            except Exception as e:
                console.print(f"{ICON['err']} Error de conexion: {e}")
    
    def monitor(self, params):
        """Streaming en tiempo real de mensajes MQTT"""
        client = self.config.get_mqtt_client()
        if client is None:
            console.print(friendly_error(
                "Cliente MQTT no disponible",
                "Compila el core Rust con: uvx maturin develop"
            ))
            return
        
        if not client.is_connected():
            console.print(friendly_error(
                "Sin conexion al broker",
                "connect <broker_url>"
            ))
            return
        
        topic = "#"  # Por defecto escuchar todos los topics
        filter_text = None
        parsed = parse_options(params, {'--topic': str, '--filter': str})
        if parsed['--topic'] is not None:
            topic = parsed['--topic']
        if parsed['--filter'] is not None:
            filter_text = parsed['--filter']
        
        console.print(f"[cyan]>> Iniciando monitoreo MQTT en topico: {topic}[/cyan]")
        if filter_text:
            console.print(f"[yellow]>> Filtro aplicado: {filter_text}[/yellow]")
        
        # Suscribirse al tópico
        if not client.subscribe(topic):
            console.print(f"{ICON['err']} No se pudo suscribir al topico")
            return
        
        # Iniciar listener
        client.start_listening()
        console.print(f"{ICON['ok']} Suscrito. Escuchando mensajes...")
        console.print()
        
        message_count = 0
        rendered_count = 0
        recent_keys = deque(maxlen=max(100, int(getattr(self.config.ui, 'max_messages', 1000))))
        recent_key_set = set()
        filter_lower = filter_text.lower() if filter_text else None
        poll_interval = max(0.1, float(getattr(self.config.ui, 'refresh_rate', 1.0)))
        display_rows = deque(maxlen=20)
        start_time = time.time()
        last_rate_checkpoint = start_time
        last_rate_count = 0
        msg_rate = 0.0
        paused = False
        stop_requested = False
        show_devices = False
        device_stats = {}

        try:
            refresh_per_second = max(2, int(round(1 / poll_interval)))
            initial_view = self._build_monitor_view(
                topic, filter_text, message_count, rendered_count,
                msg_rate, start_time, display_rows, client.is_connected(),
                paused, show_devices, device_stats,
            )

            with self._raw_stdin_if_tty(), Live(initial_view, console=console, refresh_per_second=refresh_per_second) as live:
                while not stop_requested:
                    key = self._read_key_nonblocking(timeout=poll_interval)
                    if key:
                        if key.lower() == 'p':
                            paused = True
                        elif key.lower() == 'r':
                            paused = False
                        elif key.lower() == 'q':
                            stop_requested = True
                            continue
                        elif key.lower() == 'd':
                            show_devices = not show_devices
                        elif key.lower() == 'f':
                            live.stop()
                            new_filter = console.input("[cyan]Nuevo filtro (vacío para limpiar): [/cyan]").strip()
                            filter_text = new_filter or None
                            filter_lower = filter_text.lower() if filter_text else None
                            live.start()

                    if paused:
                        now = time.time()
                        elapsed_since_checkpoint = max(0.0001, now - last_rate_checkpoint)
                        processed_since_checkpoint = message_count - last_rate_count
                        msg_rate = processed_since_checkpoint / elapsed_since_checkpoint
                        last_rate_checkpoint = now
                        last_rate_count = message_count

                        live.update(
                            self._build_monitor_view(
                                topic, filter_text, message_count, rendered_count,
                                msg_rate, start_time, display_rows, client.is_connected(),
                                paused, show_devices, device_stats,
                            ),
                            refresh=True,
                        )
                        continue

                    messages = client.get_messages(20)

                    for msg in messages:
                        msg_key = (
                            msg.get('timestamp', ''),
                            msg.get('topic', ''),
                            msg.get('payload', ''),
                            msg.get('qos', 0),
                        )
                        if msg_key in recent_key_set:
                            continue

                        if len(recent_keys) == recent_keys.maxlen:
                            oldest_key = recent_keys.popleft()
                            recent_key_set.discard(oldest_key)

                        recent_keys.append(msg_key)
                        recent_key_set.add(msg_key)
                        message_count += 1

                        payload = msg.get('payload', '')
                        if filter_lower and filter_lower not in payload.lower():
                            continue

                        rendered_count += 1
                        timestamp = format_timestamp(msg.get('timestamp'))
                        topic_value = msg.get('topic', '')
                        device_id = self._extract_device_id(topic_value, payload)
                        current_device = device_stats.get(device_id, {'count': 0, 'last_seen': '--:--:--'})
                        current_device['count'] = int(current_device.get('count', 0)) + 1
                        current_device['last_seen'] = timestamp
                        device_stats[device_id] = current_device

                        payload_display = truncate_payload(payload)
                        display_rows.append({
                            'time': timestamp,
                            'topic': topic_value,
                            'payload': payload_display,
                            'qos': msg.get('qos', 0),
                        })

                    now = time.time()
                    elapsed_since_checkpoint = max(0.0001, now - last_rate_checkpoint)
                    processed_since_checkpoint = message_count - last_rate_count
                    msg_rate = processed_since_checkpoint / elapsed_since_checkpoint
                    last_rate_checkpoint = now
                    last_rate_count = message_count

                    live.update(
                        self._build_monitor_view(
                            topic, filter_text, message_count, rendered_count,
                            msg_rate, start_time, display_rows, client.is_connected(),
                            paused, show_devices, device_stats,
                        ),
                        refresh=True,
                    )
        
        except KeyboardInterrupt:
            pass

        console.print(
            f"\n  [dim]Monitor: {format_duration(int(time.time() - start_time))} · "
            f"{message_count} procesados · {rendered_count} mostrados[/dim]\n"
        )
    
    def messages(self, params):
        """Ver mensajes MQTT recientes"""
        client = self.config.get_mqtt_client()
        if client is None:
            console.print(friendly_error(
                "Cliente MQTT no disponible",
                "Compila el core Rust con: uvx maturin develop"
            ))
            return
        
        if not client.is_connected():
            console.print(friendly_error(
                "Sin conexion al broker",
                "connect <broker_url>"
            ))
            return
        
        limit = 10
        device_id = None
        parsed = parse_options(params, {'--limit': int, '--device': str})
        if parsed['--limit'] is not None:
            limit = parsed['--limit']
        if parsed['--device'] is not None:
            device_id = parsed['--device']
        
        messages = client.get_messages(limit)
        
        if not messages:
            console.print(f"{ICON['warn']} No hay mensajes disponibles")
            return
        
        # Filtrar por device_id si se especifica
        if device_id:
            device_id_lower = device_id.lower()
            messages = [
                msg for msg in messages
                if device_id_lower in msg.get('payload', '').lower() or device_id_lower in msg.get('topic', '').lower()
            ]
            console.print(f"[cyan]>> Mostrando mensajes filtrados por: {device_id}[/cyan]")
        
        table = styled_table(f"ULTIMOS {len(messages)} MENSAJES MQTT")
        table.add_column("Hora", style="cyan", width=10)
        table.add_column("Tópico", style="yellow", width=20)
        table.add_column("Mensaje", style="white", width=40)
        table.add_column("QoS", justify="center", style="dim", width=5)
        
        for msg in messages:
            timestamp = format_timestamp(msg.get('timestamp'))
            payload = msg['payload']
            if len(payload) > 37:
                payload = payload[:37] + "..."
            
            table.add_row(
                timestamp,
                msg['topic'],
                payload,
                str(msg['qos'])
            )
        
        console.print(table)
    
    def subscribe(self, params):
        """Suscribirse a un tópico MQTT"""
        if not params:
            console.print(f"{ICON['err']} Falta el topico")
            console.print("[yellow]Uso: subscribe <topic>[/yellow]")
            return
        
        client = self.config.get_mqtt_client()
        if client is None:
            console.print(f"{ICON['err']} Cliente MQTT no disponible. Compila con: uvx maturin develop")
            return
        
        if not client.is_connected():
            console.print(f"{ICON['err']} Sin conexion al broker. Usa: connect <broker_url>")
            return
        
        topic = params[0]
        
        try:
            if client.subscribe(topic):
                console.print(f"{ICON['ok']} Suscrito exitosamente a: {topic}")
            else:
                console.print(f"{ICON['err']} Error al suscribirse a: {topic}")
        except Exception as e:
            console.print(f"{ICON['err']} Error de suscripcion: {e}")