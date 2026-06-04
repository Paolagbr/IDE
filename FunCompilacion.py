import subprocess
from tkinter import messagebox 
from scanner import Scanner
import funcionArchivos

import tkinter as tk
def ejecutar_fase(fase):

    archivo = funcionArchivos.ruta_actual
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
    
    for t in tokens_con_errores:
        if t['tipo'] == 'ERROR':
            consola.insert("end", f">>> Error léxico: '{t['valor']}' en línea {t['linea']}\n")
def analisis_sintactico():
    ejecutar_fase("sintactico")

def analisis_semantico():
    ejecutar_fase("semantico")

def codigo_intermedio():
    ejecutar_fase("intermedio")

def ejecutar_programa():
    ejecutar_fase("ejecutar")
# Función para análisis sintáctico con visualización del AST en Treeview
def analisis_sintactico(editor, tree_sintactico, consola_errores_sintacticos):
    if not editor: 
        messagebox.showwarning("Aviso", "No hay código activo para analizar.")
        return
        
    from scanner import Scanner
    from parser_sintactico import AnalizadorSintactico
    import tkinter as tk
    
    # 1. Ejecutar análisis léxico previo
    sc = Scanner()
    codigo = editor.get("1.0", "end-1c")
    tokens_validos, _ = sc.analizar(codigo)
    
    # 2. Inicializar Parser Sintáctico
    parser = AnalizadorSintactico(tokens_validos)
    raiz_ast = parser.parsear()
    
    # 3. Limpiar y rellenar consola de errores sintácticos
    consola_errores_sintacticos.delete("1.0", tk.END)
    if parser.errores:
        for err in parser.errores:
            consola_errores_sintacticos.insert(tk.END, f">>> {err['msg']}\n")
        #messagebox.showerror("Error Sintáctico", "Se detectaron problemas en la estructura sintáctica del programa.")
    else:
        consola_errores_sintacticos.insert(tk.END, ">>> Análisis Sintáctico completado con éxito. Estructura gramatical válida.\n")
        messagebox.showinfo("Éxito", "¡Estructura sintáctica totalmente válida!")

    # 4. Dibujar el AST Gráfico tipo Carpetas en el Treeview
    # Para que funcione, convertiremos la pestaña 'Sintáctico' del panel derecho en un Treeview jerárquico.
    for item in tree_sintactico.get_children():
        tree_sintactico.delete(item)
        
    def renderizar_nodo_treeview(nodo_ast, padre_id=""):
        if not nodo_ast: return
        texto_nodo = nodo_ast.tipo
        if nodo_ast.valor:
            texto_nodo += f" : '{nodo_ast.valor}'"
            
        nuevo_id = tree_sintactico.insert(padre_id, "end", text=texto_nodo, open=True)
        for hijo in nodo_ast.hijos:
            renderizar_nodo_treeview(hijo, nuevo_id)

    renderizar_nodo_treeview(raiz_ast)