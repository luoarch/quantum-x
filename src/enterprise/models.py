"""
SQLAlchemy Models - Type Safe Database Schema
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()

class Client(Base):
    """Client model for network effects tracking"""
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    institution = Column(String(200))
    client_type = Column(String(50))  # bank, fintech, asset_management
    client_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_prediction_at = Column(DateTime(timezone=True))
    
    # Statistics
    total_predictions = Column(Integer, default=0)
    total_feedback = Column(Integer, default=0)
    avg_uncertainty = Column(Float, default=0.0)
    outlier_rate = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)

class Prediction(Base):
    """Prediction model for network effects tracking"""
    __tablename__ = "predictions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), nullable=False, index=True)
    prediction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Input data
    fed_rate = Column(Float, nullable=False)
    selic_rate = Column(Float, nullable=False)
    input_metadata = Column(JSON)
    
    # Prediction results
    spillover_prediction = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)
    is_outlier = Column(Boolean, default=False)
    high_uncertainty = Column(Boolean, default=False)
    
    # Model info
    model_version = Column(String(50), nullable=False)
    var_component = Column(Float)
    nn_component = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Network effects tracking
    network_tracked = Column(Boolean, default=True)
    retrain_used = Column(Boolean, default=False)

class Feedback(Base):
    """Feedback model for network effects improvement"""
    __tablename__ = "feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), nullable=False, index=True)
    prediction_id = Column(String(100), nullable=False, index=True)
    
    # Feedback data
    actual_outcome = Column(Float)
    feedback_score = Column(Integer)  # 1-10 rating
    was_accurate = Column(Boolean)
    feedback_text = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Processing
    processed = Column(Boolean, default=False)
    retrain_used = Column(Boolean, default=False)

class NetworkMetrics(Base):
    """Network effects metrics for analytics"""
    __tablename__ = "network_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Metrics
    total_clients = Column(Integer, nullable=False)
    total_predictions = Column(Integer, nullable=False)
    health_score = Column(Float, nullable=False)
    network_strength = Column(Float, nullable=False)
    
    # Detailed metrics
    avg_uncertainty = Column(Float, nullable=False)
    outlier_rate = Column(Float, nullable=False)
    high_uncertainty_rate = Column(Float, nullable=False)
    
    # Trends
    prediction_trend = Column(String(20))  # increasing, decreasing, stable
    uncertainty_trend = Column(String(20))
    outlier_trend = Column(String(20))
    
    # Network strength components
    client_diversity = Column(Float, nullable=False)
    prediction_volume = Column(Float, nullable=False)
    input_diversity = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

class ModelVersion(Base):
    """Model version tracking for retraining"""
    __tablename__ = "model_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(50), unique=True, nullable=False)
    
    # Model info
    model_type = Column(String(100), nullable=False)
    accuracy_score = Column(Float)
    r2_score = Column(Float)
    rmse_score = Column(Float)
    
    # Training data
    training_samples = Column(Integer)
    training_clients = Column(Integer)
    training_period_start = Column(DateTime(timezone=True))
    training_period_end = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=False)
    is_retrained = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deployed_at = Column(DateTime(timezone=True))
    
    # Metadata
    model_metadata = Column(JSON)
    retrain_reason = Column(Text)
