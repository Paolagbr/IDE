import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

from scanner import Scanner
from parser_sintactico import AnalizadorSintactico

CARPETA = os.path.dirname(os.path.abspath(__file__))


def ejecutar_fase(fase, archivo):
    """archivo = ruta del archivo YA guardado de la pestaña activa."""
    if not archivo:
        messagebox.showwarning(
            "Aviso",
            "Debes guardar el archivo antes de compilar"
        )
        return

    try:
        resultado = subprocess.run(
            [sys.executable, os.path.join(CARPETA, "compilador.py"), fase, archivo],
            capture_output=True,
            text=True,
            cwd=CARPETA
        )

        salida = resultado.stdout.strip() or resultado.stderr.strip() or "(sin salida)"
        messagebox.showinfo("Salida del compilador", salida)

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ---- funciones llamadas por botones ----

def analisis_lexico(editor, tabla, consola):
    if not editor:
        return

    sc = Scanner()
    codigo = editor.get("1.0", "end-1c")

    tokens_validos, tokens_con_errores = sc.analizar(codigo)

    for i in tabla.get_children():
        tabla.delete(i)
    consola.delete("1.0", "end")

    for t in tokens_validos:
        tabla.insert('', 'end', values=(t['tipo'], t['valor'], t['linea']))

    for t in tokens_con_errores:
        if t['tipo'] == 'ERROR':
            consola.insert("end", f">>> Error léxico: '{t['valor']}' en línea {t['linea']}\n")


def analisis_semantico(archivo):
    ejecutar_fase("semantico", archivo)


def codigo_intermedio(archivo):
    ejecutar_fase("intermedio", archivo)


def ejecutar_programa(archivo):
    ejecutar_fase("ejecutar", archivo)


# Análisis sintáctico con visualización del AST en Treeview
def analisis_sintactico(editor, tree_sintactico, consola_errores_sintacticos):
    if not editor:
        messagebox.showwarning("Aviso", "No hay código activo para analizar.")
        return

    # 1. Análisis léxico previo
    sc = Scanner()
    codigo = editor.get("1.0", "end-1c")
    tokens_validos, _ = sc.analizar(codigo)

    # 2. Parser sintáctico
    parser = AnalizadorSintactico(tokens_validos)
    raiz_ast = parser.parsear()

    # 3. Consola de errores sintácticos
    consola_errores_sintacticos.delete("1.0", tk.END)
    if parser.errores:
        for err in parser.errores:
            consola_errores_sintacticos.insert(tk.END, f">>> {err['msg']}\n")
    else:
        consola_errores_sintacticos.insert(
            tk.END, ">>> Análisis Sintáctico completado con éxito. Estructura gramatical válida.\n")

    # 4. Dibujar el AST en el Treeview
    for item in tree_sintactico.get_children():
        tree_sintactico.delete(item)

    def renderizar_nodo_treeview(nodo_ast, padre_id=""):
        if not nodo_ast:
            return
        texto_nodo = nodo_ast.tipo
        if nodo_ast.valor:
            texto_nodo += f" : '{nodo_ast.valor}'"

        nuevo_id = tree_sintactico.insert(padre_id, "end", text=texto_nodo, open=True)
        for hijo in nodo_ast.hijos:
            renderizar_nodo_treeview(hijo, nuevo_id)

    renderizar_nodo_treeview(raiz_ast)
