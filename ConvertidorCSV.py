import csv
import json
import os

def crear_diccionario_revistas(carpeta_csv_areas, carpeta_csv_catalogos, archivo_salida_json):
    revistas = {}

    # Leer los archivos de "áreas" :o
    for archivo in os.listdir(carpeta_csv_areas):
        if archivo.endswith('.csv'):
            ruta_archivo = os.path.join(carpeta_csv_areas, archivo)
            with open(ruta_archivo, mode='r', encoding='latin-1') as archivo_csv:
                lector_csv = csv.DictReader(archivo_csv)
                for fila in lector_csv:
                    titulo = fila['TITULO:'].strip().lower()
                    area = fila['TITULO:'].strip()
                    if titulo not in revistas:
                        revistas[titulo] = {"areas": [], "catalogos": []}
                    if area not in revistas[titulo]["areas"]:
                        revistas[titulo]["areas"].append(area)

    # Leer archivos de "catálogos" :o
    for archivo in os.listdir(carpeta_csv_catalogos):
        if archivo.endswith('.csv'):
            ruta_archivo = os.path.join(carpeta_csv_catalogos, archivo)
            with open(ruta_archivo, mode='r', encoding='latin-1') as archivo_csv:
                lector_csv = csv.DictReader(archivo_csv)
                for fila in lector_csv:
                    titulo = fila['TITULO:'].strip().lower()
                    catalogo = fila['TITULO:'].strip()
                    if titulo not in revistas:
                        revistas[titulo] = {"areas": [], "catalogos": []}
                    if catalogo not in revistas[titulo]["catalogos"]:
                        revistas[titulo]["catalogos"].append(catalogo)

    # Escribir el diccionario en un archivo JSON ezzzz :)
    with open(archivo_salida_json, mode='w', encoding='utf-8') as archivo_json:
        json.dump(revistas, archivo_json, indent=4, ensure_ascii=False)

def main():
    # Rutas de las carpetas de los csv -.-
    carpeta_csv_areas = r'datos/csv/areas'
    carpeta_csv_catalogos = r'datos/csv/catalogos'

    # Salida del jason :o
    archivo_salida_json = r'datos/json/revistas.json'

    # Crear el diccionario de revistas y guardarlo como juson :o
    crear_diccionario_revistas(carpeta_csv_areas, carpeta_csv_catalogos, archivo_salida_json)
    print(f"Archivo JSON creado en: {archivo_salida_json}")

if __name__ == "__main__":
    main()