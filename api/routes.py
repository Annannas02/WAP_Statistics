from flask import Flask, jsonify
from router.scraper import RouterScraper
from database.db import init_db, SessionLocal
from database.models import Device, DeviceSession, NeighborNetwork, NeighborStatus
from config import ROUTER_URL, USERNAME, PASSWORD
from datetime import datetime

app = Flask(__name__)
init_db()

@app.route('/collect_devices', methods=['POST'])
def collect_devices():
    scraper = RouterScraper(ROUTER_URL)
    scraper.login(USERNAME, PASSWORD)
    
    devices = scraper.scrape_all()
    db = SessionLocal()

    print(devices)
    for device in devices:
        print(device.status)
        if device.status.lower() != "online":
            continue  # Only save active devices

        # Check if device already exists (match by MAC address)
        existing_device = db.query(Device).filter(Device.mac == device.mac).first()

        if existing_device:
            # Update fields (IP might have changed)
            existing_device.hostname = device.hostname
            existing_device.ip = device.ip
            existing_device.port_type = device.port_type
        else:
            # Create new device entry
            existing_device = Device(
                hostname=device.hostname,
                ip=device.ip,
                mac=device.mac,
                port_type=device.port_type,
            )
            db.add(existing_device)
            db.flush()  # Make sure the ID is generated

        # Add DeviceSession for currently active online device
        session = DeviceSession(
            device_id=existing_device.id,
            timestamp=datetime.now(),
            online_duration=device.duration
        )
        db.add(session)

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
        # Check if network already exists (by MAC)
        existing_network = db.query(NeighborNetwork).filter(NeighborNetwork.mac == neighbor.get("mac")).first()

        if existing_network:
            # Update fields if needed (channel, strength, etc.)
            existing_network.ssid = neighbor.get("ssid")
            existing_network.network_type = neighbor.get("network_type")
            existing_network.channel = int(neighbor.get("channel")) if neighbor.get("channel") else None
            existing_network.signal_strength = neighbor.get("signal_strength")
            existing_network.auth_mode = neighbor.get("auth_mode")
            existing_network.working_mode = neighbor.get("working_mode")
            existing_network.max_rate = neighbor.get("max_rate")
        else:
            # Create new network entry
            existing_network = NeighborNetwork(
                ssid=neighbor.get("ssid"),
                mac=neighbor.get("mac"),
                network_type=neighbor.get("network_type"),
                channel=int(neighbor.get("channel")) if neighbor.get("channel") else None,
                signal_strength=neighbor.get("signal_strength"),
                auth_mode=neighbor.get("auth_mode"),
                working_mode=neighbor.get("working_mode"),
                max_rate=neighbor.get("max_rate"),
            )
            db.add(existing_network)
            db.flush()

        # Add NeighborStatus for current timestamp
        status = NeighborStatus(
            network_id=existing_network.id,
            timestamp=datetime.now()
        )
        db.add(status)

    db.commit()
    db.close()
    scraper.quit()
    return jsonify({"status": "neighbors collected"})

@app.route('/devices/history', methods=['GET'])
def get_devices_history():
    db = SessionLocal()
    devices = db.query(Device).all()
    results = [d.__dict__ for d in devices]
    for r in results:
        r.pop('_sa_instance_state', None)
    db.close()
    return jsonify(results)

@app.route('/neighbors/history', methods=['GET'])
def get_neighbors_history():
    db = SessionLocal()
    neighbors = db.query(NeighborNetwork).all()
    results = [n.__dict__ for n in neighbors]
    for r in results:
        r.pop('_sa_instance_state', None)
    db.close()
    return jsonify(results)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})
