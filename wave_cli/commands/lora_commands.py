"""
Comandos LoRa para Wave CLI
"""

import time
from collections import deque
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..ui.theme import styled_table, styled_panel_compact, ICON, friendly_error
from ..ui.formatters import format_timestamp, parse_options, parse_message_with_options, format_duration

console = Console()


class LoRaCommands:
    """Implementación de comandos LoRa"""
    
    def __init__(self, config):
        self.config = config
    
    def send(self, params):
        """Enviar mensaje LoRa"""
        if not params:
            console.print(friendly_error(
                "Falta el mensaje a enviar",
                "send <mensaje> [--power <valor>] [--frequency <valor>]"
            ))
            return
        
        parsed, message_parts = parse_message_with_options(
            params,
            {'--power': int, '--frequency': float}
        )
        power = parsed['--power']
        frequency = parsed['--frequency']
        
        message = ' '.join(message_parts)
        tx_power = power if power is not None else self.config.lora.power
        tx_freq = frequency if frequency is not None else self.config.lora.frequency
        
        # Mostrar información del mensaje
        table = styled_table("MENSAJE TX")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Mensaje", f'"{message}"')
        table.add_row("Frecuencia", f"{tx_freq} MHz")
        table.add_row("Potencia", f"{tx_power} dBm")
        table.add_row("Longitud", f"{len(message)} bytes")
        table.add_row("Factor de dispersión", str(self.config.lora.spreading_factor))
        table.add_row("Ancho de banda", f"{self.config.lora.bandwidth} kHz")
        
        console.print(table)
        console.print()
        console.print(friendly_error(
            "Hardware LoRa no conectado",
            "Compila el core Rust con: uvx maturin develop"
        ))
    
    def listen(self, params):
        """Escuchar mensajes LoRa"""
        timeout = 30
        parsed = parse_options(params, {'--timeout': int, '--channel': int})
        if parsed['--timeout'] is not None:
            timeout = parsed['--timeout']
        
        client = self.config.get_mqtt_client()
        if client and client.is_connected():
            self._listen_mqtt(client, timeout)
        else:
            console.print(friendly_error(
                "Cliente MQTT no disponible",
                "Compila el core Rust con: uvx maturin develop"
            ))
    
    def _listen_mqtt(self, client, timeout):
        """Escuchar usando cliente MQTT"""
        console.print(f"[cyan]>> Escuchando mensajes MQTT por {timeout} segundos...[/cyan]")
        console.print("[dim]Presiona Ctrl+C para detener[/dim]")
        
        try:
            start_time = time.time()
            message_count = 0
            recent_keys = deque(maxlen=max(100, int(getattr(self.config.ui, 'max_messages', 1000))))
            recent_key_set = set()
            poll_interval = max(0.1, float(getattr(self.config.ui, 'refresh_rate', 1.0)))
            
            while time.time() - start_time < timeout:
                time.sleep(poll_interval)
                messages = client.get_messages(5)  # Últimos 5 mensajes
                
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

                    timestamp = format_timestamp(msg.get('timestamp'))
                    console.print(f"[green][<<] [{timestamp}] {msg['topic']}: {msg['payload']}[/green]")
                    message_count += 1
        
        except KeyboardInterrupt:
            console.print(f"\n{ICON['warn']} Escucha detenida. {message_count} mensajes MQTT recibidos")
        else:
            console.print(f"{ICON['info']} Tiempo de escucha completado ({message_count} mensajes MQTT recibidos)")

        # Resumen de sesión
        elapsed = int(time.time() - start_time)
        console.print(styled_panel_compact(
            f"  Duración: {format_duration(elapsed)}  ·  Mensajes: {message_count}  ·  "
            f"Tasa promedio: {message_count / max(1, elapsed):.2f} msg/s",
            title="RESUMEN ESCUCHA MQTT",
        ))
    
    def status(self, params):
        """Estado del módulo LoRa"""
        table = styled_table("ESTADO MODULO LORA")
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="green")
        
        config = self.config.lora
        
        table.add_row("Frecuencia", f"{config.frequency} MHz")
        table.add_row("Potencia", f"{config.power} dBm")
        table.add_row("Ancho de banda", f"{config.bandwidth} kHz")
        table.add_row("Factor dispersión", f"SF{config.spreading_factor}")
        table.add_row("Codificación", config.coding_rate)
        
        client = self.config.get_mqtt_client()
        if client and client.is_connected():
            table.add_row("Conexión MQTT", f"{ICON['ok']} Conectado")
        else:
            table.add_row("Conexión MQTT", f"{ICON['warn']} Sin conexión")
        
        console.print(table)