import unittest
import multiprocessing
import socket
import time
from mood.server import __main__ as server


class TestMudServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = multiprocessing.Process(target=server.serve)
        cls.proc.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.join()

    def setUp(self):
        self.s = socket.create_connection(("localhost", 1337))
        self.s.sendall(b"TestPlayer\n")
        self.s.recv(4096)

    def tearDown(self):
        self.s.close()

    def send_and_receive(self, message, timeout=0.5):
        self.s.sendall((message + "\n").encode())
        self.s.settimeout(timeout)
        result = []
        try:
            while True:
                chunk = self.s.recv(4096)
                if not chunk:
                    break
                result.append(chunk.decode())
        except socket.timeout:
            pass
        self.s.settimeout(None)
        return ''.join(result).strip()

    def test_add_monster(self):
        res = self.send_and_receive('addmon tux 0 1 100 Hello')
        self.assertIn('added monster tux', res)

    def test_encounter_monster(self):
        self.send_and_receive('addmon tux 1 1 100 fdhello')
        self.send_and_receive('move 1 0')
        res = self.send_and_receive('move 0 1')
        self.assertIn('fdhello', res)
        self.assertIn('o_o', res)

    def test_attack_monster(self):
        self.send_and_receive('addmon dragon 0 1 25 Hello')
        self.send_and_receive('move 0 1')
        res = self.send_and_receive('attack axe dragon')
        self.assertIn('attacked dragon', res.lower())

