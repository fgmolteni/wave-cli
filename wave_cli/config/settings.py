"""
Sistema de configuración para Wave CLI
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from rich.console import Console

console = Console()


@dataclass
class MqttConfig:
    """Configuración MQTT"""
    broker_url: str = ""
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    keep_alive: int = 30
    timeout: int = 10
    

@dataclass  
class LoRaConfig:
    """Configuración LoRa"""
    frequency: float = 915.0
    power: int = 14
    bandwidth: int = 125
    spreading_factor: int = 7
    coding_rate: str = "4/5"


@dataclass
class UIConfig:
    """Configuración de interfaz"""
    max_messages: int = 1000
    refresh_rate: float = 1.0
    show_timestamps: bool = True
    color_theme: str = "default"


class WaveConfig:
    """Gestor de configuración principal para Wave CLI"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.mqtt = MqttConfig()
        self.lora = LoRaConfig()
        self.ui = UIConfig()
        self._client = None
        
        self.load()
    
    def _get_default_config_path(self) -> str:
        """Obtiene la ruta por defecto del archivo de configuración"""
        config_dir = Path.home() / ".config" / "wave-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "config.json")
    
    def load(self) -> bool:
        """Carga la configuración desde archivo"""
        if not os.path.exists(self.config_file):
            console.print(f"[yellow][!!] Archivo de configuracion no encontrado: {self.config_file}[/yellow]")
            console.print("[yellow]Usando valores por defecto[/yellow]")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar cada sección
            if 'mqtt' in data:
                self.mqtt = MqttConfig(**data['mqtt'])
            
            if 'lora' in data:
                lora_data = data['lora'].copy()
                # Asegurar que frequency sea float
                if 'frequency' in lora_data:
                    lora_data['frequency'] = float(lora_data['frequency'])
                self.lora = LoRaConfig(**lora_data)
                
            if 'ui' in data:
                self.ui = UIConfig(**data['ui'])
            
            console.print(f"[green][OK] Configuracion cargada desde: {self.config_file}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red][ERR] Error cargando configuracion: {e}[/red]")
            return False
    
    def save(self) -> bool:
        """Guarda la configuración actual a archivo"""
        try:
            # Crear directorio si no existe
            config_dir = Path(self.config_file).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                'mqtt': asdict(self.mqtt),
                'lora': asdict(self.lora),
                'ui': asdict(self.ui)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green][OK] Configuracion guardada en: {self.config_file}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red][ERR] Error guardando configuracion: {e}[/red]")
            return False
    
    def get_mqtt_client(self):
        """Obtiene el cliente MQTT, creándolo si es necesario"""
        if self._client is None:
            try:
                import wave_core

                create_mqtt_client = getattr(wave_core, 'create_mqtt_client', None)

                if create_mqtt_client is None:
                    raise ImportError("create_mqtt_client no está disponible en wave_core")

                self._client = create_mqtt_client()
                
                # Nota: No llamamos a setup_logging() aquí ya que env_logger
                # puede inicializarse automáticamente y solo se debe inicializar una vez
                        
                console.print("[green][OK] Cliente MQTT inicializado[/green]")
            except ImportError:
                console.print("[yellow][!!] Modulo Rust no disponible, usando simulacion[/yellow]")
                self._client = None
        
        return self._client
    
    def update_mqtt_config(self, **kwargs):
        """Actualiza configuración MQTT"""
        for key, value in kwargs.items():
            if hasattr(self.mqtt, key):
                setattr(self.mqtt, key, value)
                console.print(f"[green][OK] MQTT {key} actualizado: {value}[/green]")
    
    def update_lora_config(self, **kwargs):
        """Actualiza configuración LoRa"""
        for key, value in kwargs.items():
            if hasattr(self.lora, key):
                old_value = getattr(self.lora, key)
                setattr(self.lora, key, value)
                console.print(f"[green][OK] LoRa {key} actualizado: {old_value} → {value}[/green]")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de la configuración actual"""
        return {
            'mqtt': asdict(self.mqtt),
            'lora': asdict(self.lora),
            'ui': asdict(self.ui),
            'config_file': self.config_file
        }