# Import required libraries for web crawling, HTML parsing, and text processing
import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import os
import shutil
import argparse
import markdown
import html2text

# Regular expression pattern to validate URLs
HTTP_URL_PATTERN = r"^http[s]*://.+"


class HyperlinkParser(HTMLParser):
    """Custom HTML parser to extract hyperlinks from web pages"""

    def __init__(self):
        super().__init__()
        self.hyperlinks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            href = attrs["href"]
            if self.is_webpage_link(href):
                self.hyperlinks.append(href)

    def is_webpage_link(self, href):
        if href.startswith(("mailto:", "tel:")):
            return False
        parts = href.split("/")
        if parts[-1] and "." in parts[-1]:
            return False
        return True


def get_hyperlinks(url):
    """
    Retrieves all hyperlinks from a given URL
    Args:
        url: The webpage URL to parse
    Returns:
        list: List of hyperlinks found in the webpage
    """
    try:
        with urllib.request.urlopen(url) as response:
            if not response.info().get("Content-Type").startswith("text/html"):
                return []
            html = response.read().decode("utf-8")
    except Exception as e:
        print(e)
        return []

    parser = HyperlinkParser()
    parser.feed(html)
    return parser.hyperlinks


def get_domain_hyperlinks(local_domain, url, base_path):
    """
    Filters and cleans hyperlinks to ensure they belong to the same domain
    Args:
        local_domain: The domain we're crawling
        url: Current URL being processed
        base_path: Base path of the website
    Returns:
        list: Cleaned list of domain-specific hyperlinks
    """
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None

        if re.search(HTTP_URL_PATTERN, link):
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain and url_obj.path.startswith(base_path):
                clean_link = link
        else:
            if link.startswith("/"):
                link = link[1:]
            elif link.startswith("#") or link.startswith("mailto:"):
                continue

            if link.startswith(base_path[1:]):
                clean_link = "https://" + local_domain + "/" + link

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)

    return list(set(clean_links))


def clean_external_links(content, base_url):
    """Elimina enlaces que no sean de email o teléfono, manteniendo su texto"""
    soup = BeautifulSoup(content, "html.parser")

    # Eliminar headers y footers
    for element in soup.find_all(["header", "footer"]):
        element.decompose()

    # Eliminar todas las imágenes
    for img in soup.find_all("img"):
        img.decompose()

    # Procesar enlaces
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href", "")
        # Mantener enlaces de email y teléfono
        if href.startswith(("mailto:", "tel:")):
            continue
        # Para todos los demás enlaces, mantener solo el texto
        a_tag.unwrap()

    return str(soup)


def html_to_clean_text(html_content):
    """
    Converts HTML content to plain text
    Args:
        html_content: Raw HTML content
    Returns:
        str: Clean plain text without HTML markup
    """
    """Convierte HTML a texto plano"""
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    return h.handle(html_content).strip()


def html_to_markdown(html_content):
    """
    Convierte contenido HTML a markdown manteniendo solo enlaces de email y teléfono
    """
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_images = True
    h.ignore_emphasis = False
    h.ignore_links = True  # Ignorar todos los enlaces por defecto
    h.unicode_snob = True

    # Procesar el contenido
    markdown_text = h.handle(html_content)

    # Restaurar enlaces de email y teléfono (que están en formato <email@example.com>)
    markdown_text = re.sub(r"<(mailto:.+?|tel:.+?)>", r"[\1](\1)", markdown_text)

    return markdown_text.strip()


def process_with_AI(content, url):
    """Procesa el contenido con GPT-4 y devuelve texto formateado en markdown"""
    try:
        # Primero convertimos el HTML a markdown
        markdown_content = html_to_markdown(content)

        return markdown_content
    except Exception as e:
        print(f"Error procesando con markdown: {str(e)}")
        return ""


def crawl(url, max_depth=1):
    """
    Main crawling function that processes web pages and generates markdown content
    Args:
        url: Starting URL for crawling
        max_depth: Maximum depth level for crawling (default: 1)
    Returns:
        str: Processed markdown content
    """
    parsed_url = urlparse(url)
    local_domain = parsed_url.netloc
    base_path = parsed_url.path

    queue = deque([(url, 0, None)])  # Añadimos None como título inicial
    seen = set([url])
    url_depth_map = {url: 0}
    processed_content = ""

    while queue:
        url, depth, page_title = queue.popleft()
        print(f"Crawling {url} at depth {depth}")

        if depth > max_depth:
            continue

        try:
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")

            # Obtener el título de la página actual
            current_title = soup.title.string if soup.title else url
            # Si no tenemos título (para la primera página), usar el título actual
            page_title = page_title or current_title

            main_content = soup.find("body")

            if main_content:
                cleaned_content = clean_external_links(str(main_content), url)
                markdown_content = process_with_AI(cleaned_content, url)
                header_prefix = "#" * (depth + 1) + " "
                processed_content += (
                    f"\n\n{header_prefix}{page_title}\n{markdown_content}\n"
                )
                print(f"Contenido procesado de: {url}")

                # Recolectar enlaces y sus títulos para la siguiente iteración
                if depth < max_depth:
                    for link_tag in soup.find_all("a", href=True):
                        link = link_tag["href"]
                        # Obtener el título del enlace (texto dentro de la etiqueta a)
                        link_title = link_tag.get_text(strip=True) or link

                        # Procesar el enlace como antes
                        clean_link = None
                        if re.search(HTTP_URL_PATTERN, link):
                            url_obj = urlparse(link)
                            if (
                                url_obj.netloc == local_domain
                                and url_obj.path.startswith(base_path)
                            ):
                                clean_link = link
                        else:
                            if link.startswith("/"):
                                link = link[1:]
                            elif link.startswith("#") or link.startswith("mailto:"):
                                continue

                            if link.startswith(base_path[1:]):
                                clean_link = "https://" + local_domain + "/" + link

                        if clean_link and clean_link not in seen:
                            if clean_link.endswith("/"):
                                clean_link = clean_link[:-1]
                            queue.append((clean_link, depth + 1, link_title))
                            seen.add(clean_link)
                            url_depth_map[clean_link] = depth + 1

            else:
                print(f"No se pudo extraer el contenido principal de {url}")

        except Exception as e:
            print(f"Error procesando {url}: {str(e)}")

    # En lugar de guardar el archivo, retornamos el contenido
    return processed_content


if __name__ == "__main__":
    """
    Entry point of the script
    Sets up argument parsing and initiates the crawling process
    """
    parser = argparse.ArgumentParser(description="Web Crawler")
    parser.add_argument(
        "--url", default="https://udc.es/es/goberno/", help="Full URL to crawl"
    )
    args = parser.parse_args()

    full_url = args.url
    domain = urlparse(full_url).netloc

    # Obtener el directorio donde está el script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(script_dir, "processed")

    # Crear el directorio si no existe
    if not os.path.exists(processed_dir):
        os.mkdir(processed_dir)

    # Obtener el contenido
    content = crawl(full_url, max_depth=1)

    # Guardar el contenido en un archivo dentro del directorio processed
    output_file = os.path.join(processed_dir, "content.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Archivo markdown creado: {output_file}")
