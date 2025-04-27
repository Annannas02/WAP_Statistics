from bs4 import BeautifulSoup
from .data_models import DeviceInfo
import re

def parse_device_list(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select("tr.trTabContent")
    devices = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 6:
            devices.append({
                "hostname": cols[0].get("title", "").strip(),
                "port_id": cols[1].get("title", "").strip(),
                "device_type": cols[2].get("title", "").strip(),
                "ip": cols[3].get("title", "").strip(),
                "mac": cols[4].get("title", "").strip(),
                "status": cols[5].get("title", "").strip(),
            })
    return devices

def parse_device_details(html: str) -> DeviceInfo:
    soup = BeautifulSoup(html, 'html.parser')

    def get_value(label):
        cell = soup.find("td", string=label)
        return cell.find_next_sibling("td").text.strip() if cell else "--"

    hostname = get_value("Host Name:")
    ip = get_value("IP Address:")
    mac = get_value("MAC Address:")
    port_type = get_value("Port Type:")
    status = get_value("Device Status:")

    # Get online duration from the div with id ShowOnlineTimeInfo
    online_minutes = 0
    duration_container = soup.find(id="ShowOnlineTimeInfo")
    if duration_container:
        duration_td = duration_container.find_all("td")
        if len(duration_td) >= 2:
            duration_text = duration_td[1].text.strip()
            online_minutes = parse_duration_to_minutes(duration_text)

    return DeviceInfo(
        hostname=hostname,
        ip=ip,
        mac=mac,
        port_type=port_type,
        status=status,
        duration=online_minutes
    )

def parse_duration_to_minutes(duration_str: str) -> int:
    """Parses a duration like '5 hours 41 minutes' into total minutes."""
    hours = 0
    minutes = 0
    hour_match = re.search(r"(\d+)\s*hour", duration_str, re.IGNORECASE)
    minute_match = re.search(r"(\d+)\s*minute", duration_str, re.IGNORECASE)

    if hour_match:
        hours = int(hour_match.group(1))
    if minute_match:
        minutes = int(minute_match.group(1))

    return hours * 60 + minutes

def extract_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    match = re.search(r'(\d+)\s*/\s*(\d+)', text)
    if match:
        return int(match.group(2))
    return 1

def parse_neighbor_aps(html: str) -> list[dict]:

    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select('tr[id^=wlan_napinfo_table_record]')
    results = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 11:
            continue
        results.append({
            "ssid": cells[0].text.strip(),
            "mac": cells[1].text.strip(),
            "network_type": cells[2].text.strip(),
            "channel": cells[3].text.strip(),
            "signal_strength": cells[4].text.strip(),
            "noise": cells[5].text.strip(),
            "dtim": cells[6].text.strip(),
            "beacon_period": cells[7].text.strip(),
            "auth_mode": cells[8].text.strip(),
            "working_mode": cells[9].text.strip(),
            "max_rate": cells[10].text.strip(),
        })
    return results