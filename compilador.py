
import sys

def analisis_lexico(archivo):
    print("Analizando léxico:", archivo)

def analisis_sintactico(archivo):
    print("Analizando sintáctico:", archivo)

def analisis_semantico(archivo):
    print("Analizando semántico:", archivo)

def codigo_intermedio(archivo):
    print("Generando código intermedio:", archivo)

def ejecutar(archivo):
    print("Ejecutando programa:", archivo)


if __name__ == "__main__":

    fase = sys.argv[1]
    archivo = sys.argv[2]

    if fase == "lexico":
        analisis_lexico(archivo)

    elif fase == "sintactico":
        analisis_sintactico(archivo)

    elif fase == "semantico":
        analisis_semantico(archivo)

    elif fase == "intermedio":
        codigo_intermedio(archivo)

    elif fase == "ejecutar":
        ejecutar(archivo)