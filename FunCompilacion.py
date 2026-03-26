import subprocess
from tkinter import messagebox 
from scanner import Scanner
import funcionArchivos

import tkinter as tk
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

# def analisis_lexico():
#     ejecutar_fase("lexico")
def analisis_lexico(editor_actual, tabla_ui, consola_err_ui):
    if not editor_actual: return
    
    # 1. Obtener el código del editor
    codigo = editor_actual.get("1.0", tk.END)
    
    # 2. Instanciar y ejecutar el scanner
    sc = Scanner()
    resultado = sc.analizar(codigo)
    
    # 3. Limpiar interfaces previas
    for item in tabla_ui.get_children():
        tabla_ui.delete(item)
    consola_err_ui.config(state="normal")
    consola_err_ui.delete("1.0", tk.END)
    
    # 4. Llenar la tabla y detectar errores
    hay_errores = False
    for t in resultado:
        if t['tipo'] == 'ERROR':
            hay_errores = True
            msg = f">>> Error Léxico: Carácter '{t['valor']}' no válido en Línea {t['linea']}, Col {t['col']}\n"
            consola_err_ui.insert(tk.END, msg)
        else:
            tabla_ui.insert("", tk.END, values=(t['tipo'], t['valor'], t['linea']))
    
    if not hay_errores:
        consola_err_ui.insert(tk.END, "Análisis léxico terminado sin errores.")
    
    consola_err_ui.config(state="disabled")

def analisis_sintactico():
    ejecutar_fase("sintactico")

def analisis_semantico():
    ejecutar_fase("semantico")

def codigo_intermedio():
    ejecutar_fase("intermedio")

def ejecutar_programa():
    ejecutar_fase("ejecutar")

