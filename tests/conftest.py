"""
Configuración de pytest para Wave CLI
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from wave_cli.config.settings import WaveConfig


@pytest.fixture
def temp_config_file():
    """Fixture que proporciona un archivo de configuración temporal"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_file = f.name
    
    yield config_file
    
    # Cleanup
    Path(config_file).unlink(missing_ok=True)


@pytest.fixture
def wave_config(temp_config_file):
    """Fixture que proporciona una instancia de WaveConfig con archivo temporal"""
    return WaveConfig(config_file=temp_config_file)


@pytest.fixture
def mock_mqtt_client():
    """Fixture que proporciona un cliente MQTT mock"""
    client = Mock()
    client.connect.return_value = True
    client.is_connected.return_value = True
    client.subscribe.return_value = True
    client.start_listening.return_value = None
    client.disconnect.return_value = None
    client.get_messages.return_value = []
    return client


@pytest.fixture
def sample_mqtt_messages():
    """Fixture que proporciona mensajes MQTT de ejemplo"""
    return [
        {
            'timestamp': '2023-01-01T12:00:00Z',
            'topic': 'sensors/temperature/room1',
            'payload': '{"value": 23.5, "unit": "C"}',
            'qos': 0
        },
        {
            'timestamp': '2023-01-01T12:01:00Z',
            'topic': 'sensors/humidity/room1', 
            'payload': '{"value": 65.0, "unit": "%"}',
            'qos': 0
        },
        {
            'timestamp': '2023-01-01T12:02:00Z',
            'topic': 'devices/gateway001/status',
            'payload': '{"status": "online", "rssi": -75}',
            'qos': 1
        }
    ]


@pytest.fixture
def configured_wave_config(temp_config_file):
    """Fixture que proporciona una WaveConfig preconfigurada"""
    config = WaveConfig(config_file=temp_config_file)
    
    # Configurar MQTT
    config.update_mqtt_config(
        broker_url="mqtt://test.mosquitto.org",
        port=1883,
        keep_alive=30
    )
    
    # Configurar LoRa
    config.update_lora_config(
        frequency=915.0,
        power=14,
        bandwidth=125,
        spreading_factor=7
    )
    
    return config


# Marcadores personalizados para pytest
def pytest_configure(config):
    """Configurar marcadores personalizados"""
    config.addinivalue_line(
        "markers", "slow: marca tests como lentos (deseleccionar con '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests como tests de integración"
    )
    config.addinivalue_line(
        "markers", "mqtt: marca tests que requieren broker MQTT"
    )


# Fixtures de scope de sesión para optimizar tests
@pytest.fixture(scope="session")
def session_config():
    """Configuración que persiste durante toda la sesión de tests"""
    return {
        'test_broker': 'mqtt://test.mosquitto.org',
        'test_port': 1883,
        'test_topics': ['test/wave-cli/+', 'sensors/+/data']
    }


# Hook para manejo de warnings
def pytest_runtest_setup(item):
    """Setup que se ejecuta antes de cada test"""
    # Configurar warnings específicos si es necesario
    pass


def pytest_runtest_teardown(item, nextitem):
    """Teardown que se ejecuta después de cada test"""
    # Cleanup específico si es necesario
    pass