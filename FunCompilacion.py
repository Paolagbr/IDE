import subprocess
from tkinter import messagebox
import funcionArchivos


def ejecutar_fase(fase):

    archivo = funcionArchivos.ruta_actual

    # verificar archivo guardado
    if not archivo:
        messagebox.showwarning(
            "Aviso",
            "Debes guardar el archivo antes de compilar"
        )
        return

    try:
        resultado = subprocess.run(
            ["python", "compilador.py", fase, archivo],
            capture_output=True,
            text=True
        )

        messagebox.showinfo(
            "Salida del compilador",
            resultado.stdout
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ---- funciones llamadas por botones ----

def analisis_lexico():
    ejecutar_fase("lexico")

def analisis_sintactico():
    ejecutar_fase("sintactico")

def analisis_semantico():
    ejecutar_fase("semantico")

def codigo_intermedio():
    ejecutar_fase("intermedio")

def ejecutar_programa():
    ejecutar_fase("ejecutar")