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

def parse_device_details(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    def get_value(label):
        cell = soup.find("td", string=label)
        return cell.find_next_sibling("td").text.strip() if cell else "--"

    return DeviceInfo(
        hostname=get_value("Host Name:"),
        ip=get_value("IP Address:"),
        mac=get_value("MAC Address:"),
        port_type=get_value("Port Type:"),
        status=get_value("Device Status:")
    )

def extract_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    # Look for the pattern like "1/2"
    match = re.search(r'(\d+)\s*/\s*(\d+)', text)
    if match:
        return int(match.group(2))
    return 1  # Fallback if not found

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