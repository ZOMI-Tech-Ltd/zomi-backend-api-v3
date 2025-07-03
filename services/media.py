import os
import uuid
import boto3
import requests
import logging
from io import BytesIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, BinaryIO
from PIL import Image, UnidentifiedImageError
import numpy as np
from blurhash import encode
from werkzeug.datastructures import FileStorage
from extensions import db
from models.media import Media
from utils.response_utils import create_response
from sqlalchemy import and_
import warnings
from services.rabbitmq_service import RabbitMQService
from mq.enums import *
from bson import ObjectId
from services.aws import AWSService

logger = logging.getLogger(__name__)


class MediaService:
    
    @staticmethod
    def _get_rabbitmq_service():
        return RabbitMQService()


    @staticmethod
    def _send_media_create_event(media: Media):
        try:
            rabbitmq = MediaService._get_rabbitmq_service()

            media_type = MediaType.VIDEO if media.media_type.upper() == 'VIDEO' else MediaType.IMAGE


            source_map = {
                'INTERNET': MediaSource.INTERNET,
                'USER_AVARTAR' : MediaSource.USER_AVATAR,
                'VOLCENGINE' : MediaSource.VOLCENGINE
    
            }

            media_source = source_map.get(media.source, MediaSource.INTERNET)


            #send message
            success = rabbitmq.send_media_create(
                media_id= media._id,
                media_type = media_type,
                url = media.url,
                source= media_source,
                width = media.width,
                height = media.height
            )
            return success
        except Exception as e:
            logger.error(f"error sending media create event: {str(e)}")
            return False

    @staticmethod
    def add_media(user_id: str, 
                  url: str,
                   media_type: str, 
                   width: int, 
                   height: int, 
                   blur_hash: str, 
                   source: str) -> dict:
        
        try:
            media = Media(
                _id=str(ObjectId()),
                url=url,
                media_type=media_type,
                width=width,    
                height=height,
                blurHash=blur_hash,
                source=source,
                userId=user_id, 
                blurHashAt=datetime.utcnow()
            )
            db.session.add(media)
            db.session.flush()
            
            MediaService._send_media_create_event(media)

            db.session.commit()

            return create_response(
                code=0,
                data=media.to_dict(include_meta=True),
                message="Media added successfully"
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding media: {str(e)}")
            return create_response(code=200, message=f"Failed to add media: {str(e)}")

    # @staticmethod
    # def generate_blurhash_from_image(image: Image.Image) -> str:
    #     try:
    #         # Ensure we have a PIL Image object

    #         if image.mode != 'RGB':
    #             image = image.convert('RGB')
            
    #         # Resize for blurhash
    #         max_size = (128, 128)
    #         if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
    #             image.thumbnail(max_size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            
            
    #         # Generate blurhash
    #         x_components = 4
    #         y_components = 3
    #         blurhash = encode(image, x_components, y_components)
            


    #         return blurhash
    #     except Exception as e:
    #         logger.error(f"Error generating blurhash: {str(e)}")
    #         return None
    
    # @staticmethod
    # def generate_blurhash_from_url(image_url: str, max_retries: int = 3) -> tuple:
    #     retries = 0
    #     while retries < max_retries:
    #         try:
    #             response = requests.get(image_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})

    #             if response.status_code == 200:
    #                 image = Image.open(BytesIO(response.content)).convert("RGB")
    #                 blurhash = MediaService.generate_blurhash_from_image(image)
    #                 return blurhash, image
                

    #             else:
    #                 logger.warning(f"HTTP error: {response.status_code} for URL {image_url}")

    #         except (requests.RequestException, UnidentifiedImageError) as e:
    #             logger.error(f"Error fetching or processing image from URL {image_url}: {e}")
            
    #         retries += 1
    #         if retries < max_retries:
    #             logger.info(f"Retrying... ({retries}/{max_retries})")
        
    #     logger.error(f"Failed to process image after {max_retries} retries.")
    #     return None, None
    
    # @staticmethod
    # def compress_image(data: bytes) -> bytes:

    #     try:
    #         image = Image.open(BytesIO(data))
            
            
    #         if image.mode in ('RGBA', 'P'):
    #             image = image.convert('RGB')
            
    #         quality = 85
    #         buf = BytesIO()
    #         image.save(buf, format='JPEG', quality=quality)
    #         out = buf.getvalue()
            
    #         #reduce quality
    #         while len(out) > MAX_FILE_SIZE and quality > 10:
    #             quality -= 5
    #             buf = BytesIO()
    #             image.save(buf, format='JPEG', quality=quality)
    #             out = buf.getvalue()
            
    #         return out
    #     except Exception as e:
    #         logger.error(f"Error compressing image: {str(e)}")
    #         raise
    
    # @staticmethod
    # def upload_to_s3(file_data: bytes, content_type: str = 'image/jpeg') -> str:
    #     try:
    #         #unique key
    #         key = f"zomi-dishes/{datetime.now().strftime('%Y%m%d')}/{ObjectId()}.jpeg"
            
    #         #upload
    #         s3_client.upload_fileobj(
    #             BytesIO(file_data),
    #             AWS_BUCKET,
    #             key,
    #             ExtraArgs={'ContentType': content_type}
    #         )
            
    #         #cloudfront url
    #         return f"{CLOUDFRONT_PREFIX}{key}"
    #     except Exception as e:
    #         logger.error(f"Error uploading to S3: {str(e)}")
    #         raise
    
    # @staticmethod
    # def process_image_data(data: bytes) -> dict:
    #     try:
    #         # Validate image data
    #         if not data:
    #             raise ValueError("Empty image data")
            
    #         # Create BytesIO object and ensure position is at start
    #         img_buffer = BytesIO(data)
    #         img_buffer.seek(0)
            
    #         # Try to open image
    #         try:
    #             img = Image.open(img_buffer)
    #             # Verify image is valid by loading it
    #             img.verify()
                
    #             # Need to reopen after verify
    #             img_buffer.seek(0)
    #             img = Image.open(img_buffer)
    #         except (UnidentifiedImageError, IOError) as e:
    #             logger.error(f"Invalid image format: {str(e)}")
    #             raise ValueError(f"Invalid image format: {str(e)}")
            
    #         # Get original format
    #         original_format = img.format or 'JPEG'
            
    #         # Get dimensions
    #         width, height = img.size
            
    #         # Convert to RGB if necessary (for blurhash and JPEG save)
    #         if img.mode not in ('RGB', 'L'):
    #             img = img.convert('RGB')
            
    #         # Check if compression is needed
    #         if len(data) > MAX_FILE_SIZE:
    #             warnings.warn(f"Image too large ({len(data)} bytes), compressing...", stacklevel=2)
    #             # Compress image
    #             output_buffer = BytesIO()
    #             img.save(output_buffer, format='JPEG', quality=85, optimize=True)
    #             data = output_buffer.getvalue()
            
    #         # Generate blurhash
    #         blurhash = MediaService.generate_blurhash_from_image(img)
            
    #         return {
    #             'data': data,
    #             'width': width,
    #             'height': height,
    #             'blur_hash': blurhash,
    #             'file_size': len(data),
    #             'format': original_format
    #         }
    #     except Exception as e:
    #         logger.error(f"Error processing image: {str(e)}")
    #         raise


    # @staticmethod
    # def upload_media(file: FileStorage, user_id: str, media_type: str = 'image', source = str) -> dict:
    #     try:
    #         #read file
    #         file_data = file.read()
    #         filename = file.filename
            
    #         #process
    #         processed = MediaService.process_image_data(file_data)
            
    #         #upload
    #         url = MediaService.upload_to_s3(processed['data'])
            
    #         print(url)
    #         #media record
    #         media = Media(
    #             _id=str(ObjectId()),
    #             url=url,
    #             source = source,
    #             width=processed['width'],
    #             height=processed['height'],
    #             blur_hash=processed['blur_hash'],
    #             file_size=processed['file_size'],
    #             userId=user_id,
    #             media_type = media_type.upper(),
    #             blurHashAt = datetime.utcnow()

    #         )
            
    #         db.session.add(media)
    #         db.session.flush()
            
    #         MediaService._send_media_create_event(media)

    #         db.session.commit()


    #         return create_response(
    #             code=0,
    #             data={
    #                 '_id': media._id,
    #                 'pg_id':media.pg_id,
    #                 'url': media.url,
    #                 'media_type': media.media_type,
    #                 'width': media.width,
    #                 'height': media.height,
    #                 'blur_hash': media.blurHash
    #             },
    #             message="Media uploaded successfully"
    #         )
            
    #     except Exception as e:
    #         db.session.rollback()
    #         logger.error(f"Error uploading media: {str(e)}")
    #         return create_response(code=500, message=f"Failed to upload media: {str(e)}")
    
    # @staticmethod
    # def batch_upload_media(files: List[FileStorage], user_id: str) -> dict:

    #     results = {
    #         'successful': [],
    #         'failed': []
    #     }
        
    #     for file in files:
    #         result = MediaService.upload_media(file, user_id)
    #         if result['code'] == 0:
    #             results['successful'].append(result['data'])
    #         else:
    #             results['failed'].append({
    #                 'filename': file.filename,
    #                 'error': result['msg']
    #             })
        
    #     return create_response(
    #         code=0,
    #         data=results,
    #         message=f"Processed {len(files)} files: {len(results['successful'])} successful, {len(results['failed'])} failed"
    #     )
    
    @staticmethod
    def import_from_url(source_url: str, user_id: str, source:str = "INTERNET") -> dict:
        try:

            #download
            response = requests.get(source_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            data = response.content
            
            #process
            processed = MediaService.process_image_data(data)
            
            #cloudfront url
            if source_url.startswith(CLOUDFRONT_PREFIX):
                url = source_url
            else:
                url = MediaService.upload_to_s3(processed['data'])
            
            print(url)

            media = Media(
                _id=str(ObjectId()),
                url=url,
                media_type='IMAGE',
                width=processed['width'],
                height=processed['height'],
                blurHash=processed['blur_hash'],
                userId=user_id,
                source = source,
                blurHashAt=datetime.utcnow()
            )
            db.session.add(media)
            db.session.flush()
            
            MediaService._send_media_create_event(media)

            db.session.commit()

            return create_response(
                code=0,
                data={
                    '_id': media._id,
                    'url': media.url,
                    'pg_id': media.pg_id,
                    'width': media.width,
                    'height': media.height,
                    'duration': media.duration,
                    'media_type': media.media_type,
                    'source': media.source
                },
                message="Media imported successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing media from URL: {str(e)}")
            return create_response(code=500, message=f"Failed to import media: {str(e)}")
    
    # @staticmethod
    # def batch_import_from_urls(urls: List[str], user_id: str) -> dict:

    #     results = {
    #         'successful': [],
    #         'failed': []
    #     }
        
    #     def process_url(url):
    #         return MediaService.import_from_url(url, user_id)
        
    #     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    #         future_to_url = {executor.submit(process_url, url): url for url in urls}
            
    #         for future in as_completed(future_to_url):
    #             url = future_to_url[future]
    #             try:
    #                 result = future.result()
    #                 if result['code'] == 0:
    #                     results['successful'].append(result['data'])
    #                 else:
    #                     results['failed'].append({
    #                         'url': url,
    #                         'error': result['msg']
    #                     })
    #             except Exception as e:
    #                 results['failed'].append({
    #                     'url': url,
    #                     'error': str(e)
    #                 })
        
    #     return create_response(
    #         code=0,
    #         data=results,
    #         message=f"Processed {len(urls)} URLs: {len(results['successful'])} successful, {len(results['failed'])} failed"
    #     )
    
    @staticmethod
    def get_media_by_id(media_id: str) -> dict:

        try:
            media = Media.query.filter_by(_id=media_id).first()
            if not media:
                return create_response(code=200, message="Media not found")
            
            return create_response(
                code=0,
                data= media.to_dict(include_meta=True),
                message="Success"
            )
        except Exception as e:
            logger.error(f"Error getting media: {str(e)}")
            return create_response(code=500, message=f"Failed to get media: {str(e)}")
    
    
    # @staticmethod
    # def _flush_media_batch(items: List[dict]):
    #     """
    #     Batch update media records
    #     """
    #     for item in items:
    #         try:
    #             media = item['media']
    #             media.url = item['url']
    #             media.width = item['width']
    #             media.height = item['height']
    #             media.blur_hash = item['blur_hash']
    #             media.file_size = item['file_size']
    #             media.updated_at = datetime.utcnow()
    #         except Exception as e:
    #             logger.error(f"Failed to update media {item['media']._id}: {str(e)}")
        
    #     try:
    #         db.session.commit()
    #     except Exception as e:
    #         db.session.rollback()
    #         logger.error(f"Failed to commit batch: {str(e)}")