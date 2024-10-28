
# Web Crawler API

This project provides a web crawler script that can be used with a REST API to extract and process content from web pages, converting it into Markdown format.

## Features

- 🌐 Web page crawling with configurable depth.
- 🚀 REST API implemented with FastAPI.
- 📝 Automatic conversion to Markdown format.
- 📚 Auto-generated documentation accessible via Swagger UI.

## Project Structure

```
webcrawler/
├── webcrawler/
│   ├── __init__.py
│   └── webcrawler.py
├── api/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8 or higher.
- pip (Python package manager).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/user/webcrawler-api.git
   cd webcrawler-api
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the API

To start the server, navigate to the API directory and run:
```bash
cd api
uvicorn main:app --reload
```
The server will start at `http://localhost:8000`.

### API Documentation

Access interactive documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Usage Example

Make a request to the API using Python:

```python
import requests

url = "http://localhost:8000/crawl"
data = {
    "url": "https://example.com",
    "max_depth": 2
}

response = requests.post(url, json=data)
print(response.json())
```

You can also use `curl`:
```bash
curl -X POST "http://localhost:8000/crawl" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://example.com","max_depth":2}'
```

### Using the Crawler Directly

You can use the crawler directly in your code:

```python
from webcrawler import crawl

content = crawl("https://example.com", max_depth=1)
print(content)
```

## Configuration

The API can be configured using environment variables:
- `PORT`: Server port (default: 8000).
- `HOST`: Server host (default: 0.0.0.0).
