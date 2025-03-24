#!/usr/bin/env python3.13
import sys
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

def test(HandlerClass=SimpleHTTPRequestHandler,
         ServerClass=ThreadingHTTPServer,
         protocol="HTTP/1.0", port=8000, bind=None):
    """Test the HTTP request handler class."""
    ServerClass.address_family, addr = _get_best_family(bind, port)
    HandlerClass.protocol_version = protocol
    with ServerClass(addr, HandlerClass) as httpd:
        host, port = httpd.socket.getsockname()[:2]
        url_host = f'[{host}]' if ':' in host else host

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        real_ip = s.getsockname()[0]
        s.close()

        print(f"Serving HTTP on {real_ip} port {port} (http://{real_ip}:{port}/) ...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            sys.exit(0)

def _get_best_family(bind, port):
    """Helper function for test()."""
    family = socket.AF_INET
    addr = (bind if bind is not None else '0.0.0.0', port)
    return family, addr

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, help="port number to listen on")
    args = parser.parse_args()
    test(port=args.port)
