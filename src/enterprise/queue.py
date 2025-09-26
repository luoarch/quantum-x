"""
RabbitMQ Queue Manager - Asynchronous Processing
"""
import pika
import json
from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime
import threading
import time

from .config import config

logger = logging.getLogger(__name__)

class QueueManager:
    """RabbitMQ-based queue manager for asynchronous processing"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self._initialize()
    
    def _initialize(self):
        """Initialize RabbitMQ connection and channels"""
        try:
            # Create connection (use localhost with default credentials)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            
            # Create channel
            self.channel = self.connection.channel()
            
            # Declare queues
            self._declare_queues()
            
            logger.info("✅ RabbitMQ queue manager initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ RabbitMQ initialization failed: {e}")
            logger.warning("⚠️ System will work without RabbitMQ (no async processing)")
            self.connection = None
            self.channel = None
    
    def _declare_queues(self):
        """Declare all required queues"""
        queues = [
            config.prediction_queue,
            config.retrain_queue,
            "network_analytics",
            "model_deployment",
            "client_notifications"
        ]
        
        for queue in queues:
            self.channel.queue_declare(
                queue=queue,
                durable=True,  # Survive broker restarts
                arguments={
                    'x-message-ttl': 3600000,  # 1 hour TTL
                    'x-max-retries': 3
                }
            )
    
    def publish_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """Publish prediction for processing"""
        if not self.connection or not self.channel:
            logger.warning("RabbitMQ not available, skipping prediction publish")
            return False
            
        try:
            message = {
                "type": "prediction",
                "data": prediction_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=config.prediction_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    priority=5  # Medium priority
                )
            )
            
            logger.info(f"Published prediction: {prediction_data.get('prediction_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing prediction: {e}")
            return False
    
    def publish_retrain_request(self, retrain_data: Dict[str, Any]) -> bool:
        """Publish retraining request"""
        if not self.connection or not self.channel:
            logger.warning("RabbitMQ not available, skipping retrain request")
            return False
            
        try:
            message = {
                "type": "retrain",
                "data": retrain_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key=config.retrain_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    priority=10  # High priority
                )
            )
            
            logger.info("Published retrain request")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing retrain request: {e}")
            return False
    
    def publish_analytics_update(self, analytics_data: Dict[str, Any]) -> bool:
        """Publish analytics update"""
        try:
            message = {
                "type": "analytics_update",
                "data": analytics_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key="network_analytics",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    priority=3  # Low priority
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error publishing analytics update: {e}")
            return False
    
    def consume_predictions(self, callback: Callable[[Dict[str, Any]], bool]):
        """Consume prediction messages"""
        def process_message(ch, method, properties, body):
            try:
                message = json.loads(body)
                success = callback(message.get("data", {}))
                
                if success:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    
            except Exception as e:
                logger.error(f"Error processing prediction message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_consume(
            queue=config.prediction_queue,
            on_message_callback=process_message
        )
    
    def consume_retrain_requests(self, callback: Callable[[Dict[str, Any]], bool]):
        """Consume retraining requests"""
        def process_message(ch, method, properties, body):
            try:
                message = json.loads(body)
                success = callback(message.get("data", {}))
                
                if success:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    
            except Exception as e:
                logger.error(f"Error processing retrain message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_consume(
            queue=config.retrain_queue,
            on_message_callback=process_message
        )
    
    def start_consuming(self, queues: list[str] = None):
        """Start consuming messages from specified queues"""
        if queues is None:
            queues = [config.prediction_queue, config.retrain_queue]
        
        try:
            logger.info(f"Starting to consume from queues: {queues}")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error in consuming: {e}")
    
    def stop_consuming(self):
        """Stop consuming messages"""
        try:
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Error stopping consumer: {e}")
    
    def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get queue information"""
        try:
            method = self.channel.queue_declare(queue=queue_name, passive=True)
            return {
                "queue": queue_name,
                "message_count": method.method.message_count,
                "consumer_count": method.method.consumer_count
            }
        except Exception as e:
            logger.error(f"Error getting queue info: {e}")
            return {"queue": queue_name, "message_count": 0, "consumer_count": 0}
    
    def purge_queue(self, queue_name: str) -> bool:
        """Purge all messages from queue"""
        try:
            self.channel.queue_purge(queue=queue_name)
            logger.info(f"Purged queue: {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Error purging queue: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check RabbitMQ connectivity"""
        try:
            return self.connection.is_open
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return False
    
    def close(self):
        """Close connections"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error(f"Error closing connections: {e}")

# Global queue manager instance
queue_manager = QueueManager()
