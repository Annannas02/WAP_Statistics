from flask import Flask, jsonify, request
from router.scraper import RouterScraper
from database.db import init_db, SessionLocal
from database.models import Device, DeviceSession, NeighborNetwork, NeighborStatus
from config import ROUTER_URL, USERNAME, PASSWORD, COLLECTOR_ENABLED, COLLECTOR_INTERVAL_MINUTES
from datetime import datetime
from sqlalchemy import func
from datetime import timedelta
from sqlalchemy import and_
from collector import start_collector_background, stop_collector_background, is_collector_running

app = Flask(__name__)
init_db()

@app.route('/collector/start', methods=['POST'])
def start_collector():
    start_collector_background(interval_minutes=COLLECTOR_INTERVAL_MINUTES)
    return jsonify({"status": "collector started"})

@app.route('/collector/stop', methods=['POST'])
def stop_collector():
    stop_collector_background()
    return jsonify({"status": "collector stopped"})

@app.route('/collector/status', methods=['GET'])
def collector_status():
    status = "running" if is_collector_running() else "stopped"
    return jsonify({"collector_status": status})

@app.route('/devices/collect', methods=['POST'])
def collect_devices():
    scraper = RouterScraper(ROUTER_URL)
    print(USERNAME)
    print(PASSWORD)
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

@app.route('/networks/collect', methods=['POST'])
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

@app.route('/devices/list', methods=['GET'])
def get_devices_list():
    db = SessionLocal()
    devices = db.query(Device).all()
    results = [d.__dict__ for d in devices]
    for r in results:
        r.pop('_sa_instance_state', None)
    db.close()
    return jsonify(results)

@app.route('/networks/list', methods=['GET'])
def get_neighbors_list():
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


@app.route('/devices/stats', methods=['GET'])
def device_stats():
    db = SessionLocal()
    
    # Fetch all data
    devices = db.query(Device).all()
    sessions = db.query(DeviceSession).order_by(DeviceSession.timestamp).all()
    
    if not devices or not sessions:
        db.close()
        return jsonify({"error": "No data available"}), 404

    # Create helper mapping
    device_id_to_hostname = {device.id: device.hostname for device in devices}
    device_id_to_port_type = {device.id: device.port_type for device in devices}

    # Group sessions into "scans" per minute
    scans = {}
    for session in sessions:
        minute_key = session.timestamp.replace(second=0, microsecond=0)
        scans.setdefault(minute_key, []).append(session)

    # Sort scans by time
    sorted_scans = sorted(scans.items())

    if not sorted_scans:
        db.close()
        return jsonify({"error": "No scans available"}), 404

    # Last scan
    last_scan_timestamp, last_scan_sessions = sorted_scans[-1]

    # Current connected devices count
    current_connected_devices = len(last_scan_sessions)

    # Historical max
    historical_max = max(len(scan) for _, scan in sorted_scans)

    # Build device cumulative data
    device_durations = {}
    device_longest_online = {}
    device_shortest_online = {}

    for session in sessions:
        device_durations[session.device_id] = device_durations.get(session.device_id, 0) + session.online_duration
        device_longest_online[session.device_id] = max(device_longest_online.get(session.device_id, 0), session.online_duration)
        if session.online_duration > 0:
            if session.device_id not in device_shortest_online:
                device_shortest_online[session.device_id] = session.online_duration
            else:
                device_shortest_online[session.device_id] = min(device_shortest_online[session.device_id], session.online_duration)

    # Longest and Shortest connection
    if device_longest_online:
        longest_device_id = max(device_longest_online, key=lambda x: device_longest_online[x])
        longest_connection = {
            "device_id": longest_device_id,
            "hostname": device_id_to_hostname.get(longest_device_id, "--"),
            "minutes": device_longest_online[longest_device_id]
        }
    else:
        longest_connection = None

    if device_shortest_online:
        shortest_device_id = min(device_shortest_online, key=lambda x: device_shortest_online[x])
        shortest_connection = {
            "device_id": shortest_device_id,
            "hostname": device_id_to_hostname.get(shortest_device_id, "--"),
            "minutes": device_shortest_online[shortest_device_id]
        }
    else:
        shortest_connection = None

    # Top 5 most active all time
    top5_all_time = sorted(device_durations.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_all_time_result = [
        {
            "device_id": dev_id,
            "hostname": device_id_to_hostname.get(dev_id, "--"),
            "total_minutes": duration
        }
        for dev_id, duration in top5_all_time
    ]

    # Top 5 most active last scan
    top5_last_scan = sorted(last_scan_sessions, key=lambda x: x.online_duration, reverse=True)[:5]
    top5_last_scan_result = [
        {
            "device_id": session.device_id,
            "hostname": device_id_to_hostname.get(session.device_id, "--"),
            "online_minutes": session.online_duration
        }
        for session in top5_last_scan
    ]

    # Port Type Usage
    port_type_usage = {}
    for port_type in device_id_to_port_type.values():
        if port_type:
            port_type_usage[port_type] = port_type_usage.get(port_type, 0) + 1

    # Average online duration
    avg_online_duration = round(sum(device_durations.values()) / len(device_durations), 2)

    db.close()

    return jsonify({
        "current_connected_devices": current_connected_devices,
        "historical_max_connected_devices": historical_max,
        "average_online_duration_minutes": avg_online_duration,
        "longest_connection": longest_connection,
        "shortest_connection": shortest_connection,
        "top5_most_active_all_time": top5_all_time_result,
        "top5_most_active_last_scan": top5_last_scan_result,
        "port_type_usage": port_type_usage
    })


@app.route('/networks/stats', methods=['GET'])
def network_stats():
    db = SessionLocal()

    # Find the latest timestamp (most recent scan)
    latest_status = db.query(NeighborStatus).order_by(NeighborStatus.timestamp.desc()).first()
    if not latest_status:
        db.close()
        return jsonify({"error": "No network data available"}), 404

    latest_time = latest_status.timestamp
    interval_start = latest_time - timedelta(minutes=1)

    # Get all statuses within 1 minute of the latest timestamp
    recent_statuses = db.query(NeighborStatus).filter(
        NeighborStatus.timestamp.between(interval_start, latest_time)
    ).all()

    network_ids = [status.network_id for status in recent_statuses]

    if not network_ids:
        db.close()
        return jsonify({"error": "No recent network data available"}), 404

    networks = db.query(NeighborNetwork).filter(NeighborNetwork.id.in_(network_ids)).all()

    # Calculate stats
    total_networks_detected_now = len(networks)

    # Average signal strength (convert to int first)
    signal_strengths = []
    for net in networks:
        if net.signal_strength:
            try:
                value = int(net.signal_strength.split("(")[0])  # Example: "-70(Weak)"
                signal_strengths.append(value)
            except (ValueError, AttributeError):
                continue

    average_signal_strength = round(sum(signal_strengths) / len(signal_strengths), 2) if signal_strengths else None

    # Channel usage count
    channel_usage = {}
    for net in networks:
        if net.channel is not None:
            channel_usage[net.channel] = channel_usage.get(net.channel, 0) + 1

    # Most used auth mode
    auth_mode_counts = {}
    for net in networks:
        if net.auth_mode:
            auth_mode_counts[net.auth_mode] = auth_mode_counts.get(net.auth_mode, 0) + 1

    # Strongest and weakest network
    networks_with_signal = []
    for net in networks:
        if net.signal_strength:
            try:
                strength = net.signal_strength
                if "(" in strength:
                    strength_value = int(strength.split("(")[0])
                else:
                    strength_value = int(strength)  # Plain -70 style
                networks_with_signal.append((net, strength_value))
            except ValueError:
                continue  # Skip invalid signal_strength formats

    # Find strongest and weakest network
    if networks_with_signal:
        strongest = max(networks_with_signal, key=lambda x: x[1])[0]
        weakest = min(networks_with_signal, key=lambda x: x[1])[0]
    else:
        strongest = None
        weakest = None

    db.close()

    return jsonify({
        "total_networks_detected_now": total_networks_detected_now,
        "average_signal_strength": average_signal_strength,
        "channel_usage": dict(sorted(channel_usage.items(), key=lambda item: item[1], reverse=True)),
        "auth_modes": dict(sorted(auth_mode_counts.items(), key=lambda item: item[1], reverse=True)),
        "strongest_network": {
            "network_id": strongest.id,
            "ssid": strongest.ssid,
            "signal_strength": strongest.signal_strength
        } if strongest else None,
        "weakest_network": {
            "network_id": weakest.id,
            "ssid": weakest.ssid,
            "signal_strength": weakest.signal_strength
        } if weakest else None
    })
    
@app.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    db = SessionLocal()
    device = db.query(Device).filter(Device.id == device_id).first()
    db.close()
    if device:
        return jsonify({
            "id": device.id,
            "hostname": device.hostname,
            "ip": device.ip,
            "mac": device.mac,
            "port_type": device.port_type
        })
    else:
        return jsonify({"error": "Device not found"}), 404

@app.route('/networks/<int:network_id>', methods=['GET'])
def get_network(network_id):
    db = SessionLocal()
    network = db.query(NeighborNetwork).filter(NeighborNetwork.id == network_id).first()
    db.close()
    if network:
        return jsonify({
            "id": network.id,
            "ssid": network.ssid,
            "mac": network.mac,
            "network_type": network.network_type,
            "channel": network.channel,
            "signal_strength": network.signal_strength,
            "auth_mode": network.auth_mode,
            "working_mode": network.working_mode,
            "max_rate": network.max_rate
        })
    else:
        return jsonify({"error": "Network not found"}), 404
    
@app.route('/networks/filter', methods=['GET'])
def filter_networks():
    db = SessionLocal()

    # Read filters from query parameters
    channel_min = request.args.get('channel_min', type=int)
    channel_max = request.args.get('channel_max', type=int)
    signal_sort = request.args.get('signal_sort', default=None, type=str)
    batch_type = request.args.get('batch', default='all', type=str)
    start_time = parse_datetime_safe(request.args.get('start'))
    end_time = parse_datetime_safe(request.args.get('end'))

    query = db.query(NeighborNetwork)

    if channel_min is not None and channel_max is not None:
        query = query.filter(NeighborNetwork.channel.between(channel_min, channel_max))

    if batch_type == 'recent':
        latest_timestamp = db.query(NeighborStatus.timestamp).order_by(NeighborStatus.timestamp.desc()).first()
        if latest_timestamp:
            recent_ids = db.query(NeighborStatus.network_id).filter(NeighborStatus.timestamp == latest_timestamp[0]).subquery()
            query = query.filter(NeighborNetwork.id.in_(recent_ids))
    elif batch_type == 'timeframe' and start_time and end_time:
        ids_in_time = db.query(NeighborStatus.network_id).filter(NeighborStatus.timestamp.between(start_time, end_time)).subquery()
        query = query.filter(NeighborNetwork.id.in_(ids_in_time))

    if signal_sort:
        if signal_sort == 'asc':
            query = query.order_by(NeighborNetwork.signal_strength.asc())
        elif signal_sort == 'desc':
            query = query.order_by(NeighborNetwork.signal_strength.desc())

    results = query.all()

    filtered = []
    for n in results:
        filtered.append({
            'id': n.id,
            'ssid': n.ssid,
            'mac': n.mac,
            'network_type': n.network_type,
            'channel': n.channel,
            'signal_strength': n.signal_strength,
            'auth_mode': n.auth_mode,
            'working_mode': n.working_mode,
            'max_rate': n.max_rate
        })

    db.close()

    return jsonify({
        "total_matched": len(filtered),
        "filters_used": request.args.to_dict(),
        "entries": filtered
    })


@app.route('/devices/filter', methods=['GET'])
def filter_devices():
    db = SessionLocal()

    ip_start = request.args.get('ip_start')
    ip_end = request.args.get('ip_end')
    port_type = request.args.get('port_type')
    batch_type = request.args.get('batch', default='all', type=str)
    start_time = parse_datetime_safe(request.args.get('start'))
    end_time = parse_datetime_safe(request.args.get('end'))

    query = db.query(Device)

    if ip_start and ip_end:
        query = query.filter(and_(Device.ip >= ip_start, Device.ip <= ip_end))

    if port_type:
        query = query.filter(Device.port_type == port_type)

    if batch_type == 'recent':
        latest_timestamp = db.query(DeviceSession.timestamp).order_by(DeviceSession.timestamp.desc()).first()
        if latest_timestamp:
            recent_device_ids = db.query(DeviceSession.device_id).filter(DeviceSession.timestamp == latest_timestamp[0]).subquery()
            query = query.filter(Device.id.in_(recent_device_ids))
    elif batch_type == 'timeframe' and start_time and end_time:
        ids_in_time = db.query(DeviceSession.device_id).filter(DeviceSession.timestamp.between(start_time, end_time)).subquery()
        query = query.filter(Device.id.in_(ids_in_time))

    results = query.all()

    filtered = []
    for d in results:
        filtered.append({
            'id': d.id,
            'hostname': d.hostname,
            'ip': d.ip,
            'mac': d.mac,
            'port_type': d.port_type
        })

    db.close()

    return jsonify({
        "total_matched": len(filtered),
        "filters_used": request.args.to_dict(),
        "entries": filtered
    })

@app.route('/router/summary', methods=['GET'])
def router_summary():
    scraper = RouterScraper(ROUTER_URL)
    try:
        scraper.login(USERNAME, PASSWORD)
        summary = scraper.scrape_router_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        scraper.quit()


def parse_datetime_safe(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
    