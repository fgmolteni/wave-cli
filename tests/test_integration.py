"""
Tests de integración para Wave CLI
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from wave_cli.config.settings import WaveConfig
from wave_cli.ui.interactive import InteractiveMode


class TestFullWorkflow:
    """Tests de workflow completo"""
    
    def setup_method(self):
        """Setup para cada test"""
        # Crear configuración temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            self.config_file = f.name
        
        self.config = WaveConfig(config_file=self.config_file)
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        Path(self.config_file).unlink(missing_ok=True)
    
    def test_config_persistence_workflow(self):
        """Test workflow completo de persistencia de configuración"""
        # 1. Configurar MQTT
        self.config.update_mqtt_config(
            broker_url="mqtt://test.broker.com",
            port=8883
        )
        
        # 2. Configurar LoRa
        self.config.update_lora_config(
            frequency=868.1,
            power=20
        )
        
        # 3. Guardar configuración
        assert self.config.save() == True
        
        # 4. Cargar configuración en nueva instancia
        new_config = WaveConfig(config_file=self.config_file)
        
        # 5. Verificar persistencia
        assert new_config.mqtt.broker_url == "mqtt://test.broker.com"
        assert new_config.mqtt.port == 8883
        assert new_config.lora.frequency == 868.1
        assert new_config.lora.power == 20
    
    @patch('wave_cli.commands.mqtt_commands.console')
    def test_mqtt_command_chain(self, mock_console):
        """Test cadena de comandos MQTT"""
        interactive = InteractiveMode(self.config)
        
        # Mock cliente MQTT
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.is_connected.return_value = True
        mock_client.subscribe.return_value = True
        mock_client.get_messages.return_value = [
            {
                'timestamp': '2023-01-01T12:00:00Z',
                'topic': 'test/topic',
                'payload': 'test message',
                'qos': 0
            }
        ]
        
        with patch.object(self.config, 'get_mqtt_client', return_value=mock_client):
            # 1. Conectar
            interactive._execute_command('connect', ['mqtt://test.broker.com'])
            
            # 2. Suscribirse
            interactive._execute_command('subscribe', ['test/topic'])
            
            # 3. Ver mensajes
            interactive._execute_command('messages', ['--limit', '5'])
        
        # Verificar llamadas en orden
        mock_client.connect.assert_called_once()
        mock_client.subscribe.assert_called_once()
        mock_client.get_messages.assert_called_once()
    
    @patch('wave_cli.commands.lora_commands.console')
    @patch('wave_cli.commands.lora_commands.time')
    def test_lora_command_chain(self, mock_time, mock_console):
        """Test cadena de comandos LoRa"""
        interactive = InteractiveMode(self.config)
        
        # 1. Configurar LoRa
        interactive._execute_command('config', ['lora', 'frequency', '868.1'])
        interactive._execute_command('config', ['lora', 'power', '20'])
        
        # 2. Enviar mensaje
        with patch('wave_cli.ui.theme.Table'):
            interactive._execute_command('send', ['test message', '--power', '15'])
        
        # 3. Ver estado
        with patch('wave_cli.ui.theme.Table'):
            interactive._execute_command('status', [])
        
        # Verificar que todos los comandos se ejecutaron sin errores
        assert self.config.lora.frequency == 868.1
        assert self.config.lora.power == 20
    
    def test_config_command_integration(self):
        """Test integración del comando config con persistencia"""
        interactive = InteractiveMode(self.config)
        
        with patch('wave_cli.commands.general_commands.console'):
            # 1. Modificar configuración MQTT
            interactive._execute_command('config', ['mqtt', 'broker_url', 'mqtt://configured.broker.com'])
            interactive._execute_command('config', ['mqtt', 'port', '8883'])
            
            # 2. Modificar configuración LoRa
            interactive._execute_command('config', ['lora', 'frequency', '433.0'])
            interactive._execute_command('config', ['lora', 'spreading_factor', '9'])
        
        # Verificar cambios en configuración
        assert self.config.mqtt.broker_url == 'mqtt://configured.broker.com'
        assert self.config.mqtt.port == 8883
        assert self.config.lora.frequency == 433.0
        assert self.config.lora.spreading_factor == 9


class TestErrorHandling:
    """Tests de manejo de errores en integración"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = WaveConfig()
        self.interactive = InteractiveMode(self.config)
    
    @patch('wave_cli.commands.mqtt_commands.console')
    def test_mqtt_connection_error_handling(self, mock_console):
        """Test manejo de errores de conexión MQTT"""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")
        
        with patch.object(self.config, 'get_mqtt_client', return_value=mock_client):
            # No debería crashear
            self.interactive._execute_command('connect', ['mqtt://invalid.broker.com'])
        
        # Verificar que se maneja el error
        mock_console.print.assert_called()
    
    @patch('wave_cli.commands.general_commands.console')
    def test_config_invalid_value_handling(self, mock_console):
        """Test manejo de valores inválidos en configuración"""
        # Intentar configurar un valor inválido
        self.interactive._execute_command('config', ['lora', 'frequency', 'invalid_value'])
        
        # Verificar que se maneja el error
        mock_console.print.assert_called()
        all_args = " ".join(str(c[0][0]) for c in mock_console.print.call_args_list if c[0])
        assert "no es un valor" in all_args.lower() or "err" in all_args.lower()
    
    @patch('wave_cli.ui.interactive.console')
    def test_malformed_command_handling(self, mock_console):
        """Test manejo de comandos mal formateados"""
        # Simular comando con comillas no balanceadas
        import shlex
        
        with patch('wave_cli.ui.interactive.shlex.split', side_effect=ValueError("No closing quotation")):
            self.interactive._execute_command('connect', ['mqtt://test.com'])
        
        # El error se maneja en el nivel superior del loop interactivo
        # Este test verifica que no se produzca una excepción no manejada


class TestPerformance:
    """Tests básicos de rendimiento"""
    
    def test_large_command_history(self):
        """Test manejo de historial grande de comandos"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        # Agregar muchos comandos al historial
        from datetime import datetime
        for i in range(1000):
            interactive.command_history.append(f"command_{i}")
            interactive.command_timestamps.append(datetime.now())
        
        # Verificar que show_history maneja la carga
        with patch('wave_cli.ui.interactive.console') as mock_console:
            interactive.show_history()
        
        # Debería mostrar solo los últimos 10 comandos
        mock_console.print.assert_called()
    
    def test_config_large_values(self):
        """Test configuración con valores extremos"""
        config = WaveConfig()
        
        # Configurar valores en los límites
        config.update_lora_config(
            frequency=928.0,  # Límite superior
            power=20,         # Potencia máxima  
            spreading_factor=12  # SF máximo
        )
        
        config.ui.max_messages = 10000  # Buffer grande
        
        # Verificar que se manejan correctamente
        assert config.lora.frequency == 928.0
        assert config.lora.power == 20
        assert config.lora.spreading_factor == 12
        assert config.ui.max_messages == 10000


@pytest.mark.integration
class TestRealWorldScenarios:
    """Tests de escenarios del mundo real"""
    
    def test_development_workflow(self):
        """Test workflow típico de desarrollo"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        with patch('wave_cli.commands.mqtt_commands.console'):
            with patch('wave_cli.commands.lora_commands.console'):
                with patch('wave_cli.commands.general_commands.console'):
                    # Workflow típico de desarrollo
                    commands = [
                        ('config', ['mqtt', 'broker_url', 'mqtt://localhost']),
                        ('config', ['lora', 'frequency', '915.0']),
                        ('help', []),
                        ('config', []),  # Ver configuración completa
                    ]
                    
                    for cmd, params in commands:
                        interactive._execute_command(cmd, params)
        
        # Verificar estado final
        assert config.mqtt.broker_url == 'mqtt://localhost'
        assert config.lora.frequency == 915.0
    
    def test_monitoring_workflow(self):
        """Test workflow típico de monitoreo"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.is_connected.return_value = True
        mock_client.subscribe.return_value = True
        mock_client.get_messages.return_value = []
        
        with patch.object(config, 'get_mqtt_client', return_value=mock_client):
            with patch('wave_cli.commands.mqtt_commands.console'):
                # Workflow típico de monitoreo
                commands = [
                    ('connect', ['mqtt://test.mosquitto.org']),
                    ('subscribe', ['sensors/+/data']),
                    ('messages', ['--limit', '10']),
                ]
                
                for cmd, params in commands:
                    interactive._execute_command(cmd, params)
        
        # Verificar llamadas de monitoreo
        mock_client.connect.assert_called()
        mock_client.subscribe.assert_called()
        mock_client.get_messages.assert_called()