import threading
import time
from router.scraper import RouterScraper
from database.db import SessionLocal
from database.models import Device, DeviceSession, NeighborNetwork, NeighborStatus
from config import ROUTER_URL, USERNAME, PASSWORD
from datetime import datetime

collector_thread = None
collector_running = False

def collect_data():
    scraper = RouterScraper(ROUTER_URL)
    scraper.login(USERNAME, PASSWORD)

    db = SessionLocal()
    devices = scraper.scrape_all()
    now = datetime.now()
    for device in devices:
            existing = db.query(Device).filter_by(mac=device.mac).first()
            if not existing:
                existing = Device(
                    hostname=device.hostname,
                    ip=device.ip,
                    mac=device.mac,
                    port_type=device.port_type
                )
                db.add(existing)
                db.commit()

            if device.status.lower() == "online":
                session = DeviceSession(
                    device_id=existing.id,
                    timestamp=now,
                    online_duration=device.duration
                )
                db.add(session)

    neighbors = scraper.scrape_neighboring_aps()
    for net in neighbors:
        existing = db.query(NeighborNetwork).filter_by(mac=net.get("mac")).first()
        if not existing:
            existing = NeighborNetwork(
                ssid=net.get("ssid"),
                mac=net.get("mac"),
                network_type=net.get("network_type"),
                channel=int(net.get("channel")),
                signal_strength=net.get("signal_strength"),
                auth_mode=net.get("auth_mode"),
                working_mode=net.get("working_mode"),
                max_rate=net.get("max_rate"),
            )
            db.add(existing)
            db.commit()

        status = NeighborStatus(
            network_id=existing.id,
            timestamp=now
        )
        db.add(status)

    db.commit()
    db.close()
    scraper.quit()

def _collector_loop(interval_minutes: int):
    global collector_running
    while collector_running:
        print("Collector: Starting data collection...")
        collect_data()
        print(f"Collector: Sleeping {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)

def start_collector_background(interval_minutes: int = 2):
    global collector_thread, collector_running
    if not collector_running:
        collector_running = True
        collector_thread = threading.Thread(target=_collector_loop, args=(interval_minutes,))
        collector_thread.daemon = True
        collector_thread.start()
        print("Collector started.")
    else:
        print("Collector already running.")

def stop_collector_background():
    global collector_running
    collector_running = False
    print("Collector stopped.")

def is_collector_running() -> bool:
    return collector_running