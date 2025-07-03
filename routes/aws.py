from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from services.aws import AWSService
from utils.response_utils import create_response
import logging


logger = logging.getLogger(__name__)

aws_bp = Blueprint('aws', __name__, url_prefix='/v3/aws')


@aws_bp.route('/generatePresignedUrl', methods=['POST'])
@jwt_required(optional=True)
def get_presigned_url():
    try:
        data = request.get_json()
        if not data:
            return create_response(code=400, message="Request body is required"), 200
        
        file_name = data.get('fileName')
        content_type = data.get('contentType')
        
        if not file_name:
            return create_response(code=400, message="fileName is required"), 200
        
        if not content_type:
            return create_response(code=400, message="contentType is required"), 200
        
        # Validate content type
        allowed_content_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/avi', 'video/mpeg', 'video/quicktime', 
            'video/x-msvideo', 'video/x-ms-wmv', 'video/x-flv', 
            'video/x-matroska', 'video/webm'
        ]
        
        if content_type not in allowed_content_types:
            return create_response(
                code=400, 
                message=f"Invalid content type. Allowed types: {', '.join(allowed_content_types)}"
            ), 200
        
        result = AWSService.generate_presigned_put_url(
            file_name=file_name,
            content_type=content_type
        )
        
        if result['code'] == 0:
            return create_response(
                code=0,
                data=result['data'],
                message="Presigned URL generated successfully"
            ), 200
        else:
            return create_response(
                code=result['code'],
                message=result['msg']
            ), 200
            
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return create_response(code=500, message="Failed to generate presigned URL"), 200