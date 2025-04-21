import unittest
import socket
import multiprocessing
import time
import sqroo  # предполагается, что сервер лежит в sqroo.py

def sqrootnet(coeffs: str, s: socket.socket) -> str:
    s.sendall((coeffs + "\n").encode())
    return s.recv(128).decode().strip()

class TestSqrootServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = multiprocessing.Process(target=sqroo.serve)
        cls.proc.start()
        time.sleep(1)  # ожидание запуска сервера

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.join()

    def setUp(self):
        self.s = socket.create_connection(("127.0.0.1", 1337))

    def tearDown(self):
        self.s.close()

    def test_two_roots(self):
        result = sqrootnet("1 -3 2", self.s)
        self.assertEqual(set(result.split()), {"1.0", "2.0"})

    def test_one_root(self):
        result = sqrootnet("1 2 1", self.s)
        self.assertEqual(result, "-1.0")

    def test_no_roots(self):
        result = sqrootnet("1 0 1", self.s)
        self.assertEqual(result, "")

    def test_invalid_input(self):
        result = sqrootnet("0 2 1", self.s)
        self.assertEqual(result, "")

