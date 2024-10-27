# Web Crawler API
Este proyecto proporciona un web crawler con una API REST para extraer y procesar contenido de páginas web, convirtiéndolo a formato markdown.

## Características

- 🌐 Crawling de páginas web con profundidad configurable

- 🚀 API REST con FastAPI

- 📝 Conversión automática a formato markdown

- 📚 Documentación automática con Swagger UI


## Estructura del Proyecto

proyecto/
├── webcrawler/
│   ├── __init__.py
│   └── webcrawler.py
├── api/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
└── README.md

## Requisitos

- Python 3.8+
- pip (gestor de paquetes de Python)


## Instalación
1. Clonar el repositorio:
```
git clone https://github.com/usuario/webcrawler-api.git
cd webcrawler-api
```
git clone https://github.com/usuario/webcrawler-api.git
cd webcrawler-api
2. Crear un entorno virtual (opcional pero recomendado):
```
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
3. Instalar dependencias:
```
pip install -r requirements.txt
```


## Uso
### Ejecutar el API

```
cd api
uvicorn main:app --reload
```
cd api
uvicorn main:app --reload
El servidor se iniciará en `http://localhost:8000`
### Documentación del API
Accede a la documentación interactiva en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


### Ejemplo de Uso
Realizar una petición al API:

```python
import requests

url = "http://localhost:8000/crawl"
data = {
    "url": "https://ejemplo.com",
    "max_depth": 2
}

response = requests.post(url, json=data)
print(response.json())
```

También puedes usar curl:
```
curl -X POST "http://localhost:8000/crawl" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://ejemplo.com","max_depth":2}'
```

### Usar el Crawler Directamente

```python
from webcrawler import crawl

content = crawl("https://ejemplo.com", max_depth=2)
print(content)
```

## Configuración
El API puede configurarse mediante variables de entorno:
- `PORT`: Puerto del servidor (por defecto: 8000)
- `HOST`: Host del servidor (por defecto: 0.0.0.0)
