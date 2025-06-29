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

logger = logging.getLogger(__name__)

#default configs
MAX_FILE_SIZE = 15 * 1024 * 1024  # 5 MB
MAX_WORKERS = 8
BATCH_SIZE = 128
CLOUDFRONT_PREFIX = os.getenv('CLOUDFRONT_URL', '')
AWS_BUCKET = os.getenv('AWS_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-1')


s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name=AWS_REGION
)


class MediaService:
    
    @staticmethod
    def generate_blurhash_from_image(image: Image.Image) -> str:
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            #resize
            max_size = (128, 128)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size)
            
            #blurhash
            image_np = np.array(image)
            x_components = 4
            y_components = 3
            blurhash = encode(image_np, x_components, y_components)
            
            return blurhash
        except Exception as e:
            logger.error(f"Error generating blurhash: {str(e)}")
            return None
    
    @staticmethod
    def generate_blurhash_from_url(image_url: str, max_retries: int = 3) -> tuple:

        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(image_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content)).convert("RGB")
                    blurhash = MediaService.generate_blurhash_from_image(image)
                    return blurhash, image
                else:
                    logger.warning(f"HTTP error: {response.status_code} for URL {image_url}")
            except (requests.RequestException, UnidentifiedImageError) as e:
                logger.error(f"Error fetching or processing image from URL {image_url}: {e}")
            
            retries += 1
            if retries < max_retries:
                logger.info(f"Retrying... ({retries}/{max_retries})")
        
        logger.error(f"Failed to process image after {max_retries} retries.")
        return None, None
    
    @staticmethod
    def compress_image(data: bytes) -> bytes:

        try:
            image = Image.open(BytesIO(data))
            
            
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            quality = 85
            buf = BytesIO()
            image.save(buf, format='JPEG', quality=quality)
            out = buf.getvalue()
            
            #reduce quality
            while len(out) > MAX_FILE_SIZE and quality > 10:
                quality -= 5
                buf = BytesIO()
                image.save(buf, format='JPEG', quality=quality)
                out = buf.getvalue()
            
            return out
        except Exception as e:
            logger.error(f"Error compressing image: {str(e)}")
            raise
    
    @staticmethod
    def upload_to_s3(file_data: bytes, content_type: str = 'image/jpeg') -> str:
        try:
            #unique key
            key = f"menu-media/{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4().hex}.jpeg"
            
            #upload
            s3_client.upload_fileobj(
                BytesIO(file_data),
                AWS_BUCKET,
                key,
                ExtraArgs={'ContentType': content_type}
            )
            
            #cloudfront url
            return f"{CLOUDFRONT_PREFIX}{key}"
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise
    
    @staticmethod
    def process_image_data(data: bytes, source_url: Optional[str] = None) -> dict:
        try:
            #compress
            if len(data) > MAX_FILE_SIZE:
                warnings.warn(f"Image too large ({len(data)} bytes), compressing...", stacklevel=2)
                data = MediaService.compress_image(data)
            
            #dimensions
            img = Image.open(BytesIO(data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            width, height = img.size
            
            #blurhash
            blurhash = MediaService.generate_blurhash_from_image(img)
            
            return {
                'data': data,
                'width': width,
                'height': height,
                'blur_hash': blurhash,
                'file_size': len(data)
            }
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise
    
    @staticmethod
    def upload_media(file: FileStorage, user_id: str, media_type: str = 'image') -> dict:
        try:
            #read file
            file_data = file.read()
            filename = file.filename
            
            #process
            processed = MediaService.process_image_data(file_data)
            
            #upload
            url = MediaService.upload_to_s3(processed['data'])
            
            #media record
            media = Media(
                _id=str(uuid.uuid4()),
                url=url,
                source_url=None,
                type=media_type,
                width=processed['width'],
                height=processed['height'],
                blur_hash=processed['blur_hash'],
                file_size=processed['file_size'],
                uploaded_by=user_id,
                original_filename=filename
            )
            
            db.session.add(media)
            db.session.commit()
            
            return create_response(
                code=0,
                data={
                    '_id': media._id,
                    'url': media.url,
                    'type': media.type,
                    'width': media.width,
                    'height': media.height,
                    'blur_hash': media.blur_hash,
                    'file_size': media.file_size
                },
                message="Media uploaded successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading media: {str(e)}")
            return create_response(code=500, message=f"Failed to upload media: {str(e)}")
    
    @staticmethod
    def batch_upload_media(files: List[FileStorage], user_id: str) -> dict:

        results = {
            'successful': [],
            'failed': []
        }
        
        for file in files:
            result = MediaService.upload_media(file, user_id)
            if result['code'] == 0:
                results['successful'].append(result['data'])
            else:
                results['failed'].append({
                    'filename': file.filename,
                    'error': result['msg']
                })
        
        return create_response(
            code=0,
            data=results,
            message=f"Processed {len(files)} files: {len(results['successful'])} successful, {len(results['failed'])} failed"
        )
    
    @staticmethod
    def import_from_url(source_url: str, user_id: str) -> dict:
        try:

            #download
            response = requests.get(source_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            data = response.content
            
            #process
            processed = MediaService.process_image_data(data, source_url)
            
            #cloudfront url
            if source_url.startswith(CLOUDFRONT_PREFIX):
                url = source_url
            else:
                url = MediaService.upload_to_s3(processed['data'])
            

            media = Media(
                _id=str(uuid.uuid4()),
                url=url,
                source_url=source_url,
                type='image',
                width=processed['width'],
                height=processed['height'],
                blur_hash=processed['blur_hash'],
                file_size=processed['file_size'],
                uploaded_by=user_id,
                blurHashAt=datetime.now()
            )
            db.session.add(media)
            
            db.session.commit()
            
            return create_response(
                code=0,
                data={
                    '_id': media._id,
                    'url': media.url,
                    'type': media.type,
                    'width': media.width,
                    'height': media.height,
                    'blur_hash': media.blur_hash,
                    'file_size': media.file_size
                },
                message="Media imported successfully"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing media from URL: {str(e)}")
            return create_response(code=500, message=f"Failed to import media: {str(e)}")
    
    @staticmethod
    def batch_import_from_urls(urls: List[str], user_id: str) -> dict:
        """
        Batch import media from URLs using thread pool
        """
        results = {
            'successful': [],
            'failed': []
        }
        
        def process_url(url):
            return MediaService.import_from_url(url, user_id)
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(process_url, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result['code'] == 0:
                        results['successful'].append(result['data'])
                    else:
                        results['failed'].append({
                            'url': url,
                            'error': result['msg']
                        })
                except Exception as e:
                    results['failed'].append({
                        'url': url,
                        'error': str(e)
                    })
        
        return create_response(
            code=0,
            data=results,
            message=f"Processed {len(urls)} URLs: {len(results['successful'])} successful, {len(results['failed'])} failed"
        )
    
    @staticmethod
    def get_media_by_id(media_id: str) -> dict:
        """
        Get media by ID
        """
        try:
            media = Media.query.filter_by(_id=media_id).first()
            if not media:
                return create_response(code=404, message="Media not found")
            
            return create_response(
                code=0,
                data={
                    '_id': media._id,
                    'url': media.url,
                    'source_url': media.source_url,
                    'type': media.type,
                    'width': media.width,
                    'height': media.height,
                    'blur_hash': media.blur_hash,
                    'file_size': media.file_size,
                    'created_at': media.created_at.isoformat() if media.created_at else None,
                    'updated_at': media.updated_at.isoformat() if media.updated_at else None
                },
                message="Success"
            )
        except Exception as e:
            logger.error(f"Error getting media: {str(e)}")
            return create_response(code=500, message=f"Failed to get media: {str(e)}")
    
    @staticmethod
    def process_pending_media() -> dict:
        """
        Process all media with source_url but no url (matching the script functionality)
        """
        try:
            # Get pending media
            pending_media = Media.query.filter(
                and_(
                    Media.url.is_(None),
                    Media.source_url.isnot(None),
                    Media.source_url != ''
                )
            ).all()
            
            total = len(pending_media)
            if total == 0:
                return create_response(
                    code=0,
                    data={'processed': 0, 'successful': 0, 'failed': 0},
                    message="No pending media to process"
                )
            
            logger.info(f"Found {total} pending media to process")
            
            successful = 0
            failed = 0
            batch = []
            
            def process_media_item(media):
                try:
                    # Download and process
                    response = requests.get(media.source_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    response.raise_for_status()
                    data = response.content
                    
                    # Process image
                    processed = MediaService.process_image_data(data, media.source_url)
                    
                    # Upload to S3 if not already CloudFront URL
                    if media.source_url.startswith(CLOUDFRONT_PREFIX):
                        url = media.source_url
                    else:
                        url = MediaService.upload_to_s3(processed['data'])
                    
                    return {
                        'media': media,
                        'url': url,
                        'width': processed['width'],
                        'height': processed['height'],
                        'blur_hash': processed['blur_hash'],
                        'file_size': processed['file_size']
                    }
                except Exception as e:
                    logger.error(f"Failed to process media {media._id}: {str(e)}")
                    return None
            
            # Process in batches using thread pool
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(process_media_item, media) for media in pending_media]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        batch.append(result)
                        successful += 1
                    else:
                        failed += 1
                    
                    # Flush batch when it reaches BATCH_SIZE
                    if len(batch) >= BATCH_SIZE:
                        MediaService._flush_media_batch(batch)
                        batch.clear()
                
                # Flush remaining items
                if batch:
                    MediaService._flush_media_batch(batch)
            
            return create_response(
                code=0,
                data={
                    'processed': total,
                    'successful': successful,
                    'failed': failed
                },
                message=f"Processing completed: {successful} successful, {failed} failed"
            )
            
        except Exception as e:
            logger.error(f"Error processing pending media: {str(e)}")
            return create_response(code=500, message=f"Failed to process pending media: {str(e)}")
    
    @staticmethod
    def _flush_media_batch(items: List[dict]):
        """
        Batch update media records
        """
        for item in items:
            try:
                media = item['media']
                media.url = item['url']
                media.width = item['width']
                media.height = item['height']
                media.blur_hash = item['blur_hash']
                media.file_size = item['file_size']
                media.updated_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Failed to update media {item['media']._id}: {str(e)}")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit batch: {str(e)}")