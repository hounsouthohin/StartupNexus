
import socket
import time
import sys

def wait_for_port(host, port, timeout=30.0):
    """Wait until a port starts accepting TCP connections."""
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    f"Waited too long for the port {port} on host {host} to start accepting connections."
                ) from ex

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python wait-for-it.py host:port timeout")
        sys.exit(1)
    
    host, port_str = sys.argv[1].split(":")
    port = int(port_str)
    timeout = int(sys.argv[2])
    
    try:
        wait_for_port(host, port, timeout=float(timeout))
        print(f"Port {port} on host {host} is now available.")
    except TimeoutError as ex:
        print(f"Error: {ex}", file=sys.stderr)
        sys.exit(1)
