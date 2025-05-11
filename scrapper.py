'''
SCRAPPER.PY
Scrapper de SCImago que lee un JSON con revistas (título —> áreas/catalogos) y extrae metadatos.
COMPLETADO 100% FUNCIONAL YIPPIEEE :3
'''

import os
import json
import logging
import time
import random
import argparse
import requests
from datetime import date, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm

# Header para las solicitudes HTTP
# Se utiliza un User-Agent para simular un navegador
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        'AppleWebKit/537.36 (KHTML, like Gecko)'
        'Chrome/58.0.3029.110 Safari/537.3'
    )
}

# Agregar un retraso aleatorio entre 1 y 3 segundos
# para evitar ser bloqueado por el servidor
THROTTLE_MIN, THROTTLE_MAX = 1, 3

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Rutas base y JSONs
BASE_DIR = Path(__file__).resolve().parent
INPUT_JSON = BASE_DIR / 'datos' / 'json' / 'revistas.json'
OUTPUT_JSON = BASE_DIR / 'datos' / 'json' / 'scimago.json'
BACKUP_JSON = BASE_DIR / 'datos' / 'json' / 'scimago_backup.json'

# URLs de SCImagoJR
SCIMAGO_BASE = 'https://www.scimagojr.com'
SEARCH_URL = SCIMAGO_BASE + '/journalsearch.php?q='  # Buscador de SCImago


def parse_args():
    """
    Configura y parsea los argumentos de línea de comandos:
      --inicio: índice para comenzar procesamiento
      --fin: índice donde terminar
      --reverso: procesar en orden inverso
      --expire: días antes de re-scrapear
      --max_retries: reintentos ante errores HTTP
    """
    parser = argparse.ArgumentParser(description='Scraper de SCImago mejorado')
    parser.add_argument('--inicio', type=int, default=0,
                        help='Índice desde donde empezar (default: 0)')
    parser.add_argument('--fin', type=int,
                        help='Índice donde terminar (opcional)')
    parser.add_argument('--reverso', action='store_true',
                        help='Procesar en orden inverso')
    parser.add_argument('--expire', type=int, default=30,
                        help='Días antes de re-scrapeo (default: 30)')
    parser.add_argument('--max_retries', type=int, default=5,
                        help='Reintentos ante fallos HTTP')
    return parser.parse_args()


def load_json(path: Path) -> dict:
    '''Carga un archivo JSON y lo convierte en un diccionario.'''
    if path.exists():
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data_safely(data: dict) -> bool:
    '''Guarda datos en el JSON principal y en un backup.'''
    try:
        # Primero guardamos en backup
        with open(BACKUP_JSON, 'w', encoding='utf-8') as bkp:
            json.dump(data, bkp, indent=2, ensure_ascii=False)
        # Luego sobrescribimos archivo principal
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as out:
            json.dump(data, out, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f'Error al guardar datos: {e}')
        return False


def should_update(entry: dict, days: int) -> bool:
    '''Determina si una entrada cacheada debe actualizarse.'''
    ultima = entry.get('ultima_visita')
    if not ultima:
        return True
    try:
        ultima_fecha = date.fromisoformat(ultima)
    except ValueError:
        return True
    return (date.today() - ultima_fecha) > timedelta(days=days)


def scrap(url: str, retries: int) -> requests.Response:
    '''Realiza GET con reintentos y exponencial backoff.'''
    delay = 1.0
    for i in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if i < retries:
                logging.warning(f'Error en {url}: {e}, retry {i}/{retries}')
                time.sleep(delay)
                delay *= 2
                continue
            raise


def find_journal_url(title: str, retries: int) -> str | None:
    '''Busca y devuelve la URL del perfil de la revista en ScimagoJR.'''
    search = SEARCH_URL + requests.utils.quote(title)
    resp = scrap(search, retries)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Selecciona primer resultado: <span class="jrnlname">
    link = soup.select_one('span.jrnlname')
    if link:
        return SCIMAGO_BASE + '/' + link.find_parent('a')['href']
    return None


def extract_subject_area(soup: BeautifulSoup) -> list[str] | None:
    '''Extrae áreas temáticas y categorías de la tabla bajo el header correspondiente.'''
    section = soup.find('h2', string='Subject Area and Category')
    if not section:
        return None
    table = section.find_next('table')
    if not table:
        return None
    return [td.get_text(strip=True) for td in table.find_all('td')]


def obtener_imagen(soup: BeautifulSoup) -> str | None:
    '''Obtiene URL de la imagen del widget (class="imgwidget").'''
    img = soup.find('img', class_='imgwidget')
    if img and img.get('src'):
        return SCIMAGO_BASE + '/' + img['src']
    return None


def scrape_journal_data(url: str, retries: int) -> dict:
    '''Scrapea metadatos (H-index, ISSN, Publisher, etc.) de una revista.'''
    # Throttle aleatorio
    time.sleep(random.uniform(THROTTLE_MIN, THROTTLE_MAX))
    resp = scrap(url, retries)
    soup = BeautifulSoup(resp.text, 'html.parser')

    def get_text_by_header(label: str) -> str | None:
        hdr = soup.find('h2', string=lambda s: s and label in s)
        return hdr.find_next_sibling('p').get_text(strip=True) if hdr else None

    datos = {
        'sitio_web': None,
        'h_index': None,
        'subject_areas': None,
        'publisher': None,
        'issn': None,
        'widget': None,
        'publication_type': None,
        'area': None,
        'catalogo': None,
        'ultima_visita': date.today().isoformat(),
    }
    # Extraer H-index
    try:
        datos['h_index'] = int(get_text_by_header('H-Index') or 0)
    except:
        pass
    # Homepage
    datos['sitio_web'] = soup.find('a', string='Homepage') and soup.find('a', string='Homepage')['href']
    # Publisher
    datos['publisher'] = get_text_by_header('Publisher')
    # ISSN
    datos['issn'] = get_text_by_header('ISSN')
    # Publication type
    datos['publication_type'] = get_text_by_header('Publication type')
    # Subject areas
    datos['subject_areas'] = extract_subject_area(soup)
    # Imagen widget
    datos['widget'] = obtener_imagen(soup)

    # Extraer Área y Catálogo
    try:
        area_section = soup.find('h2', string='Area')
        if area_section:
            datos['area'] = area_section.find_next_sibling('p').get_text(strip=True)
    except:
        pass

    try:
        catalogo_section = soup.find('h2', string='Catalog')
        if catalogo_section:
            datos['catalogo'] = catalogo_section.find_next_sibling('p').get_text(strip=True)
    except:
        pass

    return datos


def main():
    '''Función principal que orquesta la carga, scraping y guardado.'''
    args = parse_args()
    base = load_json(INPUT_JSON)
    cache = load_json(OUTPUT_JSON)

    items = list(base.keys())
    if args.reverso:
        items = items[::-1]
    fin = args.fin or len(items)
    todos = items[args.inicio:fin]

    logging.info(f'Procesando revistas {args.inicio} a {fin}, total: {len(todos)}')
    processed = 0
    for titulo in tqdm(todos, desc='Revistas'):
        key = titulo.lower().strip()
        # Salta si ya existe y no expiró
        if key in cache and not should_update(cache[key], args.expire):
            continue
        # Buscar URL
        url = find_journal_url(titulo, args.max_retries)
        if not url:
            logging.warning(f'No perfil para {titulo}')
            continue
        try:
            data = scrape_journal_data(url, args.max_retries)
            cache[key] = data
            save_data_safely(cache)
            processed += 1
        except Exception as e:
            logging.warning(f'Error scraping {titulo}: {e}')
            continue

    logging.info(f'Completado. Nuevos: {processed}')

if __name__ == '__main__':
    # Al ejecutar, se llama a la función principal
    main()