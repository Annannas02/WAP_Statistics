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

def parse_dhcp_server_info(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    host_ip = ""
    subnet_mask = ""

    ip_cell = soup.find("td", string="LAN Host IP Address:")
    if ip_cell:
        host_ip = ip_cell.find_next_sibling("td").text.strip()

    mask_cell = soup.find("td", string="Subnet Mask:")
    if mask_cell:
        subnet_mask = mask_cell.find_next_sibling("td").text.strip()

    return {
        "host_ip": host_ip,
        "subnet_mask": subnet_mask
    }

def parse_dhcp_info(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    total_ip_addresses = int(soup.find(id="lanuser_TotalIpNum").text.strip())
    eth_ip_addresses = int(soup.find(id="lanuser_EthPortIpNum").text.strip())
    wifi_ip_addresses = int(soup.find(id="lanuser_WifiPortIpNum").text.strip())
    remaining_ip_addresses = int(soup.find(id="lanuser_LeftIpAddrNum").text.strip())

    return {
        "total_ip_addresses": total_ip_addresses,
        "eth_ip_addresses": eth_ip_addresses,
        "wifi_ip_addresses": wifi_ip_addresses,
        "remaining_ip_addresses": remaining_ip_addresses,
    }

def parse_device_name(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    device_name_tag = soup.find("td", id="td1_2")
    if device_name_tag:
        return {"device_name": device_name_tag.text.strip()}
    return ""

def parse_eth_packets(html: str):
    soup = BeautifulSoup(html, "html.parser")
    ports_info = []

    # Ethernet statistics are under userEthInfos[] JavaScript object
    # But the visible table in HTML contains them too
    table = soup.find("table", id="eth_status_table")
    if not table:
        return ports_info

    rows = table.find_all("tr")[2:]  # Skip the headers
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 7:
            port_info = {
                "port_number": cols[0].text.strip(),
                "mode": cols[1].text.strip(),
                "speed": cols[2].text.strip(),
                "link": cols[3].text.strip(),
                "rx_bytes": cols[4].text.strip(),
                "rx_packets": cols[5].text.strip(),
                "tx_bytes": cols[6].text.strip(),
                "tx_packets": cols[7].text.strip(),
            }
            ports_info.append(port_info)

    return ports_info

def parse_wlan_packets(html: str):
    soup = BeautifulSoup(html, "html.parser")
    wlan_info = []

    table = soup.find("table", id="wlan_pkts_statistic_table")
    if not table:
        return wlan_info

    rows = table.find_all("tr")[2:]  # Skip header rows
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            wlan_entry = {
                "ssid_index": cols[0].text.strip(),
                "ssid_name": cols[1].text.strip(),
                "rx_bytes": cols[2].text.strip(),
                "rx_packets": cols[3].text.strip(),
                "rx_discarded": cols[5].text.strip(),
                "tx_bytes": cols[6].text.strip(),
                "tx_packets": cols[7].text.strip(),
                "tx_discarded": cols[9].text.strip(),
            }
            wlan_info.append(wlan_entry)
    
    enc_table = soup.find("table", id="wlan_ssidinfo_table")
    if not table:
        return wlan_info

    rows = enc_table.find_all("tr")[1:]  # Skip header rows
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            wlan_entry2 = {
                "auth_mode": cols[3].text.strip(),
                "encryption_mode": cols[4].text.strip(),
            }
            wlan_info.append(wlan_entry2)
    return wlan_info