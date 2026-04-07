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
def analisis_lexico(editor, tabla, consola):
    if not editor: return
    
    from scanner import Scanner
    sc = Scanner()
    codigo = editor.get("1.0", "end-1c")
    
    # 1. RECIBE LAS DOS LISTAS (Esto arregla el error)
    tokens_validos, tokens_con_errores = sc.analizar(codigo)
    
    # 2. LIMPIAR TABLA Y CONSOLA
    for i in tabla.get_children(): tabla.delete(i)
    consola.delete("1.0", "end")
    
    # 3. LLENAR LA TABLA (Usamos tokens_validos)
    for t in tokens_validos:
        tabla.insert('', 'end', values=(t['tipo'], t['valor'], t['linea']))
    
    # 4. MOSTRAR ERRORES EN LA CONSOLA (Usamos tokens_con_errores)
    for t in tokens_con_errores:
        if t['tipo'] == 'ERROR': # <--- Ahora esto sí funcionará
            consola.insert("end", f">>> Error léxico: '{t['valor']}' en línea {t['linea']}\n")
def analisis_sintactico():
    ejecutar_fase("sintactico")

def analisis_semantico():
    ejecutar_fase("semantico")

def codigo_intermedio():
    ejecutar_fase("intermedio")

def ejecutar_programa():
    ejecutar_fase("ejecutar")

