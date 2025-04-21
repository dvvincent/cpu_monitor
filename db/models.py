"""
SQLAlchemy models for SystemPulse metrics.
"""
from datetime import datetime
from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SystemMetrics(Base):
    """Time-series metrics for system monitoring."""
    __tablename__ = 'system_metrics'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # CPU metrics
    cpu_percent = Column(Float)
    cpu_freq_current = Column(Float)
    cpu_freq_min = Column(Float)
    cpu_freq_max = Column(Float)
    
    # Memory metrics
    memory_total = Column(Float)
    memory_available = Column(Float)
    memory_used = Column(Float)
    memory_percent = Column(Float)
    swap_total = Column(Float)
    swap_used = Column(Float)
    swap_free = Column(Float)
    swap_percent = Column(Float)
    
    # Disk metrics
    disk_total = Column(Float)
    disk_used = Column(Float)
    disk_free = Column(Float)
    disk_percent = Column(Float)
    
    # Network metrics
    network_bytes_sent = Column(Float)
    network_bytes_recv = Column(Float)
    network_send_rate = Column(Float)
    network_recv_rate = Column(Float)
    
    # Temperature
    temperature = Column(Float)
    
    # System info
    boot_time = Column(DateTime)
    hostname = Column(String)

    def __repr__(self):
        return f"<SystemMetrics(timestamp={self.timestamp}, cpu_percent={self.cpu_percent})>"
