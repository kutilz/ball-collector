"""Cari IP ESP32-CAM robot di jaringan yang sama dengan laptop.

Coba http://ballcollector.local dulu (mDNS); kalau gagal, scan seluruh subnet /24
laptop dan cari perangkat yang menjawab endpoint /tel.

Pakai: python find_robot.py
"""
import concurrent.futures
import json
import socket
import urllib.request

HOSTNAME = "ballcollector.local"


def cek(host, timeout=0.6):
    try:
        with urllib.request.urlopen(f"http://{host}/tel", timeout=timeout) as r:
            data = json.loads(r.read())
            return data.get("ssid", "?")
    except Exception:
        return None


def ip_laptop():
    # Tidak benar-benar mengirim paket; hanya memilih interface ke internet
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def main():
    try:
        ip = socket.gethostbyname(HOSTNAME)
        if cek(ip, timeout=2):
            print(f"Robot ditemukan via mDNS: http://{ip}/tune")
            return
    except OSError:
        pass

    base = ip_laptop().rsplit(".", 1)[0]
    print(f"mDNS gagal, scan {base}.1-254 ...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        hasil = ex.map(lambda i: (f"{base}.{i}", cek(f"{base}.{i}")), range(1, 255))
        found = [(h, ssid) for h, ssid in hasil if ssid]
    if not found:
        print("Robot tidak ditemukan. Pastikan laptop dan robot di WiFi yang sama.")
    for h, ssid in found:
        print(f"Robot ditemukan: http://{h}/tune  (WiFi {ssid})")


if __name__ == "__main__":
    main()
