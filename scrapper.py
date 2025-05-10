'''
SCRAPPER.PY
Scrapper de SCImago que lee un JSON con revistas (título —> areas/catalogos) y extrae metadatos.
'''

import json
import logging
from datetime import date, timedelta
from pathlib import Path
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

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
    return parser.parse_args()

def load_json(path: Path):
    '''Carga un archivo JSON y lo convierte en un diccionario.'''
    # Si el archivo no existe, devuelve un diccionario vacío
    # Si existe, lo carga y lo devuelve
    if path.exists():
        with path.open(encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_json(data: dict, path: Path):
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


def scrape_revista(titulo: str) -> dict:
    '''Scrapea datos de SCImago para la revista dada.'''
    # Buscador de SCImago
    buscador = f'https://www.scimagojr.com/journalsearch.php?q={requests.utils.quote(titulo)}'
    # Realiza la búsqueda
    resp = requests.get(buscador, timeout=15)
    # Verifica si la respuesta fue exitosa
    resp.raise_for_status()
    # Verifica si la búsqueda devolvió resultados
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Busca el primer resultado
    # Si no hay resultados, devuelve un diccionario vacío
    enlace = soup.select_one('a[href*="journal.php?"]')
    if not enlace or 'href' not in enlace.attrs:
        logging.warning(f'No se encontró perfil para: {titulo}')
        return {}

    # Extrae el enlace al perfil de la revista
    perfil_url = 'https://www.scimagojr.com/' + enlace['href']
    # Realiza la solicitud al perfil de la revista
    perfil_resp = requests.get(perfil_url, timeout=15)
    # Verifica si la respuesta fue exitosa
    perfil_resp.raise_for_status()
    # Verifica si la respuesta contiene el perfil de la revista
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
    except Exception as e:
        # Si ocurre un error al parsear el perfil, se registra el error y se devuelve un diccionario vacío
        logging.error(f'Error parseando perfil de {titulo}: {e}')
        return {}

    return datos

