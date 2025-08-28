# CreateMany API Test Scenarios

## API Endpoint
`POST /v3/taste/createMany`

## Headers Required
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json
```

## Test Scenarios

### 1. Create New Tastes
```json
{
  "items": [
    {
      "dishId": "dish123",
      "recommendState": 0,
      "comment": "",
      "mediaIds": [],
      "mood": 0,
      "tags": []
    },
    {
      "dishId": "dish456",
      "recommendState": 1,
      "comment": "Delicious!",
      "mediaIds": ["media1"],
      "mood": 1,
      "tags": ["spicy"]
    }
  ]
}
```
Expected: Creates two new tastes with states 0 and 3 respectively.

### 2. Update Existing Tastes
```json
{
  "items": [
    {
      "dishId": "dish123",
      "recommendState": 1,
      "comment": "Updated review",
      "mediaIds": ["media2"],
      "mood": 2,
      "tags": ["sweet"]
    },
    {
      "tasteId": "taste789",
      "dishId": "dish456",
      "recommendState": 2,
      "comment": "Not my taste",
      "mediaIds": [],
      "mood": 0,
      "tags": []
    }
  ]
}
```
Expected: Updates existing tastes with new states (100 and 31).

### 3. Delete Tastes
```json
{
  "items": [
    {
      "dishId": "dish123",
      "recommendState": null
    },
    {
      "tasteId": "taste456",
      "dishId": "dish789",
      "recommendState": null
    }
  ]
}
```
Expected: Soft deletes the tastes (adds deletedAt timestamp).

### 4. Mixed Operations
```json
{
  "items": [
    {
      "dishId": "dish001",
      "recommendState": 0,
      "comment": "New taste",
      "mediaIds": [],
      "mood": 0,
      "tags": []
    },
    {
      "dishId": "dish002",
      "recommendState": 1,
      "comment": "",
      "mediaIds": ["media1", "media2"],
      "mood": 1,
      "tags": []
    },
    {
      "tasteId": "existingTaste123",
      "dishId": "dish003",
      "recommendState": null
    }
  ]
}
```
Expected: Creates new taste (state 30), updates existing taste (state 4), and deletes one taste.

## State Calculation Logic

### Without Content (No Comment, No Media)
- recommendState 0 (Eaten Only) → state: 0
- recommendState 1 (Eaten + Like) → state: 1
- recommendState 2 (Eaten + Dislike) → state: 2

### With Comment Only
- recommendState 0 (Eaten + Comment) → state: 30
- recommendState 1 (Eaten + Comment + Like) → state: 3
- recommendState 2 (Eaten + Comment + Dislike) → state: 31

### With Media Only
- recommendState 0 (Eaten + Media) → state: 40
- recommendState 1 (Eaten + Media + Like) → state: 4
- recommendState 2 (Eaten + Media + Dislike) → state: 41

### With Comment AND Media
- recommendState 0 (Eaten + Comment + Media) → state: 5
- recommendState 1 (Eaten + Comment + Media + Like) → state: 100
- recommendState 2 (Eaten + Comment + Media + Dislike) → state: 101

## Response Format

### Success Response
```json
{
  "code": 0,
  "data": [
    {
      "id": "taste_id",
      "state": 30,
      "recommendState": 0,
      "action": "created",
      "dishId": "dish123"
    },
    {
      "id": "taste_id2",
      "state": 100,
      "recommendState": 1,
      "action": "updated",
      "dishId": "dish456"
    },
    {
      "id": "taste_id3",
      "action": "deleted",
      "dishId": "dish789"
    }
  ],
  "message": "Tastes processed successfully"
}
```

### Error Response
```json
{
  "code": 200,
  "data": {
    "failed": [
      {
        "code": 400,
        "message": "Invalid recommend state. Must be 0, 1, 2, or null"
      }
    ]
  },
  "message": "Some taste operations failed"
}
```

## Key Features
1. **Unified API**: Single endpoint handles create, update, and delete operations
2. **Flexible Querying**: Can use either `tasteId` or `userId + dishId` combination
3. **Soft Delete**: Uses `deletedAt` timestamp for deletion
4. **Auto-restore**: Deleted tastes are automatically restored when user acts on them again
5. **State Calculation**: Automatic state calculation based on content and recommendState
6. **Batch Processing**: Process multiple tastes in a single request
7. **Backward Compatible**: Existing `recommend_dish` and `unrecommend_dish` methods now use the unified `process_taste` internally