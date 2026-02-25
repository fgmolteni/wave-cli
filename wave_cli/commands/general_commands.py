"""
Comandos generales para Wave CLI
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from ..ui.theme import styled_table, styled_panel, styled_panel_compact, PANEL_KWARGS, ICON, COLORS, section_rule, friendly_error

console = Console()


class GeneralCommands:
    """Implementación de comandos generales"""
    
    def __init__(self, config):
        self.wave_config = config
    
    def config(self, params):
        """Ver/modificar configuración"""
        if len(params) == 0:
            # Mostrar toda la configuración
            self._show_full_config()
        elif len(params) == 1:
            # Mostrar sección específica
            section = params[0].lower()
            if section in ['mqtt', 'lora', 'ui']:
                self._show_config_section(section)
            else:
                console.print(friendly_error(
                    f"Sección desconocida: {section}",
                    "Secciones: mqtt, lora, ui"
                ))
        elif len(params) == 3:
            # Modificar configuración: config <seccion> <parametro> <valor>
            section = params[0].lower()
            parameter = params[1].lower()
            value = params[2]
            self._update_config(section, parameter, value)
        else:
            console.print("[yellow]Uso:[/yellow]")
            console.print("[yellow]  config                    - Ver toda la configuración[/yellow]")
            console.print("[yellow]  config <seccion>          - Ver sección específica[/yellow]")
            console.print("[yellow]  config <seccion> <param> <valor> - Modificar parámetro[/yellow]")
    
    def _show_full_config(self):
        """Muestra toda la configuración"""
        # Configuración MQTT
        mqtt_table = styled_table("CONFIGURACION MQTT")
        mqtt_table.add_column("Parámetro", style="cyan")
        mqtt_table.add_column("Valor", style="green")
        
        mqtt_config = self.wave_config.mqtt
        mqtt_table.add_row("Broker URL", mqtt_config.broker_url or "No configurado")
        mqtt_table.add_row("Puerto", str(mqtt_config.port))
        mqtt_table.add_row("Keep Alive", f"{mqtt_config.keep_alive}s")
        mqtt_table.add_row("Timeout", f"{mqtt_config.timeout}s")
        
        # Configuración LoRa
        lora_table = styled_table("CONFIGURACION LORA")
        lora_table.add_column("Parámetro", style="cyan")
        lora_table.add_column("Valor", style="green")
        lora_table.add_column("Descripción", style="dim")
        
        lora_config = self.wave_config.lora
        lora_table.add_row("Frecuencia", f"{lora_config.frequency} MHz", "Frecuencia de operación")
        lora_table.add_row("Potencia", f"{lora_config.power} dBm", "Potencia de transmisión")
        lora_table.add_row("Ancho de banda", f"{lora_config.bandwidth} kHz", "Ancho de banda")
        lora_table.add_row("Factor dispersión", str(lora_config.spreading_factor), "Factor de dispersión")
        lora_table.add_row("Codificación", lora_config.coding_rate, "Tasa de codificación")
        
        # Configuración UI
        ui_table = styled_table("CONFIGURACION INTERFAZ")
        ui_table.add_column("Parámetro", style="cyan")
        ui_table.add_column("Valor", style="green")
        
        ui_config = self.wave_config.ui
        ui_table.add_row("Max mensajes", str(ui_config.max_messages))
        ui_table.add_row("Tasa de refresco", f"{ui_config.refresh_rate}s")
        ui_table.add_row("Mostrar timestamps", "Sí" if ui_config.show_timestamps else "No")
        ui_table.add_row("Tema de colores", ui_config.color_theme)
        
        console.print(mqtt_table)
        console.print()
        console.print(section_rule())
        console.print()

        # Layout side-by-side para LoRa y UI si el terminal es ancho
        term_width = console.size.width
        if term_width >= 120:
            console.print(Columns([lora_table, ui_table], expand=True, equal=True))
        else:
            console.print(lora_table)
            console.print()
            console.print(section_rule())
            console.print()
            console.print(ui_table)
        
        # Información del archivo de configuración
        info_panel = styled_panel(
            f"[dim]Archivo de configuración: {self.wave_config.config_file}[/dim]",
            title="INFORMACION",
        )
        console.print(info_panel)
    
    def _show_config_section(self, section):
        """Muestra una sección específica de configuración"""
        if section == 'mqtt':
            config_obj = self.wave_config.mqtt
            title = "CONFIGURACION MQTT"
        elif section == 'lora':
            config_obj = self.wave_config.lora
            title = "CONFIGURACION LORA"
        elif section == 'ui':
            config_obj = self.wave_config.ui
            title = "CONFIGURACION INTERFAZ"
        else:
            return
        
        table = styled_table(title)
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor", style="green")
        
        # Obtener todos los atributos del objeto de configuración
        for attr_name in dir(config_obj):
            if not attr_name.startswith('_'):
                attr_value = getattr(config_obj, attr_name)
                if not callable(attr_value):
                    # Formatear valor para display
                    if isinstance(attr_value, str):
                        display_value = attr_value or "No configurado"
                    elif isinstance(attr_value, bool):
                        display_value = "Sí" if attr_value else "No"
                    else:
                        display_value = str(attr_value)
                    
                    table.add_row(attr_name.replace('_', ' ').title(), display_value)
        
        console.print(table)
    
    def _update_config(self, section, parameter, value):
        """Actualiza un parámetro de configuración"""
        try:
            if section == 'mqtt':
                config_obj = self.wave_config.mqtt
                update_func = self.wave_config.update_mqtt_config
            elif section == 'lora':
                config_obj = self.wave_config.lora
                update_func = self.wave_config.update_lora_config
            elif section == 'ui':
                config_obj = self.wave_config.ui
                update_func = lambda **kwargs: setattr(config_obj, list(kwargs.keys())[0], list(kwargs.values())[0])
            else:
                console.print(friendly_error(
                    f"Sección desconocida: {section}",
                    "Secciones: mqtt, lora, ui"
                ))
                return
            
            # Verificar que el parámetro existe
            if not hasattr(config_obj, parameter):
                available_params = [attr for attr in dir(config_obj) 
                                 if not attr.startswith('_') and not callable(getattr(config_obj, attr))]
                console.print(friendly_error(
                    f"Parámetro desconocido: {parameter}",
                    f"Disponibles: {', '.join(available_params)}"
                ))
                return
            
            # Obtener el tipo actual del parámetro
            current_value = getattr(config_obj, parameter)
            
            # Convertir el valor al tipo correcto
            if isinstance(current_value, int):
                converted_value = int(value)
            elif isinstance(current_value, float):
                converted_value = float(value)
            elif isinstance(current_value, bool):
                converted_value = value.lower() in ['true', '1', 'yes', 'on']
            else:
                converted_value = str(value)
            
            # Actualizar configuración
            if section in ['mqtt', 'lora']:
                update_func(**{parameter: converted_value})
            else:
                old_value = getattr(config_obj, parameter)
                setattr(config_obj, parameter, converted_value)
                console.print(styled_panel_compact(
                    f"  [dim]{section}.{parameter}[/dim]\n"
                    f"  [red]{old_value}[/red] [bold white]→[/bold white] [green]{converted_value}[/green]",
                    title="CONFIGURACION ACTUALIZADA",
                ))
            
            # Guardar configuración
            if self.wave_config.save():
                console.print(f"{ICON['ok']} Configuración guardada")
            
        except ValueError as e:
            console.print(friendly_error(
                f"'{value}' no es un valor válido para {parameter}",
                f"Requiere tipo: {type(getattr(config_obj, parameter)).__name__}"
            ))
        except Exception as e:
            console.print(friendly_error(f"Error actualizando configuración: {e}"))