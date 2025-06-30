from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from marshmallow import ValidationError
from services.media import MediaService
from utils.response_utils import create_response
from extensions import db
import logging
import os
import boto3

logger = logging.getLogger(__name__)

media_bp = Blueprint('media', __name__, url_prefix='/v3/media')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mkv',
                       'webm', 'flv', 'wmv', 'm4v', 'm4a', 'aac', 'ogg', 'wav', 'mp3'}

MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 15 * 1024 * 1024))

AWS_BUCKET = os.getenv('AWS_BUCKET_NAME')



s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-west-1')
)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@media_bp.route('/upload', methods=['POST'])
@jwt_required(optional=True)
def upload_media():
    """
    Single media file
    
    Form Data:
        file: The image file to upload
        type: Media type (image/video)
        source: Media source (INTERNET/USER_AVARTAR/VOLCENGINE)
    Returns:
        JSON response with uploaded media data including URL and blurhash
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return create_response(code=200, message="No file provided"), 200
        
        file = request.files['file']
        if file.filename == '':
            return create_response(code=200, message="No file selected"), 200
        
        if not allowed_file(file.filename):
            return create_response(
                code=200, 
                message=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            ), 200
        

        media_type = request.form.get('type', 'image')
        source = request.form.get('source', 'INTERNET')
        

        result = MediaService.upload_media(
            file=file,
            user_id=current_user_id,
            media_type=media_type,
            source = source
        )
        
        if result['code'] == 0:
            return create_response(
                code=0,
                data=result['data'],
                message="Media uploaded successfully"
            ), 200
        else:
            return create_response(
                code=result['code'],
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        return create_response(code=200, message="Failed to upload media"), 200


# @media_bp.route('/batch-upload', methods=['POST'])
# @jwt_required()
# def batch_upload_media():
#     """
#     Multiple media files
    
#     Form Data:
#         files: Multiple image files
        
#     Returns:
#         JSON response with uploaded media data
#     """
#     try:
#         current_user_id = get_jwt_identity()
        
#         files = request.files.getlist('files')
#         if not files:
#             return create_response(code=200, message="No files provided"), 200
        
#         for file in files:
#             if not allowed_file(file.filename):
#                 return create_response(
#                     code=200,
#                     message=f"File '{file.filename}' type not allowed"
#                 ), 200
        
#         source = request.form.get('source', 'INTERNET')


#         result = MediaService.batch_upload_media(
#             files=files,
#             user_id=current_user_id,
#             source = source
#         )
        
#         if result['code'] == 0:
#             return create_response(
#                 code=0,
#                 data=result['data'],
#                 message="Media files uploaded successfully"
#             ), 201
#         else:
#             return create_response(
#                 code=result['code'],
#                 message=result['msg']
#             ), 200
            
#     except Exception as e:
#         logger.error(f"Error batch uploading media: {str(e)}")
#         return create_response(code=200, message="Failed to upload media files"), 200


@media_bp.route('/import-url', methods=['POST'])
@jwt_required(optional=True)
def import_media_from_url():
    """
    Media from URL
    
    Request Body:
        source_url: URL of the image to import
        source: Media source (INTERNET/USER_AVARTAR/VOLCENGINE)
    Returns:
        JSON response with imported media data
    """
    try:
        current_user_id = get_jwt_identity()
        


        data = request.get_json()
        if not data:
            return create_response(code=200, message="Request body is required"), 200
            
        try:
            validated_data = data
        except ValidationError as e:
            return create_response(code=200, message="Validation error", data=e.messages), 200
        
        source = request.form.get('source', 'INTERNET')

        result = MediaService.import_from_url(
            source_url=validated_data['source_url'], 
            user_id=current_user_id,
            source = source
        )
        
        if result['code'] == 0:
            return create_response(
                code=0,
                data=result['data'],
                message="Media imported successfully"
            ), 200
        else:
            return create_response(
                code=result['code'],
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error importing media from URL: {str(e)}")
        return create_response(code=200, message="Failed to import media"), 200


# @media_bp.route('/batch-import-urls', methods=['POST'])
# @jwt_required()
# def batch_import_media_from_urls():
#     """
#     Multiple media from URLs
    
#     Request Body:
#         urls: Array of image URLs to import
        
#     Returns:
#         JSON response with import results
#     """
#     try:
#         current_user_id = get_jwt_identity()
        
#         data = request.get_json()
#         if not data:
#             return create_response(code=200, message="Request body is required"), 200
            
#         try:
#             validated_data = media_batch_import_schema.load(data)
#         except ValidationError as e:
#             return create_response(code=200, message="Validation error", data=e.messages), 200
        
#         source = request.form.get('source', 'INTERNET')
        


#         result = MediaService.batch_import_from_urls(
#             urls=validated_data['urls'],
#             user_id=current_user_id,
#             source = source
#         )
        
#         if result['code'] == 0:
#             return create_response(
#                 code=0,
#                 data=result['data'],
#                 message="Media imported successfully"
#             ), 201
#         else:
#             return create_response(
#                 code=result['code'],
#                 message=result['msg']
#             ), 200
            
#     except Exception as e:
#         logger.error(f"Error batch importing media: {str(e)}")
#         return create_response(code=500, message="Failed to import media"), 500


@media_bp.route('/<string:media_id>', methods=['GET'])
@jwt_required(optional=True)
def get_media(media_id):
    """
    Media details by ID
    
    Path Parameters:
        media_id: The media ID
        
    Returns:
        JSON response with media details
    """
    try:
        result = MediaService.get_media_by_id(media_id)
        
        if result['code'] == 0:
            return create_response(
                code=0,
                data=result['data'],
                message="Success"
            ), 200
        else:
            return create_response(
                code=result['code'],
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error getting media: {str(e)}")
        return create_response(code=200, message="Failed to get media"), 200



from sqlalchemy.sql import text
@media_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check
    """
    try:

        s3_status = "healthy"
        try:
            s3_client.head_bucket(Bucket=AWS_BUCKET)
        except Exception as e:
            s3_status = f"unhealthy: {str(e)}"
        

        db_status = "healthy"
        try:
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        

        is_healthy = s3_status == "healthy" and db_status == "healthy"
        
        return create_response(
            code=0,
            data={
                'status': 'healthy' if is_healthy else 'unhealthy',
                's3': s3_status,
                'database': db_status,
                'config': {
                    'max_file_size': MAX_FILE_SIZE,
                    'bucket': AWS_BUCKET
                }
            },
            message="Media service health check"
        ), 200 if is_healthy else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            code=500,
            message=f"Health check failed: {str(e)}"
        ), 503
