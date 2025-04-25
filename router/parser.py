from bs4 import BeautifulSoup

def parse_device_info(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    def get(id):  # Helper to safely extract by ID
        tag = soup.find(id=id)
        return tag.text.strip() if tag else None

    return {
        "device_type": get("td1_2"),
        "description": get("td2_2"),
        "serial_number": get("td3_2"),
        "hardware_version": get("td4_2"),
        "software_version": get("td5_2"),
        "manufacture_info": get("td6_2"),
        "registration_status": get("td7_2"),
        "ont_id": get("td8_2"),
        "cpu_usage": get("td9_2"),
        "memory_usage": get("td10_2"),
        "system_time": get("td14_2"),
        "custom_info": get("td13_2"),
        "ip_address": get("td21_2"),  # Optional (present in some configs)
        "uptime": get("ShowTime")     # Hidden by default, but Selenium captures it if JS loads it
    }