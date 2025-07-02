
import json
import pika
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import os
from contextlib import contextmanager
from mq.enums import *
from bson import ObjectId



logger = logging.getLogger(__name__)


class RabbitMQService:
    

    def __init__(self):
        self.connection_params = pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST', 'localhost'),
            port=int(os.getenv('RABBITMQ_PORT', 5672)),
            virtual_host=os.getenv('RABBITMQ_VHOST', '/'),
            credentials=pika.PlainCredentials(
                username=os.getenv('RABBITMQ_USER', 'guest'),
                password=os.getenv('RABBITMQ_PASS', 'guest')
            ),
            connection_attempts=3,
            retry_delay=2
        )
        self.exchange = os.getenv('RABBITMQ_EXCHANGE', 'app_exchange')
        self._connection = None
        self._channel = None
    


    @contextmanager
    def get_channel(self):
        try:
            if not self._connection or self._connection.is_closed:
                self._connection = pika.BlockingConnection(self.connection_params)
                self._channel = self._connection.channel()
                


                self._channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type='direct',
                    durable=True
                )
            
            yield self._channel
            
        except Exception as e:
            logger.error(f"RabbitMQ connection error: {str(e)}")
            raise
        finally:
            pass
    
    def send_message(self, queue_name: str, data: Dict[str, Any]) -> bool:
        try:
            with self.get_channel() as channel:
                channel.queue_declare(queue=queue_name, durable=True)
                
                channel.queue_bind(
                    exchange=self.exchange,
                    queue=queue_name,
                    routing_key=queue_name
                )
                
                channel.basic_publish(
                    exchange=self.exchange,
                    routing_key=queue_name,
                    body=json.dumps(data, ensure_ascii=False),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json',
                        timestamp=int(datetime.utcnow().timestamp())
                    )
                )
                
                logger.info(f"Message sent successfully to queue: {queue_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send message to {queue_name}: {str(e)}")
            return False
    
    def send_media_create(self, media_id: str, media_type: MediaType, 
                         url: str, source: MediaSource,
                         width: Optional[int] = None, 
                         height: Optional[int] = None) -> bool:
        message = MediaCreateMessage(
            mediaId=media_id,
            type=media_type.value,
            url=url,
            source=source.value,
            width=width,
            height=height
        )
        
        data = {k: v for k, v in asdict(message).items() if v is not None}
        
        return self.send_message(queue_name=QueueName.MEDIA_CREATE.value, data=data)
    



    def send_dish_collect(self, user_id: str, dish_id: str, 
                         state: CollectState) -> bool:
        message = DishCollectMessage(
            userId=user_id,
            dishId=dish_id,
            state=state.value
        )
        
        return self.send_message(QueueName.DISH_COLLECT.value, asdict(message))
    

    def send_taste_create(self, taste_id: str, user_id: str, dish_id: str,
                         comment: str, recommend_state: RecommendState,
                         media_ids: Optional[List[str]] = None) -> bool:
        message = TasteCreateMessage(
            id=taste_id,
            userId=user_id,
            dishId=dish_id,
            comment=comment,
            recommendState=recommend_state.value,
            mediaIds=media_ids
        )
        
        data = {k: v for k, v in asdict(message).items() if v is not None}
        
        return self.send_message(QueueName.TASTE_CREATE.value, data)
    
    def send_taste_add_dish(self, id: str, user_id: str, merchant_id: str, name: str,
                           price: Optional[int] = None,
                           media_ids: Optional[List[str]] = None,
                           description: Optional[str] = None,
                           characteristic: Optional[str] = None) -> bool:
        message = TasteAddDishMessage(
            id=id,
            userId=user_id,
            merchantID=merchant_id,
            name=name,
            price=price,
            mediaIds=media_ids,
            description=description,
            characteristic=characteristic
        )
        
        data = {k: v for k, v in asdict(message).items() if v is not None}
        
        return self.send_message(QueueName.TASTE_ADD_DISH.value, data)
    
    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed")
    
    def __del__(self):
        self.close()


# _rabbitmq_service = None


# def get_rabbitmq_service() -> RabbitMQService:
#     global _rabbitmq_service
#     if _rabbitmq_service is None:
#         _rabbitmq_service = RabbitMQService()
#     return _rabbitmq_service


# #helper funcs
# def send_media_create_event(media_id: str, media_type: str, url: str, 
#                            source: str = "INTERNET", **kwargs) -> bool:
#     """
#     Convenience function to send media create event
    
#     Args:
#         media_id: Media ID
#         media_type: IMAGE or VIDEO
#         url: Media URL
#         source: INTERNET, USER_AVATAR, or VOLCENGINE
#         **kwargs: Optional width, height
#     """
#     try:
#         service = get_rabbitmq_service()
#         return service.send_media_create(
#             media_id=media_id,
#             media_type=MediaType(media_type),
#             url=url,
#             source=MediaSource(source),
#             width=kwargs.get('width'),
#             height=kwargs.get('height')
#         )
#     except Exception as e:
#         logger.error(f"Failed to send media create event: {str(e)}")
#         return False


# def send_dish_collect_event(user_id: str, dish_id: str, is_collect: bool) -> bool:
#     """
#     Convenience function to send dish collect event
    
#     Args:
#         user_id: User ID
#         dish_id: Dish ID
#         is_collect: True for collect, False for uncollect
#     """
#     try:
#         service = get_rabbitmq_service()
#         state = CollectState.COLLECT if is_collect else CollectState.UNCOLLECT
#         return service.send_dish_collect(user_id, dish_id, state)
#     except Exception as e:
#         logger.error(f"Failed to send dish collect event: {str(e)}")
#         return False


# def send_taste_create_event(taste_id: str, user_id: str, dish_id: str,
#                            comment: str = "", recommend_state: int = 1,
#                            media_ids: Optional[List[str]] = None) -> bool:
#     """
#     Convenience function to send taste create event
    
#     Args:
#         taste_id: Taste ID
#         user_id: User ID
#         dish_id: Dish ID
#         comment: Comment text
#         recommend_state: 0=default, 1=recommend, 2=not recommend
#         media_ids: Optional list of media IDs
#     """
#     try:
#         service = get_rabbitmq_service()
#         return service.send_taste_create(
#             taste_id=taste_id,
#             user_id=user_id,
#             dish_id=dish_id,
#             comment=comment,
#             recommend_state=RecommendState(recommend_state),
#             media_ids=media_ids
#         )
#     except Exception as e:
#         logger.error(f"Failed to send taste create event: {str(e)}")
#         return False