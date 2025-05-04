import unittest
import multiprocessing
import socket
import mood.client as client
import mood.server as srv
import time

tux = r'''Moved to (0, 1)
 ____
< hi >
 ----
   \
    \
        .--.
       |o_o |
       |:_/ |
      //   \ \
     (|     | )
    /'\_   _/`\
    \___)=(___/
'''

class TestSrv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = multiprocessing.Process(target=srv.run_server)
        cls.proc.start()
        time.sleep(1) 
    
    def setUp(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(('localhost', 1337))
        self.cmdline = client.Client_MUD(socket=self.s)

    def test_1(self):
        """Test addmon"""
        self.s.sendall("test1\n".encode())
        self.s.recv(1024).rstrip().decode()

        self.cmdline.do_addmon("tux coords 0 1 hello hi hp 10")
        response = self.s.recv(1024).rstrip().decode()
        self.assertEqual(response, "Added monster tux to (0, 1) saying hi")

    def test_2(self):
        """Test move and encount"""
        self.s.sendall("test2\n".encode())
        self.s.recv(1024).rstrip().decode()
        self.cmdline.do_addmon("tux coords 0 1 hello hi hp 10")
        self.s.recv(1024).rstrip().decode()
        self.cmdline.do_down("")
        response = self.s.recv(1024).rstrip().decode()
        response_lines = response.strip().splitlines()
        expected_lines = tux.strip().splitlines()
        self.assertEqual(len(response_lines), len(expected_lines))
        for resp_line, exp_line in zip(response_lines, expected_lines):
            self.assertEqual(resp_line.strip(), exp_line.strip())

    def test_3(self):
        """Test attack"""
        self.s.sendall("test3\n".encode())
        self.s.recv(1024).rstrip().decode()

        self.cmdline.do_addmon("tux coords 0 1 hello hi hp 10")
        self.s.recv(1024).rstrip().decode()
        self.cmdline.do_down("")
        self.s.recv(1024).rstrip().decode()
        self.cmdline.do_attack("tux with axe")
        response = self.s.recv(1024).rstrip().decode()
        self.assertEqual(response, "test3 attacked tux, damage 10 hit points\ntux died")

    def tearDown(self):
        self.s.close()

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
