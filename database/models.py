from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DeviceSnapshot(Base):
    __tablename__ = 'device_snapshots'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hostname = Column(String)
    ip = Column(String)
    mac = Column(String)
    port_type = Column(String)
    status = Column(String)

class NeighborSnapshot(Base):
    __tablename__ = 'neighbor_snapshots'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ssid = Column(String)
    mac = Column(String)
    network_type = Column(String)
    channel = Column(Integer)
    signal_strength = Column(String)
    noise = Column(String)
    dtim = Column(Integer)
    beacon_period = Column(Integer)
    auth_mode = Column(String)
    working_mode = Column(String)
    max_rate = Column(String)