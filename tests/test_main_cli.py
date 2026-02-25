"""
Tests para comandos no interactivos de main.py
"""

from unittest.mock import patch

from click.testing import CliRunner

from wave_cli.main import cli


class TestMainCliNamespaces:
    """Valida namespaces mqtt/lora en modo no interactivo"""

    def setup_method(self):
        self.runner = CliRunner()

    @patch('wave_cli.main.MqttCommands.connect')
    def test_mqtt_connect_command(self, mock_connect):
        result = self.runner.invoke(cli, ['mqtt', 'connect', 'broker.emqx.io', '--port', '1883'])
        assert result.exit_code == 0
        mock_connect.assert_called_once_with(['broker.emqx.io', '--port', '1883'])

    @patch('wave_cli.main.MqttCommands.messages')
    def test_mqtt_messages_command(self, mock_messages):
        result = self.runner.invoke(cli, ['mqtt', 'messages', '--limit', '5', '--device', 'node01'])
        assert result.exit_code == 0
        mock_messages.assert_called_once_with(['--limit', '5', '--device', 'node01'])

    @patch('wave_cli.main.LoRaCommands.listen')
    def test_lora_listen_command(self, mock_listen):
        result = self.runner.invoke(cli, ['lora', 'listen', '--timeout', '10', '--channel', '5'])
        assert result.exit_code == 0
        mock_listen.assert_called_once_with(['--timeout', '10', '--channel', '5'])

    @patch('wave_cli.main.LoRaCommands.send')
    def test_lora_send_command(self, mock_send):
        result = self.runner.invoke(cli, ['lora', 'send', 'hola', '--power', '20', '--frequency', '915.5'])
        assert result.exit_code == 0
        mock_send.assert_called_once_with(['hola', '--power', '20', '--frequency', '915.5'])
