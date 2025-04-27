from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    ip = Column(String)
    mac = Column(String, unique=True, nullable=False)
    port_type = Column(String)

class DeviceSession(Base):
    __tablename__ = 'device_sessions'

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    online_duration = Column(Integer)  # in minutes

class NeighborNetwork(Base):
    __tablename__ = 'neighbor_networks'

    id = Column(Integer, primary_key=True)
    ssid = Column(String)
    mac = Column(String, unique=True, nullable=False)
    network_type = Column(String)
    channel = Column(Integer)
    signal_strength = Column(String)
    auth_mode = Column(String)
    working_mode = Column(String)
    max_rate = Column(String)

class NeighborStatus(Base):
    __tablename__ = 'neighbor_statuses'

    id = Column(Integer, primary_key=True)
    network_id = Column(Integer, ForeignKey('neighbor_networks.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)