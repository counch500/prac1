import unittest
from unittest.mock import MagicMock, patch
from mood.client.__main__ import Client_MUD

class TestClientCommandTransformations(unittest.TestCase):

    @patch('threading.Thread')  # Мокаем поток
    @patch('socket.socket')     # Мокаем сокет
    def setUp(self, mock_socket_class, mock_thread_class):
        self.mock_socket = MagicMock()
        mock_socket_class.return_value = self.mock_socket
        self.mock_socket.recv.return_value = b"Welcome to MUD!\n"

        # Отключаем настоящий поток
        mock_thread_instance = MagicMock()
        mock_thread_class.return_value = mock_thread_instance

        self.client = Client_MUD("TestPlayer")
        self.client.s = self.mock_socket

    def test_attack_command_sword(self):
        self.mock_socket.sendall.reset_mock()
        self.client.onecmd('attack tux with sword')
        self.mock_socket.sendall.assert_called_with(b"attack sword tux\n")

    def test_attack_command_axe(self):
        self.mock_socket.sendall.reset_mock()
        self.client.onecmd('attack tux with axe')
        self.mock_socket.sendall.assert_called_with(b"attack axe tux\n")

    def test_attack_command_invalid_weapon(self):
        self.mock_socket.sendall.reset_mock()
        self.client.onecmd('attack tux with banana')
        self.mock_socket.sendall.assert_not_called()

    def test_addmon_command_valid1(self):
        self.mock_socket.sendall.reset_mock()
        self.client.onecmd('addmon tux coords 0 1 hp 30 hello Hello')
        self.mock_socket.sendall.assert_called_with(b"addmon tux 0 1 30 Hello\n")

    def test_addmon_command_valid2(self):
        self.mock_socket.sendall.reset_mock()
        self.client.onecmd('addmon tux coords 2 2 hp 40 hello Hi')
        self.mock_socket.sendall.assert_called_with(b"addmon tux 2 2 40 Hi\n")

    def test_addmon_command_invalid(self):
        self.mock_socket.sendall.reset_mock()
        self.client.onecmd('addmon tux coords 10 10 hp -5 hello Oops')
        self.mock_socket.sendall.assert_not_called()

if __name__ == '__main__':
    unittest.main()

