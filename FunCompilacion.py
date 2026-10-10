import os
import re
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

# Módulos de tu compilador
from scanner import Scanner
from parser_sintactico import AnalizadorSintactico
from semantico import SemanticAnalyzer, formatear_valor
from ast_node import completar_posiciones

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


# ---------------------------------------------------------------
# Marcas de error en el editor (subrayado rojo, como en Visual Studio)
# ---------------------------------------------------------------
def marcar_errores(editor, errores):
    """errores: lista de (fila, columna, largo). largo=None -> se calcula con la palabra bajo la marca.
    Pasa una lista vacía para limpiar las marcas."""
    try:
        editor.tag_config("err_marca", underline=True, underlinefg="#FF5555", background="#4A2A2A")
    except tk.TclError:
        editor.tag_config("err_marca", underline=True, foreground="#FF5555", background="#4A2A2A")
    editor.tag_remove("err_marca", "1.0", "end")

    for fila, col, largo in errores:
        try:
            fila, col = int(fila), int(col)
        except (TypeError, ValueError):
            continue                      # p. ej. errores al final del archivo ("EOF")
        ini = f"{fila}.{col - 1}"
        if not largo:
            resto = editor.get(ini, f"{fila}.end")
            m = re.match(r"\w+|\S", resto)
            largo = len(m.group(0)) if m else 1
        editor.tag_add("err_marca", ini, f"{fila}.{col - 1 + largo}")
    editor.tag_raise("err_marca")


def _atributos(nodo):
    """Texto de la columna Atributos: 'tipo (H), valor (S)'."""
    return ", ".join(f"{n} ({c})" for n, c in getattr(nodo, 'atributos', []))


def _posicion(nodo):
    return f"{nodo.line}:{nodo.col}" if getattr(nodo, 'col', None) else ""


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

    marcas = []
    for t in tokens_con_errores:
        if t['tipo'] == 'ERROR':
            consola.insert("end", f">>> Error léxico: '{t['valor']}' en línea {t['linea']}, col {t['col']}\n")
            marcas.append((t['linea'], t['col'], len(t['valor'])))
    marcar_errores(editor, marcas)


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
    completar_posiciones(raiz_ast)

    # 3. Consola de errores sintácticos + marcas rojas en el editor
    consola_errores_sintacticos.delete("1.0", tk.END)
    if parser.errores:
        for err in parser.errores:
            consola_errores_sintacticos.insert(tk.END, f">>> {err['msg']}\n")
    else:
        consola_errores_sintacticos.insert(
            tk.END, ">>> Análisis Sintáctico completado con éxito. Estructura gramatical válida.\n")
    marcar_errores(editor, [(e['linea'], e['col'], None) for e in parser.errores])

    # 4. Dibujar el AST en el Treeview (con la columna Fila:Col)
    for item in tree_sintactico.get_children():
        tree_sintactico.delete(item)
    try:
        tree_sintactico.tag_configure("err", foreground="#FF5555")
    except Exception:
        pass

    def renderizar_nodo_treeview(nodo_ast, padre_id=""):
        if not nodo_ast:
            return
        texto_nodo = nodo_ast.tipo
        if nodo_ast.valor:
            texto_nodo += f" : '{nodo_ast.valor}'"
        etiquetas = ("err",) if nodo_ast.tipo == "ERROR_SINTACTICO" else ()
        nuevo_id = tree_sintactico.insert(padre_id, "end", text=texto_nodo, values=(_posicion(nodo_ast),),
                                          open=True, tags=etiquetas)
        for hijo in nodo_ast.hijos:
            renderizar_nodo_treeview(hijo, nuevo_id)

    renderizar_nodo_treeview(raiz_ast)


# --- SEMANTICO

def analisis_semantico(editor, tree_ast_widget, tabla_simbolos_widget, consola_errores_widget, consola_traza=None):
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
    if consola_traza is not None:
        consola_traza.delete("1.0", "end")

    # 3. Análisis Léxico y Sintáctico previo para obtener el AST
    sc = Scanner()
    tokens_validos, _ = sc.analizar(codigo)

    parser = AnalizadorSintactico(tokens_validos)
    raiz_ast = parser.parsear()
    completar_posiciones(raiz_ast)

    # Si hay errores sintácticos o el AST está vacío, detener (y marcarlos en el editor)
    if parser.errores or not raiz_ast:
        marcar_errores(editor, [(e['linea'], e['col'], None) for e in parser.errores])
        detalle = "\n".join(e['msg'] for e in parser.errores[:5]) or "El programa está vacío."
        messagebox.showerror(
            "Error Sintáctico",
            "Debes corregir los errores sintácticos antes de realizar el análisis semántico.\n\n" + detalle
        )
        return

    # 4. Ejecutar el Analizador Semántico
    analizador = SemanticAnalyzer()
    ast_anotado, tabla_simbolos, errores_semanticos = analizador.analyze(raiz_ast)

    # 4.1 Traza paso a paso: relación AST <-> tabla de símbolos (pestaña "Resultados")
    if consola_traza is not None:
        consola_traza.insert("end", "RECORRIDO DEL AST Y USO DE LA TABLA DE SÍMBOLOS   ([fila:columna] fase detalle)\n", "titulo")
        consola_traza.insert("end", "Declaración → INSERTAR | Uso → BUSCAR | Expresión → PROPAGAR tipo y valor | Asignación → COMPARAR tipos\n", "titulo")
        consola_traza.insert("end", "Atributos:  H = HEREDADO (baja del padre o de la tabla de símbolos)   S = SINTETIZADO (sube desde los hijos)\n\n", "titulo")
        for linea_traza in analizador.trace:
            etiqueta = "error" if "ERROR" in linea_traza else ("decl" if "DECLARACIÓN" in linea_traza else "normal")
            consola_traza.insert("end", linea_traza + "\n", etiqueta)

    # 5. Mostrar Errores Semánticos en el Treeview de errores
    if errores_semanticos:
        for err_msg in errores_semanticos:
            m = re.search(r"\[Línea (\d+)(?:, Col (\d+))?\]", err_msg)
            linea = m.group(1) if m else "-"
            col = m.group(2) if (m and m.group(2)) else "-"
            consola_errores_widget.insert("", "end", values=(linea, col, "Semántico", err_msg))
        messagebox.showwarning("Análisis Semántico", f"Se encontraron {len(errores_semanticos)} errores semánticos.")
    else:
        messagebox.showinfo("Análisis Semántico", "Análisis semántico completado con éxito sin errores.")

    # 5.1 Marcas rojas en el editor, en la posición exacta de cada error
    marcar_errores(editor, [(e['linea'], e['col'], e['largo']) for e in analizador.error_info if e['col']])

    # 6. Llenar la Tabla de Símbolos en la GUI (con el último valor conocido)
    if tabla_simbolos_widget and tabla_simbolos:
        for sym in tabla_simbolos.get_all_symbols():
            tabla_simbolos_widget.insert("", "end", values=(
                sym.name,
                sym.data_type,
                sym.line,
                sym.offset,
                sym.value_text
            ))

    # 7. Renderizar el AST Anotado: columnas Tipo, Valor y Fila:Col
    try:
        tree_ast_widget.tag_configure("err", foreground="#FF5555")
    except Exception:
        pass

    def renderizar_ast_anotado(nodo, padre_id=""):
        if not nodo:
            return
        texto_nodo = str(nodo.node_type)
        if nodo.value is not None and nodo.value != "":
            texto_nodo += f" : '{nodo.value}'"
        tipo = nodo.data_type or ""
        valor = formatear_valor(nodo.valor_calc)
        etiquetas = ("err",) if (nodo.tiene_error or tipo == 'error') else ()

        nuevo_id = tree_ast_widget.insert(padre_id, "end", text=texto_nodo,
                                          values=(tipo, valor, _atributos(nodo), _posicion(nodo)),
                                          open=True, tags=etiquetas)
        for hijo in nodo.children:
            renderizar_ast_anotado(hijo, nuevo_id)

    renderizar_ast_anotado(ast_anotado)
