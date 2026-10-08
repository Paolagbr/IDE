import ast
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

# Módulos de tu compilador
from scanner import Scanner
from parser_sintactico import AnalizadorSintactico
from semantico import SemanticAnalyzer

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

# --- SEMANTICO
def analisis_semantico(editor, tree_ast_widget, tabla_simbolos_widget, consola_errores_widget):
    if not editor:
        messagebox.showwarning("Aviso", "No hay un editor activo.")
        return

    # 1. Obtener código fuente del editor
    codigo = editor.get("1.0", "end-1c")

    # 2. Limpiar componentes gráficos de la GUI
    for item in consola_errores_widget.get_children():
        consola_errores_widget.delete(item)
    for item in tree_ast_widget.get_children():
        tree_ast_widget.delete(item)
    if tabla_simbolos_widget:
        for item in tabla_simbolos_widget.get_children():
            tabla_simbolos_widget.delete(item)

    # 3. Análisis Léxico y Sintáctico previo para obtener el AST
    sc = Scanner()
    tokens_validos, _ = sc.analizar(codigo)
    
    parser = AnalizadorSintactico(tokens_validos)
    raiz_ast = parser.parsear()

    # Si hay errores sintácticos o el AST está vacío, detener
    if parser.errores or not raiz_ast:
        detalle = "\n".join(e['msg'] for e in parser.errores[:5]) or "El programa está vacío."
        messagebox.showerror(
            "Error Sintáctico",
            "Debes corregir los errores sintácticos antes de realizar el análisis semántico.\n\n" + detalle
        )
        return

    # 4. Ejecutar el Analizador Semántico
    analizador = SemanticAnalyzer()
    ast_anotado, tabla_simbolos, errores_semanticos = analizador.analyze(raiz_ast)

    # 5. Mostrar Errores Semánticos en el Treeview de errores
    if errores_semanticos:
        for err_msg in errores_semanticos:
            # Extraer número de línea si viene en formato "Error semántico [Línea X]: ..."
            linea = "-"
            if "[Línea " in err_msg:
                try:
                    linea = err_msg.split("[Línea ")[1].split("]")[0]
                except Exception:
                    linea = "-"

            consola_errores_widget.insert("", "end", values=(
                linea,
                1,
                "Semántico",
                err_msg
            ))
        messagebox.showwarning("Análisis Semántico", f"Se encontraron {len(errores_semanticos)} errores semánticos.")
    else:
        messagebox.showinfo("Análisis Semántico", "Análisis semántico completado con éxito sin errores.")

    # 6. Llenar la Tabla de Símbolos en la GUI
    if tabla_simbolos_widget and tabla_simbolos:
        for sym in tabla_simbolos.get_all_symbols():
            tabla_simbolos_widget.insert("", "end", values=(
                sym.name, 
                sym.data_type, 
                sym.line, 
                sym.offset
            ))

    # 7. Renderizar el AST Anotado en la pantalla
    def renderizar_ast_anotado(nodo, padre_id=""):
        if not nodo:
            return
        
        # Formatear el texto del nodo mostrando tipo, valor y anotación de tipo
        texto_nodo = getattr(nodo, 'node_type', getattr(nodo, 'tipo', 'NODO'))
        valor = getattr(nodo, 'value', getattr(nodo, 'valor', None))
        dtype = getattr(nodo, 'data_type', getattr(nodo, 'dtype', None))

        if valor is not None and valor != "":
            texto_nodo += f" : '{valor}'"
        if dtype:
            texto_nodo += f"  [{dtype}]"

        nuevo_id = tree_ast_widget.insert(padre_id, "end", text=texto_nodo, open=True)
        
        # Recorrer hijos
        hijos = getattr(nodo, 'children', getattr(nodo, 'hijos', []))
        for hijo in hijos:
            renderizar_ast_anotado(hijo, nuevo_id)

    renderizar_ast_anotado(ast_anotado)