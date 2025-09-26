"""
Real Model Retrainer - Network Effects Implementation
Retreina modelo com dados reais dos clientes
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import joblib
import os

from .database import db_manager
from .cache import cache_manager
from .queue import queue_manager
from .config import config

logger = logging.getLogger(__name__)

class NetworkEffectsRetrainer:
    """Real model retrainer using client data for network effects"""
    
    def __init__(self, base_model_path: str = "models/"):
        self.base_model_path = base_model_path
        self.current_model = None
        self.current_version = "1.0.0"
        
        # Ensure model directory exists
        os.makedirs(self.base_model_path, exist_ok=True)
    
    def should_retrain(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if model should be retrained based on network effects"""
        try:
            # Get retrain candidates from database
            candidates = db_manager.get_retrain_candidates(
                config.min_clients_for_retrain,
                config.min_predictions_for_retrain
            )
            
            # Check cache for recent retrain status
            cached_status = cache_manager.get_retrain_status()
            if cached_status:
                last_retrain = datetime.fromisoformat(cached_status.get("last_retrain", "1970-01-01"))
                hours_since_retrain = (datetime.utcnow() - last_retrain).total_seconds() / 3600
                
                if hours_since_retrain < config.retrain_frequency_hours:
                    return False, {"reason": "Too soon since last retrain", "hours_since": hours_since_retrain}
            
            should_retrain = candidates["should_retrain"]
            
            return should_retrain, {
                "client_count": candidates["client_count"],
                "prediction_count": candidates["prediction_count"],
                "recent_predictions": len(candidates["recent_predictions"]),
                "min_clients_required": config.min_clients_for_retrain,
                "min_predictions_required": config.min_predictions_for_retrain
            }
            
        except Exception as e:
            logger.error(f"Error checking retrain conditions: {e}")
            return False, {"error": str(e)}
    
    def prepare_training_data(self, predictions: List[Any]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from client predictions"""
        try:
            if not predictions:
                return pd.DataFrame(), pd.Series()
            
            # Convert predictions to DataFrame
            data = []
            for pred in predictions:
                data.append({
                    'fed_rate': pred.fed_rate,
                    'selic_rate': pred.selic_rate,
                    'spillover': pred.spillover_prediction,
                    'uncertainty': pred.uncertainty,
                    'is_outlier': pred.is_outlier,
                    'client_id': pred.client_id,
                    'created_at': pred.created_at
                })
            
            df = pd.DataFrame(data)
            
            # Prepare features (X) and target (y)
            X = df[['fed_rate', 'selic_rate']].copy()
            y = df['spillover'].copy()
            
            # Add derived features for better learning
            X['fed_selic_ratio'] = X['fed_rate'] / (X['selic_rate'] + 1e-8)
            X['rate_diff'] = X['selic_rate'] - X['fed_rate']
            X['rate_sum'] = X['fed_rate'] + X['selic_rate']
            
            # Add time-based features
            df['created_at'] = pd.to_datetime(df['created_at'])
            X['hour_of_day'] = df['created_at'].dt.hour
            X['day_of_week'] = df['created_at'].dt.dayofweek
            X['month'] = df['created_at'].dt.month
            
            logger.info(f"Prepared training data: {len(X)} samples, {X.shape[1]} features")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return pd.DataFrame(), pd.Series()
    
    def retrain_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Retrain the hybrid model with new data"""
        try:
            from sklearn.model_selection import train_test_split
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.metrics import mean_squared_error, r2_score
            from sklearn.preprocessing import StandardScaler
            import joblib
            
            if len(X) < 10:
                return {"success": False, "error": "Insufficient data for retraining"}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train new model (simplified for demo - in production use your hybrid model)
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            # Generate new version
            new_version = f"1.{int(datetime.utcnow().timestamp())}"
            
            # Save model and scaler
            model_path = os.path.join(self.base_model_path, f"model_{new_version}.joblib")
            scaler_path = os.path.join(self.base_model_path, f"scaler_{new_version}.joblib")
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Update current model
            self.current_model = model
            self.current_version = new_version
            
            # Create model version record
            version_data = {
                "version": new_version,
                "model_type": "RandomForest_NetworkEffects",
                "accuracy_score": r2,
                "r2_score": r2,
                "rmse_score": rmse,
                "training_samples": len(X),
                "training_clients": len(set([p.client_id for p in predictions])),
                "training_period_start": min([p.created_at for p in predictions]),
                "training_period_end": max([p.created_at for p in predictions]),
                "is_active": True,
                "is_retrained": True,
                "model_metadata": {
                    "features": list(X.columns),
                    "mse": mse,
                    "rmse": rmse,
                    "r2": r2
                },
                "retrain_reason": "Network effects data accumulation"
            }
            
            db_manager.create_model_version(version_data)
            
            # Cache new model version
            cache_manager.cache_model_version(new_version, version_data)
            
            # Invalidate old caches
            cache_manager.invalidate_network_cache()
            
            logger.info(f"Model retrained successfully: {new_version}")
            logger.info(f"R² Score: {r2:.4f}, RMSE: {rmse:.4f}")
            
            return {
                "success": True,
                "version": new_version,
                "r2_score": r2,
                "rmse": rmse,
                "training_samples": len(X),
                "model_path": model_path
            }
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            return {"success": False, "error": str(e)}
    
    def process_retrain_request(self, retrain_data: Dict[str, Any]) -> bool:
        """Process retraining request from queue"""
        try:
            logger.info("Processing retrain request...")
            
            # Check if retrain is needed
            should_retrain, info = self.should_retrain()
            if not should_retrain:
                logger.info(f"Retrain not needed: {info}")
                return True
            
            # Get recent predictions for training
            predictions = db_manager.get_recent_predictions(hours=24, limit=10000)
            if not predictions:
                logger.warning("No recent predictions found for retraining")
                return True
            
            # Prepare training data
            X, y = self.prepare_training_data(predictions)
            if X.empty:
                logger.warning("No valid training data prepared")
                return True
            
            # Retrain model
            result = self.retrain_model(X, y)
            
            if result["success"]:
                # Update retrain status in cache
                cache_manager.cache_retrain_status({
                    "last_retrain": datetime.utcnow().isoformat(),
                    "version": result["version"],
                    "r2_score": result["r2_score"],
                    "training_samples": result["training_samples"]
                })
                
                # Publish analytics update
                queue_manager.publish_analytics_update({
                    "type": "model_retrained",
                    "version": result["version"],
                    "r2_score": result["r2_score"],
                    "training_samples": result["training_samples"]
                })
                
                logger.info("Retrain request processed successfully")
                return True
            else:
                logger.error(f"Retrain failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing retrain request: {e}")
            return False
    
    def get_model_for_prediction(self) -> Optional[Any]:
        """Get current model for predictions"""
        try:
            if self.current_model is not None:
                return self.current_model
            
            # Try to load from database
            active_version = db_manager.get_active_model_version()
            if active_version:
                model_path = os.path.join(self.base_model_path, f"model_{active_version.version}.joblib")
                if os.path.exists(model_path):
                    self.current_model = joblib.load(model_path)
                    self.current_version = active_version.version
                    return self.current_model
            
            logger.warning("No model available for prediction")
            return None
            
        except Exception as e:
            logger.error(f"Error getting model for prediction: {e}")
            return None
    
    def predict_with_network_effects(self, fed_rate: float, selic_rate: float) -> Dict[str, Any]:
        """Make prediction using current model with network effects"""
        try:
            model = self.get_model_for_prediction()
            if model is None:
                return {"error": "No model available"}
            
            # Prepare input features
            X = pd.DataFrame({
                'fed_rate': [fed_rate],
                'selic_rate': [selic_rate],
                'fed_selic_ratio': [fed_rate / (selic_rate + 1e-8)],
                'rate_diff': [selic_rate - fed_rate],
                'rate_sum': [fed_rate + selic_rate],
                'hour_of_day': [datetime.utcnow().hour],
                'day_of_week': [datetime.utcnow().weekday()],
                'month': [datetime.utcnow().month]
            })
            
            # Load scaler
            scaler_path = os.path.join(self.base_model_path, f"scaler_{self.current_version}.joblib")
            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
                X_scaled = scaler.transform(X)
            else:
                X_scaled = X.values
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            
            # Calculate uncertainty (simplified)
            uncertainty = 0.05  # In production, use proper uncertainty quantification
            
            return {
                "prediction": float(prediction),
                "uncertainty": uncertainty,
                "model_version": self.current_version,
                "is_outlier": abs(prediction) > 2.0,
                "high_uncertainty": uncertainty > 0.1,
                "network_effects_enabled": True
            }
            
        except Exception as e:
            logger.error(f"Error in network effects prediction: {e}")
            return {"error": str(e)}

# Global retrainer instance
retrainer = NetworkEffectsRetrainer()
