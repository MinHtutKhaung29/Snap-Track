import os
import socket
import subprocess
import sys

import qrcode

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "qr.png")
PORT = 8010


def lan_ip():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetIPConfiguration | Where-Object {$_.NetAdapter.Name -eq 'Wi-Fi' -and $_.IPv4Address} | Select-Object -First 1).IPv4Address.IPAddress"],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def main():
    ip = lan_ip()
    url = "http://{}:{}/".format(ip, PORT)
    img = qrcode.make(url)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print("url  " + url)
    print("qr   " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
