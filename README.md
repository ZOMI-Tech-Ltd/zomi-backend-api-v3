# ZOMI Restaurant Recommendation API

A Flask-based API service for restaurant dish recommendations, user interactions, and media management.

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Dish Endpoints](#dish-endpoints)
  - [User Actions](#user-actions)
  - [Taste Management](#taste-management)
  - [Media Management](#media-management)
- [Message Queue Integration](#message-queue-integration)
- [Response Format](#response-format)
- [Environment Variables](#environment-variables)

## Overview

This API provides endpoints for:
- Viewing dish information and recommendations
- Managing user collections and recommendations
- Creating and managing user-generated content (UGC)
- Uploading and processing media files
- Integration with RabbitMQ for asynchronous processing

## Authentication

Most endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Endpoints marked with 🔓 support optional authentication (enhanced features when authenticated).

## API Endpoints

### Dish Endpoints

#### Get Dish Overview 🔓
```
GET /v3/dish/{dish_id}/overview
```

Retrieves detailed information about a specific dish.

**Query Parameters:**
- `lat` (float, optional): User latitude for distance calculation
- `lon` (float, optional): User longitude for distance calculation

**Response:**
```json
{
  "code": 0,
  "data": {
    "_id": "dish_id",
    "title": "Dish Name",
    "price": 2800,
    "images": {
      "url": "https://...",
      "width": 800,
      "height": 600,
      "externalImage": true
    },
    "recommendedCount": 42,
    "merchant": {
      "_id": "merchant_id",
      "name": "Restaurant Name",
      "distance_km": 2.5
    },
    "isCollected": false,
    "isRecommended": false
  },
  "msg": "Success"
}
```

### User Actions

#### Add Dish (UGC) 🔒
```
POST /v3/dish/add
```

Create a new dish through user-generated content flow.

**Request Body:**
```json
{
  "merchantId": "merchant_id",
  "name": "Dish Name",
  "price": 2800,
  "mediaIds": ["media_id1"],
  "description": "Delicious dish",
  "characteristic": "Spicy and savory"
}
```

#### Recommend Dish 🔒
```
POST /v3/dish/recommend/{dish_id}
```

Quick recommendation without detailed review.

**Response:**
```json
{
  "code": 0,
  "msg": "Recommended successfully"
}
```

#### Unrecommend Dish 🔒
```
DELETE /v3/dish/recommend/{dish_id}
```

Remove recommendation (sets recommendState=2, preserves record).

#### Collect Dish 🔒
```
POST /v3/dish/collect/{dish_id}
```

Add dish to user's collection.

#### Uncollect Dish 🔒
```
DELETE /v3/dish/collect/{dish_id}
```

Remove dish from user's collection.

#### Get User Items by Merchant 🔒
```
GET /v3/merchant/{merchant_id}/user-items
```

Get user's collected and recommended dishes within a merchant.

**Response:**
```json
{
  "code": 0,
  "data": {
    "collected": ["dish_id1", "dish_id2"],
    "recommended": ["taste_id1", "taste_id2"],
    "merchant": {
      "_id": "merchant_id",
      "name": "Restaurant Name"
    }
  }
}
```

### Taste Management

#### Get User Taste Total 🔒
```
POST /v3/taste/userTotal
```

Get total number of user's taste reviews.

**Response:**
```json
{
  "code": 0,
  "data": {
    "total": 25
  }
}
```

#### Get Taste Details 🔒
```
GET /v3/taste/{taste_id}
```

Get detailed information about a specific taste review.

#### Create Taste 🔒
```
POST /v3/taste/create
```

Create a detailed taste review with media and comments.

**Request Body:**
```json
{
  "dishId": "dish_id",
  "comment": "Amazing flavor!",
  "mediaIds": ["media_id1", "media_id2"],
  "mood": 1,
  "tags": ["spicy", "authentic"],
  "recommendState": 1
}
```

**Mood Values:**
- 0: Default
- 1: Must Try
- 2: To Be Repeated
- 3: Worth a Shot

**Recommend State:**
- 0: Default
- 1: Recommend
- 2: Not Recommend

#### Create Multiple Tastes 🔒
```
POST /v3/taste/createMany
```

Create multiple taste reviews in one request.

**Request Body:**
```json
{
  "items": [
    {
      "dishId": "dish_id1",
      "comment": "Great!",
      "mood": 1
    },
    {
      "dishId": "dish_id2",
      "comment": "Not bad",
      "mood": 3
    }
  ]
}
```

#### Edit Taste 🔒
```
PUT /v3/taste/edit/{taste_id}
```

Update an existing taste review.

**Request Body:**
```json
{
  "dishId": "dish_id",
  "comment": "Updated comment",
  "mediaIds": ["media_id1"],
  "mood": 2,
  "tags": ["updated", "tags"]
}
```

#### Delete Taste 🔒
```
POST /v3/taste/delete
```

Soft delete a taste review.

**Request Body:**
```json
{
  "id": "taste_id"
}
```

#### Like Taste 🔒
```
POST /v3/taste/like/{taste_id}
```

Like another user's taste review.

#### Unlike Taste 🔒
```
DELETE /v3/taste/like/{taste_id}
```

Remove like from a taste review.

### Media Management

#### Upload Media 🔓
```
POST /v3/media/upload
```

Upload a single media file.

**Form Data:**
- `file`: The media file (image/video)
- `type`: Media type ("image" or "video")
- `source`: Media source ("INTERNET", "USER_AVATAR", "VOLCENGINE")

**Response:**
```json
{
  "code": 0,
  "data": {
    "_id": "media_id",
    "url": "https://cloudfront.net/...",
    "width": 1920,
    "height": 1080,
    "blur_hash": "L6PZfSi_.AyE..."
  }
}
```

#### Import Media from URL 🔓
```
POST /v3/media/import-url
```

Import media from an external URL.

**Request Body:**
```json
{
  "source_url": "https://example.com/image.jpg"
}
```

#### Get Media Details 🔓
```
GET /v3/media/{media_id}
```

Get detailed information about a media item.

#### Health Check
```
GET /v3/media/health
```

Check media service health status.

**Response:**
```json
{
  "code": 0,
  "data": {
    "status": "healthy",
    "s3": "healthy",
    "database": "healthy",
    "config": {
      "max_file_size": 15728640,
      "bucket": "your-bucket-name"
    }
  }
}
```

## Message Queue Integration

The API sends messages to RabbitMQ for asynchronous processing:

### Queue: `media/create`
Triggered when media is uploaded or imported.
```json
{
  "mediaId": "media_id",
  "type": "IMAGE",
  "url": "https://...",
  "source": "INTERNET",
  "width": 1920,
  "height": 1080
}
```

### Queue: `dish/collect`
Triggered when user collects/uncollects a dish.
```json
{
  "userId": "user_id",
  "dishId": "dish_id",
  "state": 1
}
```
States: 1 = collect, 2 = uncollect

### Queue: `taste/create`
Triggered when user creates a taste review.
```json
{
  "id": "taste_id",
  "userId": "user_id",
  "dishId": "dish_id",
  "comment": "Great dish!",
  "recommendState": 1,
  "mediaIds": ["media_id1"]
}
```

### Queue: `taste/addDish`
Triggered when user adds a new dish via UGC.
```json
{
  "userId": "user_id",
  "merchantID": "merchant_id",
  "name": "New Dish",
  "price": 2800,
  "mediaIds": ["media_id1"],
  "description": "Description",
  "characteristic": "Spicy"
}
```

## Response Format

All API responses follow this standard format:

```json
{
  "code": 0,
  "data": {},
  "msg": "Success"
}
```

**Common Response Codes:**
- `0`: Success
- `200`: Generic error
- `400`: Bad request
- `401`: Unauthorized
- `404`: Not found
- `409`: Conflict (already exists)
- `500`: Internal server error

## Environment Variables

```env
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database
POSTGRES_SCHEMA=mongodb

# MongoDB
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB=zomi_backend
ENABLE_MONGODB_WRITE=true
MONGODB_FIRST=true

# JWT
JWT_SECRET_KEY=your_secret_key

# AWS S3
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key
AWS_BUCKET_NAME=your_bucket
AWS_REGION=us-west-1
CLOUDFRONT_URL=https://your-cloudfront.net/

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=app_exchange

# Media
MAX_FILE_SIZE=15728640
```

## Running the Application

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:4003`

## Testing

Use the following curl examples to test the endpoints:

```bash
# Get dish overview
curl -X GET "http://localhost:4003/v3/dish/DISH_ID/overview?lat=37.7749&lon=-122.4194"

# Recommend a dish (requires auth)
curl -X POST "http://localhost:4003/v3/dish/recommend/DISH_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Upload media
curl -X POST "http://localhost:4003/v3/media/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  -F "type=image" \
  -F "source=INTERNET"
```