import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.models import CheckResult
from app.services.checker import check_service
from config import Config

class ServiceMonitor:
    def __init__(self):
        self.running = False
        self.thread = None
    
    def load_services(self):
        """Load services from services.json"""
        with open(Config.SERVICES_FILE) as f:
            services = json.load(f)

        return [s["domain"] for s in services]
    
    def run_check_cycle(self):
        """Run one complete check cycle for all services"""
        services = self.load_services()
        
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {executor.submit(check_service, svc): svc for svc in services}
            
            for future in as_completed(futures):
                service = futures[future]
                try:
                    svc, dns, tcp, latency, packet_loss, status = future.result()
                    
                    # Save to database
                    CheckResult.save(svc, latency, packet_loss, dns, tcp, status)
                    
                    # Log to console
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{svc}] "
                          f"DNS:{dns} TCP:{tcp} PING:{latency} STATUS:{status}")
                    
                except Exception as e:
                    print(f"Error checking {service}: {e}")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle completed\n")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            self.run_check_cycle()
            time.sleep(Config.CHECK_INTERVAL)
    
    def start(self):
        """Start monitoring in background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.thread.start()
            print("Service monitor started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Service monitor stopped")

# Global monitor instance
monitor = ServiceMonitor()
