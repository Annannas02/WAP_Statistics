from flask import Flask, jsonify
from router.scraper import RouterScraper
from database.db import init_db, SessionLocal
from database.models import DeviceSnapshot, NeighborSnapshot
from config import ROUTER_URL, USERNAME, PASSWORD

app = Flask(__name__)
init_db()


@app.route('/collect_devices', methods=['POST'])
def collect_devices():
    
    scraper = RouterScraper(ROUTER_URL)
    scraper.login(USERNAME, PASSWORD)
    
    devices = scraper.scrape_all()
    db = SessionLocal()
    for device in devices:
        snap = DeviceSnapshot(
            hostname=device.hostname,
            ip=device.ip,
            mac=device.mac,
            port_type=device.port_type,
            status=device.status,
        )
        db.add(snap)
    db.commit()
    db.close()
    scraper.quit()
    return jsonify({"status": "devices collected"})

@app.route('/collect_neighbors', methods=['POST'])
def collect_neighbors():
    scraper = RouterScraper(ROUTER_URL)
    scraper.login(USERNAME, PASSWORD)
    neighbors = scraper.scrape_neighboring_aps()
    db = SessionLocal()
    for neighbor in neighbors:
        snap = NeighborSnapshot(
            ssid=neighbor.get("ssid"),
            mac=neighbor.get("mac"),
            network_type=neighbor.get("network_type"),
            channel=int(neighbor.get("channel")),
            signal_strength=neighbor.get("signal_strength"),
            noise=neighbor.get("noise"),
            dtim=int(neighbor.get("dtim")),
            beacon_period=int(neighbor.get("beacon_period")),
            auth_mode=neighbor.get("auth_mode"),
            working_mode=neighbor.get("working_mode"),
            max_rate=neighbor.get("max_rate"),
        )
        db.add(snap)
    db.commit()
    db.close()
    scraper.quit()
    return jsonify({"status": "neighbors collected"})

@app.route('/devices/history', methods=['GET'])
def get_devices_history():
    db = SessionLocal()
    devices = db.query(DeviceSnapshot).all()
    results = [d.__dict__ for d in devices]
    for r in results:
        r.pop('_sa_instance_state', None)
    db.close()
    return jsonify(results)

@app.route('/neighbors/history', methods=['GET'])
def get_neighbors_history():
    db = SessionLocal()
    neighbors = db.query(NeighborSnapshot).all()
    results = [n.__dict__ for n in neighbors]
    for r in results:
        r.pop('_sa_instance_state', None)
    db.close()
    return jsonify(results)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})
