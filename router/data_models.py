from dataclasses import dataclass

@dataclass
class DeviceInfo:
    hostname: str
    ip: str
    mac: str
    port_type: str
    status: str
