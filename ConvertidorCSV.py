import csv
import json
import os

def convertir_csv_a_json(carpeta_csv, archivo_salida_json):

    datos = []

    #Lee toda la carpeta :o
    for archivo in os.listdir(carpeta_csv):
        if archivo.endswith('.csv'):
            ruta_archivo = os.path.join(carpeta_csv, archivo)
            with open(ruta_archivo, mode='r', encoding='latin-1') as archivo_csv:
                lector_csv = csv.DictReader(archivo_csv)
                for fila in lector_csv:
                    datos.append(fila)
                    

    #Escribir JSON uwu
    with open(archivo_salida_json, mode='w', encoding='utf-8') as archivo_json:
        json.dump(datos, archivo_json, indent=4, ensure_ascii=False)

def main():
    #Ruta de la carpeta de los CSV :o
    carpeta_csv = r'C:\Users\josea\OneDrive\Documentos\Escritorio\Desarrollo IV\datos\csv'

    #Salida del JASON :o
    archivo_salida_json = r'C:\Users\josea\OneDrive\Documentos\Escritorio\Desarrollo IV\proyectoDS4\datosconvertidos.json'

    convertir_csv_a_json(carpeta_csv, archivo_salida_json)
    print(f"Archivo JSON creado en: {archivo_salida_json}")


if __name__ == "__main__":
    main()