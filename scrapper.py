'''
SCRAPPER.PY
Scrapper de SCImago que lee un JSON con revistas (título —> areas/catalogos) y extrae metadatos.
COMPLETADO 100% FUNCIONAL YIPPIEEE :3
'''

import json
import logging
import time
import random
from datetime import date, timedelta
from pathlib import Path
import argparse
import requests
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

def parse_args():
    parser = argparse.ArgumentParser(description='Scrapper de SCImago')
    parser.add_argument(
        '--input', default = 'datos/json/revistas.json',
        help = 'Ruta al archivo JSON con revistas (título —> áreas/catalogos)'
    )
    parser.add_argument(
        '--output', default = 'datos/json/scimago.json',
        help = 'Ruta al archivo JSON de salida con datos de Scimago'
    )
    parser.add_argument(
        '--expire', type = int, default = 30,
        help = 'Días para considerar una entrada desactualizada y volver a scrapearla'
    )
    parser.add_argument(
        '--max_retries', type = int, default = 5,
        help = 'Número máximo de intentos ante errores temporales'
    )
    return parser.parse_args()

def load_json(path: Path) -> dict:
    '''Carga un archivo JSON y lo convierte en un diccionario.'''
    # Si el archivo no existe, devuelve un diccionario vacío
    # Si existe, lo carga y lo devuelve
    if path.exists():
        with path.open(encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_json(data: dict, path: Path) -> None:
    '''Guarda un diccionario en un archivo JSON.'''
    # Crea el directorio si no existe
    # y guarda el archivo en formato JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def should_update(entry: dict, days: int) -> bool:
    '''Determina si la entrada debe ser actualizada.'''
    # Si no hay fecha de última visita, se considera que debe actualizarse
    # Si la fecha de última visita es mayor a los días especificados, se considera que debe actualizarse
    ultima = entry.get('ultima_visita')
    if not ultima:
        return True
    try:
        ultima_fecha = date.fromisoformat(ultima)
    except ValueError:
        return True
    return (date.today() - ultima_fecha) > timedelta(days=days)

def get_with_retries(url: str, max_tries: int) -> requests.Response:
    '''Realiza una solicitud HTTP con reintentos ante errores temporales.'''
    delay = 1.0
    for intento in range(1, max_tries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            # Si es 503 y aún quedan intentos, esperamos y reintentamos
            if status == 503 and intento < max_tries:
                logging.warning(f'503 en {url}, retry {intento}/{max_tries} tras {delay:.1f}s')
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except requests.exceptions.RequestException as e:
            # Para otros fallos de red, si hay intentos restantes
            if intento < max_tries:
                logging.warning(f'Error red en {url}: {e}, retry {intento}/{max_tries} tras {delay:.1f}s')
                time.sleep(delay)
                delay *= 2
                continue
            raise

def scrape_revista(titulo: str) -> dict:
    '''Scrapea datos de SCImago para la revista dada.'''
    # Throttle para evitar ser bloqueado
    time.sleep(random.uniform(THROTTLE_MIN, THROTTLE_MAX))
    # Buscador de SCImago
    query = requests.utils.quote(titulo)
    url_busqueda = f'https://www.scimagojr.com/journalsearch.php?q={query}'
    resp = get_with_retries(url_busqueda, max_retries)
    soup = BeautifulSoup(resp.text, 'html.parser')
    enlace = soup.select_one('a[href*="journal.php?"]')
    if not enlace or 'href' not in enlace.attrs:
        logging.warning(f'No perfil para "{titulo}"')
        return {}
    # Extrae el enlace al perfil de la revista
    perfil_url = 'https://www.scimagojr.com/' + enlace['href']
    perfil_resp = get_with_retries(perfil_url, max_retries)
    psoup = BeautifulSoup(perfil_resp.text, 'html.parser')

    try:
        # Extrae los datos del perfil de la revista
        datos = {
            'sitio_web'             : psoup.select_one('a.journalImageLink')['href'],
            'h_index'               : int(psoup.select_one('.hindex .value').text.strip()),
            'subject_areas'         : [e.text.strip() for e in psoup.select('.subject_area .category')],
            'publisher'             : psoup.select_one('.publisher .value').text.strip(),
            'issn'                  : psoup.select_one('.issn .value').text.strip(),
            'widget'                : psoup.select_one('#widget_code').text.strip(),
            'publication_type'      : psoup.select_one('.pub_type .value').text.strip(),
            'ultima_visita'         : date.today().isoformat(),
        }
        return datos
    except Exception as e:
        # Si ocurre un error al parsear el perfil, se registra el error y se devuelve un diccionario vacío
        logging.error(f'Error parseando perfil de {titulo}: {e}')
        return {}

def main():
    '''Función principal del scrapper.'''
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    input_path = Path(args.input)
    output_path = Path(args.output)

    base = load_json(input_path)
    logging.info(f'Cargadas {len(base)} revistas desde {input_path}')

    # Si el archivo de salida no existe, se crea un diccionario vacío
    cache = load_json(output_path)

    for titulo in tqdm(base.keys(), desc='Revistas'):
        # Si el título ya está en el cache y no ha expirado, se omite
        # Si el título no está en el cache, se scrapea
        key = titulo.lower().strip()
        if key in cache and not should_update(cache[key], args.expire):
            continue
        try:
            resultado = scrape_revista(titulo, args.max_retries)
        except Exception as e:
            logging.warning(f'Salteando "{titulo}" tras errores: {e}')
            continue
        # Si el resultado es un diccionario vacío, se omite
        # Si el resultado es un diccionario con datos, se guarda
        if resultado:
            # Si se scrapeó con éxito, se actualiza el cache
            cache[key] = resultado
            save_json(cache, output_path)

    logging.info('Scraping completado.')


if __name__ == '__main__':
    # Al ejecutar, se llama a la función principal
    main()
