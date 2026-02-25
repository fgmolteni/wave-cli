"""
Tests para los comandos del CLI
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from wave_cli.commands.mqtt_commands import MqttCommands
from wave_cli.commands.lora_commands import LoRaCommands
from wave_cli.commands.general_commands import GeneralCommands
from wave_cli.config.settings import WaveConfig


def _extract_printed_text(mock_console):
    """Extrae texto legible de todas las llamadas a console.print."""
    parts = []
    for call in mock_console.print.call_args_list:
        if call[0]:
            parts.append(str(call[0][0]))
    return " ".join(parts)


class TestMqttCommands:
    """Tests para comandos MQTT"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = WaveConfig()
        self.mqtt_commands = MqttCommands(self.config)
    
    @patch('wave_cli.commands.mqtt_commands.console')
    def test_connect_without_params(self, mock_console):
        """Test comando connect sin parámetros"""
        self.mqtt_commands.connect([])
        
        # Verificar que se muestra error
        mock_console.print.assert_called()
        all_text = _extract_printed_text(mock_console)
        assert "Falta la URL del broker" in all_text
    
    @patch('wave_cli.commands.mqtt_commands.console')
    def test_connect_no_client(self, mock_console):
        """Test comando connect sin cliente disponible"""
        with patch.object(self.config, 'get_mqtt_client', return_value=None):
            self.mqtt_commands.connect(["mqtt://test.broker.com"])
        
        # Verificar error de cliente no disponible
        mock_console.print.assert_called()
        all_text = _extract_printed_text(mock_console)
        assert "Cliente MQTT no disponible" in all_text
    
    @patch('wave_cli.commands.mqtt_commands.console')
    @patch('wave_cli.commands.mqtt_commands.Progress')
    def test_connect_success(self, mock_progress, mock_console):
        """Test comando connect exitoso"""
        # Mock del cliente MQTT
        mock_client = Mock()
        mock_client.connect.return_value = True
        
        with patch.object(self.config, 'get_mqtt_client', return_value=mock_client):
            self.mqtt_commands.connect(["mqtt://test.broker.com", "--port", "1883"])
        
        # Verificar llamadas
        mock_client.connect.assert_called_once_with("test.broker.com", 1883)
        mock_console.print.assert_called()
    
    @patch('wave_cli.commands.mqtt_commands.console')
    def test_messages_no_client(self, mock_console):
        """Test comando messages sin cliente"""
        with patch.object(self.config, 'get_mqtt_client', return_value=None):
            self.mqtt_commands.messages(["--limit", "10"])
        
        args = mock_console.print.call_args[0][0]
        all_text = _extract_printed_text(mock_console)
        assert "Cliente MQTT no disponible" in all_text
    
    @patch('wave_cli.commands.mqtt_commands.console')
    def test_messages_not_connected(self, mock_console):
        """Test comando messages sin conexión"""
        mock_client = Mock()
        mock_client.is_connected.return_value = False
        
        with patch.object(self.config, 'get_mqtt_client', return_value=mock_client):
            self.mqtt_commands.messages([])
        
        all_text = _extract_printed_text(mock_console)
        assert "Sin conexion al broker" in all_text
    
    @patch('wave_cli.commands.mqtt_commands.console')
    @patch('wave_cli.ui.theme.Table')
    def test_messages_success(self, mock_table, mock_console):
        """Test comando messages exitoso"""
        # Mock del cliente con mensajes
        mock_client = Mock()
        mock_client.is_connected.return_value = True
        mock_client.get_messages.return_value = [
            {
                'timestamp': '2023-01-01T12:00:00Z',
                'topic': 'test/topic',
                'payload': 'test message',
                'qos': 0
            }
        ]
        
        with patch.object(self.config, 'get_mqtt_client', return_value=mock_client):
            self.mqtt_commands.messages(["--limit", "5"])
        
        mock_client.get_messages.assert_called_once_with(5)
        mock_console.print.assert_called()

    def test_read_key_nonblocking_without_tty(self):
        """Debe retornar None cuando no hay TTY"""
        with patch('wave_cli.commands.mqtt_commands.sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            assert self.mqtt_commands._read_key_nonblocking() is None

    def test_raw_stdin_context_without_tty(self):
        """El contexto raw debe degradar de forma segura sin TTY"""
        with patch('wave_cli.commands.mqtt_commands.sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            with self.mqtt_commands._raw_stdin_if_tty() as enabled:
                assert enabled is False


class TestLoRaCommands:
    """Tests para comandos LoRa"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = WaveConfig()
        self.lora_commands = LoRaCommands(self.config)
    
    @patch('wave_cli.commands.lora_commands.console')
    def test_send_without_params(self, mock_console):
        """Test comando send sin parámetros"""
        self.lora_commands.send([])
        
        all_text = _extract_printed_text(mock_console)
        assert "Falta el mensaje a enviar" in all_text
    
    @patch('wave_cli.commands.lora_commands.console')
    @patch('wave_cli.commands.lora_commands.Progress')
    @patch('wave_cli.commands.lora_commands.time')
    def test_send_success(self, mock_time, mock_progress, mock_console):
        """Test comando send exitoso"""
        with patch('wave_cli.ui.theme.Table') as mock_table:
            self.lora_commands.send(["test", "message", "--power", "20"])
        
        # Verificar que se muestra la tabla de información
        mock_table.assert_called()
        mock_console.print.assert_called()
    
    @patch('wave_cli.commands.lora_commands.console')
    def test_listen_with_mqtt_client(self, mock_console):
        """Test comando listen con cliente MQTT disponible"""
        mock_client = Mock()
        mock_client.is_connected.return_value = True
        
        with patch.object(self.config, 'get_mqtt_client', return_value=mock_client):
            with patch.object(self.lora_commands, '_listen_mqtt') as mock_listen_mqtt:
                self.lora_commands.listen(["--timeout", "30"])
                
                mock_listen_mqtt.assert_called_once_with(mock_client, 30)
    
    @patch('wave_cli.commands.lora_commands.console')
    def test_status_shows_config(self, mock_console):
        """Test comando status muestra configuración real"""
        with patch('wave_cli.ui.theme.Table') as mock_table:
            self.lora_commands.status([])
        
        # Verificar que se muestra la tabla de estado
        mock_table.assert_called()
        mock_console.print.assert_called()


class TestGeneralCommands:
    """Tests para comandos generales"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = WaveConfig()
        self.general_commands = GeneralCommands(self.config)
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_show_all(self, mock_console):
        """Test comando config mostrar toda la configuración"""
        with patch.object(self.general_commands, '_show_full_config') as mock_show_full:
            self.general_commands.config([])
            mock_show_full.assert_called_once()
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_show_section(self, mock_console):
        """Test comando config mostrar sección específica"""
        with patch.object(self.general_commands, '_show_config_section') as mock_show_section:
            self.general_commands.config(["mqtt"])
            mock_show_section.assert_called_once_with("mqtt")
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_unknown_section(self, mock_console):
        """Test comando config con sección desconocida"""
        self.general_commands.config(["unknown_section"])
        
        all_text = _extract_printed_text(mock_console)
        assert "Sección desconocida" in all_text
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_update_mqtt(self, mock_console):
        """Test actualización de configuración MQTT"""
        with patch.object(self.config, 'update_mqtt_config') as mock_update:
            with patch.object(self.config, 'save', return_value=True):
                self.general_commands.config(["mqtt", "port", "8883"])
            
            mock_update.assert_called_once_with(port=8883)
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_update_lora(self, mock_console):
        """Test actualización de configuración LoRa"""
        with patch.object(self.config, 'update_lora_config') as mock_update:
            with patch.object(self.config, 'save', return_value=True):
                self.general_commands.config(["lora", "frequency", "868.1"])
            
            mock_update.assert_called_once_with(frequency=868.1)
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_invalid_parameter(self, mock_console):
        """Test configuración con parámetro inválido"""
        self.general_commands.config(["mqtt", "invalid_param", "value"])
        
        all_text = _extract_printed_text(mock_console)
        assert "Parámetro desconocido" in all_text


# Tests de integración básica
class TestCommandsIntegration:
    """Tests de integración entre comandos y configuración"""
    
    def test_mqtt_config_persistence(self):
        """Test que cambios en comandos MQTT persisten en configuración"""
        config = WaveConfig()
        mqtt_commands = MqttCommands(config)
        
        # Simular actualización de configuración
        config.update_mqtt_config(broker_url="mqtt://test.broker.com", port=8883)
        
        assert config.mqtt.broker_url == "mqtt://test.broker.com"
        assert config.mqtt.port == 8883
    
    def test_lora_config_persistence(self):
        """Test que cambios en comandos LoRa persisten en configuración"""
        config = WaveConfig()
        lora_commands = LoRaCommands(config)
        
        # Simular actualización de configuración
        config.update_lora_config(frequency=868.1, power=20)
        
        assert config.lora.frequency == 868.1
        assert config.lora.power == 20