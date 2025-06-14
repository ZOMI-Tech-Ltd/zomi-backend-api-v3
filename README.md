# rec-pdp

## Description

`rec-pdp` is a Flask-based API service designed to provide recommendations and features for product display pages (PDP), likely focusing on dishes. It uses a PostgreSQL database for data storage and JWT (JSON Web Tokens) for securing its endpoints. The application is structured with blueprints for modularity, separating concerns like dish information, user actions, and authentication.


## API Endpoints

The API is versioned with a `/v3` prefix for most new endpoints.

### Dishes (`/v3/dish`)

*   **`GET /v3/dish/<dish_id>/overview`**
    *   **Description:** Retrieves an overview for a specific dish.
    *   **Path Parameters:**
        *   `dish_id` (string): The ID of the dish.
    *   **Query Parameters (Optional):**
        *   `lat` (float): Latitude for location context.
        *   `lon` (float): Longitude for location context.
    *   **Authentication:** Optional JWT. If a valid token is provided, `current_user_id` is available to the service.
    *   **Responses:**
        *   `200 OK`: Returns dish overview data.
        *   `404 Not Found`: Dish not found or other error.

### User Actions (`/v3`)

These endpoints generally require JWT authentication. The user ID is typically extracted from the JWT. However, a helper function `get_current_user_id()` exists that can fall back to a `user_id` query parameter, which might be used for development or testing.

*   **`POST /v3/dish/recommend/<dish_id>`**
    *   **Description:** Allows an authenticated user to recommend a dish.
    *   **Path Parameters:** `dish_id` (string)
    *   **Headers:** `Authorization: Bearer <your_jwt_token>`
    *   **Responses:**
        *   `200 OK` or `201 Created`: Recommendation successful.
        *   `401 Unauthorized`: Invalid or missing token.
        *   `404 Not Found`: Dish not found.

*   **`DELETE /v3/dish/recommend/<dish_id>`**
    *   **Description:** Allows an authenticated user to remove their recommendation for a dish.
    *   **Path Parameters:** `dish_id` (string)
    *   **Headers:** `Authorization: Bearer <your_jwt_token>`
    *   **Responses:**
        *   `200 OK` or `204 No Content`: Unrecommend successful.
        *   `401 Unauthorized`: Invalid or missing token.
        *   `404 Not Found`: Dish or recommendation not found.

*   **`POST /v3/dish/collect/<dish_id>`**
    *   **Description:** Allows an authenticated user to add a dish to their collection.
    *   **Path Parameters:** `dish_id` (string)
    *   **Headers:** `Authorization: Bearer <your_jwt_token>`
    *   **Responses:**
        *   `200 OK` or `201 Created`: Collection successful.
        *   `401 Unauthorized`: Invalid or missing token.
        *   `404 Not Found`: Dish not found.

*   **`DELETE /v3/dish/collect/<dish_id>`**
    *   **Description:** Allows an authenticated user to remove a dish from their collection.
    *   **Path Parameters:** `dish_id` (string)
    *   **Headers:** `Authorization: Bearer <your_jwt_token>`
    *   **Responses:**
        *   `200 OK` or `204 No Content`: Removal from collection successful.
        *   `401 Unauthorized`: Invalid or missing token.
        *   `404 Not Found`: Dish or collection item not found.


## Environment Variables

The application uses the following environment variables, configured in the `.env` file:

*   `POSTGRES_USER`: Username for the PostgreSQL database.
*   `POSTGRES_PASSWORD`: Password for the PostgreSQL database.
*   `POSTGRES_HOST`: Hostname or IP address of the PostgreSQL server.
*   `POSTGRES_PORT`: Port number for the PostgreSQL server.
*   `POSTGRES_DB`: Name of the PostgreSQL database.
*   `POSTGRES_SCHEMA`: PostgreSQL schema to use (e.g., `public`).
*   `JWT_SECRET_KEY`: A secure secret key for signing JWTs.

## Project Structure

A brief overview of the key directories:

*   `models/`: Contains SQLAlchemy database models (e.g., `User`, `Dish`).
*   `routes/`: Contains Flask Blueprints defining API routes (e.g., `auth.py`, `dish.py`).
*   `services/`: Likely contains business logic and service layer functions that interact with models and are called by routes.
*   `schemas/`: Likely contains Marshmallow schemas for request/response serialization and validation.
*   `utils/`: For utility functions and helpers.
*   `cache/`: Potentially for caching mechanisms (Redis config was noted as commented out in `config.py`).
*   `app.py`: Main application entry point, creates the Flask app instance.
*   `config.py`: Configuration settings for the application.
*   `extensions.py`: Initializes Flask extensions like SQLAlchemy, Marshmallow, and JWTManager.

## Contributing
