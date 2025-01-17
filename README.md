# Job Title Categorization API

This repository contains the source code for the Job Title Categorization API, which categorizes job titles into top matching service types using a sentence transformer model.

## Core Functionalities

### 1. `main.py`
- **Application Initialization**: Sets up logging, configures the FastAPI application, and runs the server.
- **Middleware and Routers**: Includes middleware for CORS and security headers, and registers the categorize and health check routers.
- **Scheduler**: Uses APScheduler to periodically refresh service type embeddings.

### 2. `services/service_data.py`
- **ServiceData Class**: Manages service types and their embeddings for categorization.
- **Initialization**: Fetches service types from the database and retrieves or caches their embeddings.
- **Embeddings Update**: Updates internal NumPy arrays for vectorized computations.
- **Top Service Types**: Provides the top N service types for given title embeddings.

### 3. `routers/categorize.py`
- **Categorize Endpoint**: Endpoint to categorize job titles into top matching service types.
- **Validation**: Validates and processes user input, including user ID.
- **Batch Processing**: Handles batch processing of job titles and retrieves embeddings asynchronously.

### 4. `routers/health.py`
- **Health Check Endpoint**: Provides a simple health check endpoint to monitor the status of the API.

### 5. `schemas/job_title.py`
- **JobTitles Schema**: Defines the Pydantic model for validating job title inputs, including a user ID and a list of job titles.

### 6. `utils/api_key.py`
- **API Key Validation**: Validates API keys for securing the endpoints.

### 7. `utils/logging_config.py`
- **Logging Configuration**: Configures logging with INFO level, specific formatting, and handlers for both file and stream output, including log rotation.

### 8. `utils/redis_config.py`
- **Redis Configuration**: Manages Redis configuration and caching for embeddings.

### Environment Variables
- **API_KEY**: The API key for securing the endpoints.
- **API_KEY_NAME**: The name of the header where the API key should be provided.

## Getting Started
1. **Install Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

2. **Run the Application**:
    ```sh
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

3. **Check Health**:
    - Endpoint: `GET /health`
    - Response: `{"status": "healthy"}`

4. **Categorize Job Titles**:
    - Endpoint: `POST /categorize`
    - Request Body:
      ```json
      {
          "user_id": "user123",
          "titles": ["Software Engineer", "Data Scientist"]
      }
      ```

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For any inquiries or support, please contact [goodkc12@gmail.com](mailto:goodkc12@gmail.com).
