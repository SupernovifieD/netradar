import subprocess
import socket
import requests
from requests.exceptions import RequestException

def dns_check(domain, timeout=2):
    """Check if DNS resolution works"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(domain)
        return "OK"
    except Exception:
        return "FAIL"

def tcp_check(domain):
    """Check TCP/HTTP connectivity"""
    try:
        requests.head(f"https://{domain}", timeout=2, allow_redirects=True, verify=False)
        return "HTTPS"
    except RequestException:
        pass
    try:
        requests.head(f"http://{domain}", timeout=2, allow_redirects=True)
        return "HTTP"
    except RequestException:
        pass
    return "FAIL"

def ping_stats(domain):
    """Get ping latency and packet loss"""
    try:
        result = subprocess.run(
            ["ping", "-c", "4", "-W", "1", domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        output = result.stdout

        if result.returncode != 0:
            return ("na", "100")

        loss_line = [l for l in output.split("\n") if "packet loss" in l]
        packet_loss = loss_line[0].split(",")[2].strip().split("%")[0] if loss_line else "100"

        avg_line = [l for l in output.split("\n") if "avg" in l or "mdev" in l]
        latency = avg_line[0].split("=")[1].split("/")[1].strip() if avg_line else "na"

        return (latency, packet_loss)

    except Exception:
        return ("na", "100")

def compute_status(dns, tcp):
    """Determine overall service status"""
    return "UP" if tcp != "FAIL" else "DOWN"

def check_service(service):
    """Run all checks for a service"""
    dns = dns_check(service)
    tcp = tcp_check(service) if dns == "OK" else "FAIL"
    latency, packet_loss = ping_stats(service)
    status = compute_status(dns, tcp)
    return (service, dns, tcp, latency, packet_loss, status)
