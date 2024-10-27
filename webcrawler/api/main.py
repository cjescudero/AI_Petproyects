from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import sys
import os

# Añadir el directorio del webcrawler al path para poder importarlo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webcrawler.webcrawler import crawl

app = FastAPI(
    title="Web Crawler API",
    description="API para procesar y extraer contenido de páginas web",
    version="1.0.0",
)


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: Optional[int] = 1


@app.post(
    "/crawl",
    summary="Procesar una URL",
    description="Recibe una URL y su profundidad máxima para procesarla y devolver el contenido en formato markdown",
)
async def crawl_endpoint(request: CrawlRequest):
    try:
        content = crawl(str(request.url), max_depth=request.max_depth)
        return {
            "status": "success",
            "url": str(request.url),
            "max_depth": request.max_depth,
            "content": content,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error procesando la URL: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
