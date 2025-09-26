"""
Database Manager - PostgreSQL with SQLAlchemy
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator, Optional, List, Dict, Any
import logging

from .config import config
from .models import Base, Client, Prediction, Feedback, NetworkMetrics, ModelVersion

logger = logging.getLogger(__name__)

class DatabaseManager:
    """PostgreSQL Database Manager with connection pooling"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection and create tables"""
        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                config.database.url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # Client operations
    def create_client(self, client_data: Dict[str, Any]) -> Optional[Client]:
        """Create new client"""
        try:
            with self.get_session() as session:
                client = Client(**client_data)
                session.add(client)
                session.flush()
                return client
        except SQLAlchemyError as e:
            logger.error(f"Error creating client: {e}")
            return None
    
    def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        try:
            with self.get_session() as session:
                return session.query(Client).filter(Client.client_id == client_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting client: {e}")
            return None
    
    def update_client_stats(self, client_id: str, stats: Dict[str, Any]) -> bool:
        """Update client statistics"""
        try:
            with self.get_session() as session:
                client = session.query(Client).filter(Client.client_id == client_id).first()
                if client:
                    for key, value in stats.items():
                        setattr(client, key, value)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error updating client stats: {e}")
            return False
    
    # Prediction operations
    def create_prediction(self, prediction_data: Dict[str, Any]) -> Optional[Prediction]:
        """Create new prediction record"""
        try:
            with self.get_session() as session:
                prediction = Prediction(**prediction_data)
                session.add(prediction)
                session.flush()
                return prediction
        except SQLAlchemyError as e:
            logger.error(f"Error creating prediction: {e}")
            return None
    
    def get_predictions_by_client(self, client_id: str, limit: int = 100) -> List[Prediction]:
        """Get predictions for a specific client"""
        try:
            with self.get_session() as session:
                return session.query(Prediction)\
                    .filter(Prediction.client_id == client_id)\
                    .order_by(Prediction.created_at.desc())\
                    .limit(limit)\
                    .all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting client predictions: {e}")
            return []
    
    def get_recent_predictions(self, hours: int = 24, limit: int = 1000) -> List[Prediction]:
        """Get recent predictions for retraining"""
        try:
            with self.get_session() as session:
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                
                return session.query(Prediction)\
                    .filter(Prediction.created_at >= cutoff)\
                    .order_by(Prediction.created_at.desc())\
                    .limit(limit)\
                    .all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent predictions: {e}")
            return []
    
    # Feedback operations
    def create_feedback(self, feedback_data: Dict[str, Any]) -> Optional[Feedback]:
        """Create new feedback record"""
        try:
            with self.get_session() as session:
                feedback = Feedback(**feedback_data)
                session.add(feedback)
                session.flush()
                return feedback
        except SQLAlchemyError as e:
            logger.error(f"Error creating feedback: {e}")
            return None
    
    def get_feedback_by_prediction(self, prediction_id: str) -> Optional[Feedback]:
        """Get feedback for a specific prediction"""
        try:
            with self.get_session() as session:
                return session.query(Feedback)\
                    .filter(Feedback.prediction_id == prediction_id)\
                    .first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting feedback: {e}")
            return None
    
    # Analytics operations
    def create_network_metrics(self, metrics_data: Dict[str, Any]) -> Optional[NetworkMetrics]:
        """Create network metrics record"""
        try:
            with self.get_session() as session:
                metrics = NetworkMetrics(**metrics_data)
                session.add(metrics)
                session.flush()
                return metrics
        except SQLAlchemyError as e:
            logger.error(f"Error creating network metrics: {e}")
            return None
    
    def get_latest_metrics(self) -> Optional[NetworkMetrics]:
        """Get latest network metrics"""
        try:
            with self.get_session() as session:
                return session.query(NetworkMetrics)\
                    .order_by(NetworkMetrics.created_at.desc())\
                    .first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest metrics: {e}")
            return None
    
    # Model version operations
    def create_model_version(self, version_data: Dict[str, Any]) -> Optional[ModelVersion]:
        """Create new model version"""
        try:
            with self.get_session() as session:
                # Deactivate current active version
                session.query(ModelVersion).filter(ModelVersion.is_active == True).update({"is_active": False})
                
                # Create new version
                version = ModelVersion(**version_data)
                session.add(version)
                session.flush()
                return version
        except SQLAlchemyError as e:
            logger.error(f"Error creating model version: {e}")
            return None
    
    def get_active_model_version(self) -> Optional[ModelVersion]:
        """Get currently active model version"""
        try:
            with self.get_session() as session:
                return session.query(ModelVersion)\
                    .filter(ModelVersion.is_active == True)\
                    .first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active model version: {e}")
            return None
    
    def get_retrain_candidates(self, min_clients: int, min_predictions: int) -> Dict[str, Any]:
        """Get data for retraining decision"""
        try:
            with self.get_session() as session:
                # Count active clients
                client_count = session.query(Client)\
                    .filter(Client.is_active == True)\
                    .count()
                
                # Count recent predictions
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(hours=24)
                prediction_count = session.query(Prediction)\
                    .filter(Prediction.created_at >= cutoff)\
                    .count()
                
                # Get recent predictions for training
                recent_predictions = self.get_recent_predictions(hours=24, limit=10000)
                
                return {
                    "client_count": client_count,
                    "prediction_count": prediction_count,
                    "recent_predictions": recent_predictions,
                    "should_retrain": client_count >= min_clients and prediction_count >= min_predictions
                }
        except SQLAlchemyError as e:
            logger.error(f"Error getting retrain candidates: {e}")
            return {"client_count": 0, "prediction_count": 0, "recent_predictions": [], "should_retrain": False}
    
    def delete(self, model_class, record_id: str) -> bool:
        """Delete a record by ID"""
        try:
            with self.get_session() as session:
                record = session.query(model_class).filter(model_class.id == record_id).first()
                if record:
                    session.delete(record)
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting record: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()
