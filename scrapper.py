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
