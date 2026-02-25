"""
Tests para el sistema de configuración
"""

import json
import tempfile
from pathlib import Path
import pytest

from wave_cli.config.settings import WaveConfig, MqttConfig, LoRaConfig, UIConfig


class TestWaveConfig:
    """Tests para WaveConfig"""
    
    def test_default_initialization(self):
        """Test inicialización con valores por defecto"""
        config = WaveConfig()
        
        assert config.mqtt.port == 1883
        assert config.lora.frequency == 915.0
        assert config.ui.max_messages == 1000
    
    def test_custom_config_file(self):
        """Test inicialización con archivo personalizado"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "mqtt": {"broker_url": "mqtt://test.broker.com", "port": 8883},
                "lora": {"frequency": 868.1, "power": 20},
                "ui": {"max_messages": 2000}
            }
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = WaveConfig(config_file=config_file)
            
            assert config.mqtt.broker_url == "mqtt://test.broker.com"
            assert config.mqtt.port == 8883
            assert config.lora.frequency == 868.1
            assert config.lora.power == 20
            assert config.ui.max_messages == 2000
        finally:
            Path(config_file).unlink()
    
    def test_save_and_load_config(self):
        """Test guardado y carga de configuración"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            # Crear y modificar configuración
            config = WaveConfig(config_file=config_file)
            config.mqtt.broker_url = "mqtt://saved.broker.com"
            config.lora.frequency = 433.0
            config.ui.max_messages = 500
            
            # Guardar
            assert config.save() == True
            
            # Cargar en nueva instancia
            new_config = WaveConfig(config_file=config_file)
            
            assert new_config.mqtt.broker_url == "mqtt://saved.broker.com"
            assert new_config.lora.frequency == 433.0
            assert new_config.ui.max_messages == 500
        finally:
            Path(config_file).unlink(missing_ok=True)
    
    def test_update_mqtt_config(self):
        """Test actualización de configuración MQTT"""
        config = WaveConfig()
        
        config.update_mqtt_config(
            broker_url="mqtt://updated.broker.com",
            port=1884,
            keep_alive=60
        )
        
        assert config.mqtt.broker_url == "mqtt://updated.broker.com"
        assert config.mqtt.port == 1884
        assert config.mqtt.keep_alive == 60
    
    def test_update_lora_config(self):
        """Test actualización de configuración LoRa"""
        config = WaveConfig()
        
        config.update_lora_config(
            frequency=868.1,
            power=15,
            spreading_factor=9
        )
        
        assert config.lora.frequency == 868.1
        assert config.lora.power == 15
        assert config.lora.spreading_factor == 9
    
    def test_get_config_summary(self):
        """Test obtención de resumen de configuración"""
        config = WaveConfig()
        summary = config.get_config_summary()
        
        assert "mqtt" in summary
        assert "lora" in summary
        assert "ui" in summary
        assert "config_file" in summary
        
        # Verificar estructura
        assert isinstance(summary["mqtt"], dict)
        assert "broker_url" in summary["mqtt"]
        assert "port" in summary["mqtt"]


class TestMqttConfig:
    """Tests para MqttConfig"""
    
    def test_default_values(self):
        """Test valores por defecto"""
        config = MqttConfig()
        
        assert config.broker_url == ""
        assert config.port == 1883
        assert config.username is None
        assert config.password is None
        assert config.keep_alive == 30
        assert config.timeout == 10
    
    def test_custom_values(self):
        """Test valores personalizados"""
        config = MqttConfig(
            broker_url="mqtt://custom.broker.com",
            port=8883,
            username="user",
            password="pass",
            keep_alive=45,
            timeout=15
        )
        
        assert config.broker_url == "mqtt://custom.broker.com"
        assert config.port == 8883
        assert config.username == "user"
        assert config.password == "pass"
        assert config.keep_alive == 45
        assert config.timeout == 15


class TestLoRaConfig:
    """Tests para LoRaConfig"""
    
    def test_default_values(self):
        """Test valores por defecto"""
        config = LoRaConfig()
        
        assert config.frequency == 915.0
        assert config.power == 14
        assert config.bandwidth == 125
        assert config.spreading_factor == 7
        assert config.coding_rate == "4/5"
    
    def test_custom_values(self):
        """Test valores personalizados"""
        config = LoRaConfig(
            frequency=868.1,
            power=20,
            bandwidth=250,
            spreading_factor=9,
            coding_rate="4/6"
        )
        
        assert config.frequency == 868.1
        assert config.power == 20
        assert config.bandwidth == 250
        assert config.spreading_factor == 9
        assert config.coding_rate == "4/6"


class TestUIConfig:
    """Tests para UIConfig"""
    
    def test_default_values(self):
        """Test valores por defecto"""
        config = UIConfig()
        
        assert config.max_messages == 1000
        assert config.refresh_rate == 1.0
        assert config.show_timestamps == True
        assert config.color_theme == "default"
    
    def test_custom_values(self):
        """Test valores personalizados"""
        config = UIConfig(
            max_messages=2000,
            refresh_rate=0.5,
            show_timestamps=False,
            color_theme="dark"
        )
        
        assert config.max_messages == 2000
        assert config.refresh_rate == 0.5
        assert config.show_timestamps == False
        assert config.color_theme == "dark"