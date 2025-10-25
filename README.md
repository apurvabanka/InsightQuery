# InsightQuery

This API provides endpoints for uploading CSV files and managing them by session ID.

## Demo

https://github.com/user-attachments/assets/demo.mov

## Features

- Create CSV sessions with unique session IDs
- Upload CSV files to specific sessions
- Retrieve all files for a session
- Delete sessions and individual files
- Automatic file storage with unique filenames
- Database tracking of all uploads

## API Endpoints

### 1. Create Session
**POST** `/api/csv/sessions`

Create a new CSV session with a unique session ID.

**Request Body:**
```json
{
  "session_id": "your_session_id"
}
```

**Response:**
```json
{
  "message": "Session created successfully",
  "session_id": "your_session_id"
}
```

### 2. Upload CSV File
**POST** `/api/csv/upload`

Upload a CSV file to a specific session.

**Form Data:**
- `file`: The CSV file to upload
- `session_id`: The session ID to upload to

**Response:**
```json
{
  "message": "File uploaded successfully",
  "session_id": "your_session_id",
  "file": {
    "id": "file_uuid",
    "filename": "stored_filename.csv",
    "original_filename": "original_name.csv",
    "file_size": 1024,
    "content_type": "text/csv",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

### 3. Get Session Files
**GET** `/api/csv/sessions/{session_id}`

Retrieve all CSV files for a specific session.

**Response:**
```json
{
  "id": "session_uuid",
  "session_id": "your_session_id",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "csv_files": [
    {
      "id": "file_uuid",
      "filename": "stored_filename.csv",
      "original_filename": "original_name.csv",
      "file_size": 1024,
      "content_type": "text/csv",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### 4. Get All Sessions
**GET** `/api/csv/sessions`

Retrieve all CSV sessions with their files.

### 5. Delete Session
**DELETE** `/api/csv/sessions/{session_id}`

Delete a session and all its associated files.

### 6. Delete File
**DELETE** `/api/csv/files/{file_id}`

Delete a specific CSV file.

## Database Models

### CSVSession
- `id`: Unique identifier (UUID)
- `session_id`: User-provided session identifier
- `created_at`: Session creation timestamp
- `updated_at`: Last update timestamp

### CSVFile
- `id`: Unique identifier (UUID)
- `session_id`: Foreign key to CSVSession
- `filename`: Stored filename (UUID-based)
- `original_filename`: Original uploaded filename
- `file_size`: File size in bytes
- `content_type`: MIME type
- `file_path`: Path to stored file
- `created_at`: Upload timestamp

## Usage Example

```python
import requests

# 1. Create a session
session_data = {"session_id": "my_session_123"}
response = requests.post("http://localhost:8000/api/csv/sessions", json=session_data)

# 2. Upload a CSV file
with open("data.csv", "rb") as f:
    files = {"file": f}
    data = {"session_id": "my_session_123"}
    response = requests.post("http://localhost:8000/api/csv/upload", files=files, data=data)

# 3. Get session files
response = requests.get("http://localhost:8000/api/csv/sessions/my_session_123")
files = response.json()
```

## Running the API

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
cd backend
uvicorn main:app --reload
```

3. Access the API documentation:
```
http://localhost:8000/docs
```

## File Storage

- CSV files are stored in the `uploads/` directory
- Each file gets a unique UUID-based filename to prevent conflicts
- Original filenames are preserved in the database
- Files are automatically cleaned up when sessions or files are deleted

## Error Handling

- **400 Bad Request**: Invalid file type (non-CSV) or duplicate session ID
- **404 Not Found**: Session or file not found
- **500 Internal Server Error**: File system or database errors

## Security Considerations

- Only CSV files are accepted
- File size limits can be added as needed
- Session IDs should be validated for format/security
- Consider adding authentication for production use 