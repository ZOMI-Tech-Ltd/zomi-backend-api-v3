
from marshmallow import Schema, fields, validate, validates, ValidationError
from extensions import ma
import re


class MediaUploadSchema(ma.Schema):

    type = fields.String(
        missing='image',
        validate=validate.OneOf(['image', 'video']),
        error_messages={
            'invalid': 'Invalid media type. Must be "image" or "video"'
        }
    )
    

class MediaImportUrlSchema(ma.Schema):

    source_url = fields.URL(
        required=True,
        validate=[
            validate.Length(min=10, max=2048),
            validate.Regexp(
                r'^https?://.+\.(jpg|jpeg|png|gif|webp)(\?.*)?$',
                flags=re.IGNORECASE,
                error="URL must point to an image file (jpg, jpeg, png, gif, or webp)"
            )
        ],
        error_messages={
            'required': 'Source URL is required',
            'invalid': 'Invalid URL format'
        }
    )
    
    @validates('source_url')
    def validate_source_url(self, value):
        """Additional validation for source URL"""
        # Check for potentially harmful URLs
        blocked_domains = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '192.168.',
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.'
        ]
        
        for domain in blocked_domains:
            if domain in value.lower():
                raise ValidationError('URL points to a blocked domain')
        
        # Check URL length
        if len(value) > 2048:
            raise ValidationError('URL is too long (max 2048 characters)')
        
        return value


class MediaBatchImportSchema(ma.Schema):

    urls = fields.List(
        fields.URL(
            validate=[
                validate.Length(min=10, max=2048),
                validate.Regexp(
                    r'^https?://.+\.(jpg|jpeg|png|gif|webp)(\?.*)?$',
                    flags=re.IGNORECASE,
                    error="Each URL must point to an image file"
                )
            ]
        ),
        required=True,
        validate=[
            validate.Length(min=1, max=100, error="Can import 1-100 URLs at a time")
        ],
        error_messages={
            'required': 'URLs array is required'
        }
    )
    
    @validates('urls')
    def validate_urls(self, value):
        if len(value) != len(set(value)):
            raise ValidationError('Duplicate URLs found')
        
        # Validate each URL
        for url in value:
            # Same validation as single import
            blocked_domains = [
                'localhost', '127.0.0.1', '0.0.0.0',
                '192.168.', '10.', '172.'
            ]
            
            for domain in blocked_domains:
                if domain in url.lower():
                    raise ValidationError(f'URL {url} points to a blocked domain')
        
        return value


class MediaResponseSchema(ma.Schema):



    _id = fields.String(dump_only=True)
    url = fields.URL(dump_only=True)

    type = fields.String(dump_only=True)
    width = fields.Integer(dump_only=True)
    height = fields.Integer(dump_only=True)
    blur_hash = fields.String(dump_only=True, data_key='blurHash')
    file_size = fields.Integer(dump_only=True, data_key='fileSize')
    
    # Optional fields
    original_filename = fields.String(dump_only=True, allow_none=True)
    uploaded_by = fields.String(dump_only=True, allow_none=True)
    
    # Timestamps
    created_at = fields.DateTime(format='iso', dump_only=True)
    updated_at = fields.DateTime(format='iso', dump_only=True)
    
    class Meta:
        ordered = True


class MediaListResponseSchema(ma.Schema):
    """
    Schema for batch media response
    """
    successful = fields.List(fields.Nested(MediaResponseSchema))
    failed = fields.List(fields.Dict())
    
    class Meta:
        ordered = True


class MediaProcessingStatsSchema(ma.Schema):
    """
    Schema for media processing statistics
    """
    processed = fields.Integer()
    successful = fields.Integer()
    failed = fields.Integer()
    
    class Meta:
        ordered = True