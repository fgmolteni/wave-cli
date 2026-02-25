"""
Tests para el modo interactivo
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from wave_cli.ui.interactive import InteractiveMode
from wave_cli.config.settings import WaveConfig


class TestInteractiveMode:
    """Tests para InteractiveMode"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = WaveConfig()
        self.interactive = InteractiveMode(self.config)
    
    def test_initialization(self):
        """Test inicialización del modo interactivo"""
        assert self.interactive.config == self.config
        assert self.interactive.command_history == []
        assert hasattr(self.interactive, 'mqtt_commands')
        assert hasattr(self.interactive, 'lora_commands')
        assert hasattr(self.interactive, 'general_commands')
    
    def test_command_mapping(self):
        """Test que todos los comandos están mapeados"""
        expected_commands = [
            'connect', 'monitor', 'messages', 'subscribe',  # MQTT
            'send', 'listen', 'status',                      # LoRa
            'config', 'help', 'history', 'clear',           # General
            'mqtt', 'lora'                                  # Namespaces
        ]
        
        for command in expected_commands:
            assert command in self.interactive.command_map
            assert callable(self.interactive.command_map[command])
    
    @patch('wave_cli.ui.interactive.console')
    def test_execute_valid_command(self, mock_console):
        """Test ejecución de comando válido"""
        with patch.object(self.interactive.mqtt_commands, 'connect') as mock_connect:
            self.interactive._execute_command('connect', ['mqtt://test.com'])
            mock_connect.assert_called_once_with(['mqtt://test.com'])
    
    @patch('wave_cli.ui.interactive.console')
    def test_execute_invalid_command(self, mock_console):
        """Test ejecución de comando inválido"""
        self.interactive._execute_command('invalid_command', [])
        
        # Verificar que se muestra error
        mock_console.print.assert_called()
        printed_messages = [str(call[0][0]) for call in mock_console.print.call_args_list if call[0]]
        assert any("Comando desconocido" in msg for msg in printed_messages)

    @patch('wave_cli.ui.interactive.console')
    def test_show_guide(self, mock_console):
        """Test comando guide muestra guía"""
        self.interactive.show_guide()
        mock_console.print.assert_called()
        printed_text = str(mock_console.print.call_args[0][0])
        assert "INICIO" in printed_text

    def test_normalize_command_alias(self):
        """Alias deben mapear a comando canónico"""
        assert self.interactive._normalize_command('conn') == 'connect'
        assert self.interactive._normalize_command('tx') == 'send'
        assert self.interactive._normalize_command('help') == 'help'

    @patch('wave_cli.ui.interactive.console')
    def test_execute_mqtt_namespace(self, mock_console):
        """Namespace mqtt debe enrutar subcomandos"""
        with patch.object(self.interactive, '_execute_command') as mock_execute:
            self.interactive._execute_mqtt_namespace(['connect', 'broker.emqx.io', '--port', '1883'])
            mock_execute.assert_called_once_with('connect', ['broker.emqx.io', '--port', '1883'])

    @patch('wave_cli.ui.interactive.console')
    def test_execute_lora_namespace(self, mock_console):
        """Namespace lora debe enrutar subcomandos"""
        with patch.object(self.interactive, '_execute_command') as mock_execute:
            self.interactive._execute_lora_namespace(['listen', '--timeout', '10'])
            mock_execute.assert_called_once_with('listen', ['--timeout', '10'])

    def test_suggest_commands_returns_matches(self):
        """Debe sugerir comandos similares para typo"""
        matches = self.interactive._suggest_commands('conect')
        assert 'connect' in matches
    
    @patch('wave_cli.ui.interactive.console')
    def test_execute_command_with_exception(self, mock_console):
        """Test ejecución de comando que lanza excepción"""
        with patch.object(self.interactive.mqtt_commands, 'connect', side_effect=Exception("Test error")):
            self.interactive._execute_command('connect', ['mqtt://test.com'])
        
        # Verificar que se captura y muestra el error
        mock_console.print.assert_called()
        args = mock_console.print.call_args[0][0]
        assert "Error" in args
    
    @patch('wave_cli.ui.interactive.console')
    def test_show_help(self, mock_console):
        """Test mostrar ayuda"""
        self.interactive.show_help()
    
        # Verificar que se muestra la ayuda
        mock_console.print.assert_called()
        printed_text = str(mock_console.print.call_args[0][0])
        assert "MQTT" in printed_text
    
    @patch('wave_cli.ui.interactive.console')
    def test_show_history_empty(self, mock_console):
        """Test mostrar historial vacío"""
        self.interactive.show_history()
        
        args = mock_console.print.call_args[0][0]
        assert "No hay comandos en el historial" in args
    
    @patch('wave_cli.ui.interactive.console')
    def test_show_history_with_commands(self, mock_console):
        """Test mostrar historial con comandos"""
        from datetime import datetime
        self.interactive.command_history = ['connect mqtt://test.com', 'status', 'help']
        self.interactive.command_timestamps = [datetime.now(), datetime.now(), datetime.now()]
        self.interactive.show_history()
    
        # Verificar que se muestran entradas del historial
        mock_console.print.assert_called()
        all_text = " ".join(str(c[0][0]) for c in mock_console.print.call_args_list if c[0])
        assert "connect" in all_text
    
    @patch('wave_cli.ui.interactive.console')
    def test_clear_screen(self, mock_console):
        """Test limpiar pantalla"""
        self.interactive.clear_screen()
        mock_console.clear.assert_called_once()


class TestInteractiveModeIntegration:
    """Tests de integración para el modo interactivo"""
    
    @patch('wave_cli.ui.interactive.Prompt')
    @patch('wave_cli.ui.interactive.console')
    def test_command_parsing(self, mock_console, mock_prompt):
        """Test parsing de comandos con parámetros"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        # Test comando simple
        with patch.object(interactive, '_execute_command') as mock_execute:
            # Simular input del usuario
            mock_prompt.ask.side_effect = ['help', 'exit']
            
            try:
                interactive.start()
            except (KeyboardInterrupt, EOFError):
                pass
            
            # Verificar que se parseó correctamente
            mock_execute.assert_called()
    
    @patch('wave_cli.ui.interactive.Prompt')
    @patch('wave_cli.ui.interactive.console')
    def test_command_with_parameters(self, mock_console, mock_prompt):
        """Test parsing de comando con parámetros complejos"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        with patch.object(interactive, '_execute_command') as mock_execute:
            # Comando con comillas y parámetros
            mock_prompt.ask.side_effect = ['connect "mqtt://test.com" --port 1883', 'exit']
            
            try:
                interactive.start()
            except (KeyboardInterrupt, EOFError):
                pass
            
            # Verificar que se parseó correctamente con shlex
            mock_execute.assert_called()
    
    def test_command_history_accumulation(self):
        """Test acumulación del historial de comandos"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        # Simular varios comandos
        test_commands = ['connect mqtt://test.com', 'status', 'help']
        
        for cmd in test_commands:
            interactive.command_history.append(cmd)
        
        assert len(interactive.command_history) == 3
        assert interactive.command_history == test_commands
    
    @pytest.mark.parametrize("command,expected_method", [
        ("connect", "connect"),
        ("monitor", "monitor"), 
        ("send", "send"),
        ("config", "config"),
        ("help", "show_help"),
    ])
    def test_command_routing(self, command, expected_method):
        """Test que los comandos se enrutan correctamente"""
        config = WaveConfig()
        interactive = InteractiveMode(config)
        
        assert command in interactive.command_map
        
        # Verificar que el comando mapea al método correcto
        mapped_function = interactive.command_map[command]
        if hasattr(interactive, expected_method) and callable(getattr(interactive, expected_method)):
            expected_function = getattr(interactive, expected_method)
            assert mapped_function == expected_function
        else:
            # Para comandos que están en submódulos
            assert callable(mapped_function)