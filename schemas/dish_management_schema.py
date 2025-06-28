"""
Dish Management Schemas
Marshmallow schemas for dish CRUD operation validation
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from extensions import ma
import re


class MediaItemSchema(ma.Schema):
    """Schema for validating media items in dish"""
    media_id = fields.String(required=True, validate=validate.Length(min=1, max=50))
    is_pinned = fields.Boolean(missing=False)
    is_verified = fields.Boolean(missing=False)


class DishCreateSchema(ma.Schema):
    """
    Schema for dish creation validation
    Ensures all required fields are present and valid
    """
    
    # Required fields
    title = fields.String(
        required=True, 
        validate=[
            validate.Length(min=1, max=200),
            validate.Regexp(r'^[\w\s\-\'\",\.]+$', error="Title contains invalid characters")
        ],
        error_messages={
            'required': 'Dish title is required',
            'invalid': 'Invalid dish title format'
        }
    )
    
    merchant_id = fields.String(
        required=True,
        validate=validate.Length(equal=24),  # MongoDB ObjectId length
        error_messages={
            'required': 'Merchant ID is required',
            'invalid': 'Invalid merchant ID format'
        }
    )
    
    price = fields.Integer(
        required=True,
        validate=validate.Range(min=0, max=999999),  # Max $9999.99
        error_messages={
            'required': 'Price is required',
            'invalid': 'Price must be a positive integer in cents'
        }
    )
    
    # Optional fields
    description = fields.String(
        missing=None,
        allow_none=True,
        validate=validate.Length(max=1000)
    )
    
    media_ids = fields.List(
        fields.String(validate=validate.Length(equal=24)),
        missing=[],
        validate=validate.Length(max=10)  # Limit number of media items
    )
    
    ingredients = fields.List(
        fields.String(validate=validate.Length(min=1, max=100)),
        missing=[],
        validate=validate.Length(max=50)
    )
    
    cuisine = fields.List(
        fields.String(validate=validate.OneOf([
            'Italian', 'Japanese', 'Chinese', 'Indian', 'Korean',
            'Thai', 'French', 'Mexican', 'Spanish', 'Vietnamese',
            'Middle Eastern', 'American', 'Mediterranean'
        ])),
        missing=[]
    )
    
    meal_type = fields.List(
        fields.String(validate=validate.OneOf([
            'Breakfast', 'Lunch', 'Dinner', 'Brunch', 'Snack', 'Dessert'
        ])),
        missing=[]
    )
    
    flavor = fields.List(
        fields.String(validate=validate.Length(min=1, max=50)),
        missing=[]
    )
    
    course_type = fields.String(
        missing=None,
        allow_none=True,
        validate=validate.OneOf([
            'Appetizer', 'Main Course', 'Dessert', 'Beverage', 'Side Dish'
        ])
    )
    
    # Service options
    pickup_enabled = fields.Boolean(missing=False)
    delivery_enabled = fields.Boolean(missing=False)
    dine_in_enabled = fields.Boolean(missing=False)
    
    @validates('title')
    def validate_title(self, value):
        """Custom validation for title to prevent SQL injection patterns"""
        if any(pattern in value.lower() for pattern in ['drop', 'delete', 'insert', 'update']):
            raise ValidationError('Title contains potentially harmful patterns')
        return value
    
    @validates('price')
    def validate_price(self, value):
        """Ensure price is reasonable"""
        if value < 0:
            raise ValidationError('Price cannot be negative')
        if value > 999999:  # More than $9999.99
            raise ValidationError('Price exceeds maximum allowed value')
        return value
    
    @post_load
    def process_data(self, data, **kwargs):
        """Post-processing of validated data"""
        # Ensure at least one service option is enabled
        service_options = ['pickup_enabled', 'delivery_enabled', 'dine_in_enabled']
        if not any(data.get(option, False) for option in service_options):
            data['delivery_enabled'] = True  # Default to delivery if none specified
        
        # Clean up title
        if 'title' in data:
            data['title'] = ' '.join(data['title'].split())  # Normalize whitespace
        
        return data


class DishUpdateSchema(ma.Schema):
    """
    Schema for dish update validation
    All fields are optional for partial updates
    """
    
    title = fields.String(
        validate=[
            validate.Length(min=1, max=200),
            validate.Regexp(r'^[\w\s\-\'\",\.]+$', error="Title contains invalid characters")
        ]
    )
    
    price = fields.Integer(
        validate=validate.Range(min=0, max=999999)
    )
    
    description = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000)
    )
    
    media_ids = fields.List(
        fields.String(validate=validate.Length(equal=24)),
        validate=validate.Length(max=10)
    )
    
    ingredients = fields.List(
        fields.String(validate=validate.Length(min=1, max=100)),
        validate=validate.Length(max=50)
    )
    
    cuisine = fields.List(
        fields.String(validate=validate.OneOf([
            'Italian', 'Japanese', 'Chinese', 'Indian', 'Korean',
            'Thai', 'French', 'Mexican', 'Spanish', 'Vietnamese',
            'Middle Eastern', 'American', 'Mediterranean'
        ]))
    )
    
    meal_type = fields.List(
        fields.String(validate=validate.OneOf([
            'Breakfast', 'Lunch', 'Dinner', 'Brunch', 'Snack', 'Dessert'
        ]))
    )
    
    flavor = fields.List(
        fields.String(validate=validate.Length(min=1, max=50))
    )
    
    course_type = fields.String(
        allow_none=True,
        validate=validate.OneOf([
            'Appetizer', 'Main Course', 'Dessert', 'Beverage', 'Side Dish'
        ])
    )
    
    pickup_enabled = fields.Boolean()
    delivery_enabled = fields.Boolean()
    dine_in_enabled = fields.Boolean()
    
    @validates_schema
    def validate_update(self, data, **kwargs):
        """Ensure at least one field is being updated"""
        if not data:
            raise ValidationError('No fields provided for update')
        
        # If service options are being updated, ensure at least one remains enabled
        service_options = ['pickup_enabled', 'delivery_enabled', 'dine_in_enabled']
        if any(option in data for option in service_options):
            # Check if all are being set to False
            all_false = all(
                data.get(option, True) is False 
                for option in service_options 
                if option in data
            )
            if all_false:
                raise ValidationError('At least one service option must remain enabled')


class DishBulkDeleteSchema(ma.Schema):
    """
    Schema for bulk dish deletion validation
    """
    
    dish_ids = fields.List(
        fields.String(validate=validate.Length(equal=24)),
        required=True,
        validate=[
            validate.Length(min=1, max=100, error="Can delete 1-100 dishes at a time")
        ],
        error_messages={
            'required': 'Dish IDs are required for bulk deletion'
        }
    )
    
    @validates('dish_ids')
    def validate_dish_ids(self, value):
        """Ensure all dish IDs are unique"""
        if len(value) != len(set(value)):
            raise ValidationError('Duplicate dish IDs found')
        return value


class DishResponseSchema(ma.Schema):
    """
    Schema for dish response serialization
    Used to format dish data for API responses
    """
    
    _id = fields.String(dump_only=True)
    title = fields.String()
    merchant_id = fields.String(attribute='merchant_col')
    price = fields.Integer()
    description = fields.String()
    
    # Media as nested objects
    media = fields.List(fields.Dict())
    
    # Arrays
    ingredients = fields.List(fields.String())
    cuisine = fields.List(fields.String())
    meal_type = fields.List(fields.String())
    flavor = fields.List(fields.String())
    
    course_type = fields.String()
    
    # Service options
    pickup_enabled = fields.Boolean()
    delivery_enabled = fields.Boolean()
    dine_in_enabled = fields.Boolean()
    
    # Stats
    recommendedCount = fields.Integer(attribute='recommendedCount')
    collection_cnt = fields.Integer()
    
    # Metadata
    is_verified = fields.Boolean()
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso')
    deleted_at = fields.DateTime(format='iso', dump_only=True)
    
    class Meta:
        ordered = True