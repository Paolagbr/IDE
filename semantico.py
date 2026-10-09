# semantico.py
# Analizador Semántico y Tabla de Símbolos para el Compilador.
# Trabaja sobre el AST real de parser_sintactico.py (nodos con etiquetas como
# "Decl_Variable (int)", "Nodo_Asignar (id: x)", "Op_Aritmetico: +", "Literal: 10"...).
import re

NUMERICOS = ('int', 'float')


class Symbol:
    """Representa una entrada en la Tabla de Símbolos."""
    def __init__(self, name, data_type, line, offset=0):
        self.name = name           # Nombre de la variable
        self.data_type = data_type # Tipo: 'int', 'float', 'bool'
        self.lines = [line] if line is not None else []        # Línea de declaración
        self.offset = offset       # Dirección / Desplazamiento de memoria
    
    @property
    def line(self):
            """Devuelve las líneas de uso ordenadas y separadas por comas."""
            return ", ".join(map(str, sorted(self.lines)))

    def add_line(self, line):
            """Registra una línea nueva sin repetir las existentes."""
            if line is not None and line not in self.lines:
                self.lines.append(line)

    def add_reference(self, name, line):
            """Registra una nueva aparición de una variable ya declarada."""
            sym = self.lookup(name)
            if sym:
                sym.add_line(line)   

    def __repr__(self):
        return f"Symbol(name='{self.name}', type='{self.data_type}', line={self.line}, offset={self.offset})"

  

class SymbolTable:
    """Tabla de Símbolos basada en un diccionario."""
    def __init__(self):
        self.symbols = {}
        self.current_offset = 0

    def insert(self, name, data_type, line):
        """Inserta una variable. Retorna (True, None) o (False, mensaje_error)."""
        if name in self.symbols:
            return False, f"Error semántico [Línea {line}]: Declaración duplicada de la variable '{name}'."

        size = 8 if data_type == 'float' else (1 if data_type == 'bool' else 4)
        self.symbols[name] = Symbol(name, data_type, line, self.current_offset)
        self.current_offset += size
        return True, None

    def lookup(self, name):
        return self.symbols.get(name, None)

    def get_all_symbols(self):
        return list(self.symbols.values())
    
    def add_reference(self, name, line):
        """Registra una nueva aparición de una variable ya declarada."""
        sym = self.lookup(name)
        if sym:
            sym.add_line(line)


class SemanticAnalyzer:
    """Recorre y anota el AST aplicando las reglas semánticas y la verificación de tipos."""
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []

    # ---------- utilidades ----------
    def add_error(self, message, line):
        self.errors.append(f"Error semántico [Línea {line}]: {message}")

    @staticmethod
    def _anotar(nodo, tipo):
        nodo.data_type = tipo
        nodo.dtype = tipo

    @staticmethod
    def _valor_etiqueta(etiqueta):
        """'Literal: 10' -> '10'   |   'Op_Aritmetico: +' -> '+'"""
        return etiqueta.split(":", 1)[1].strip() if ":" in etiqueta else etiqueta

    @staticmethod
    def _nombre_en_etiqueta(etiqueta):
        m = re.search(r"id:\s*(\w+)", etiqueta)
        return m.group(1) if m else None

    def _linea(self, nodo, linea_padre):
        lin = getattr(nodo, 'line', None)
        # 1 es el valor por defecto de ASTNode; se hereda la del padre si hay una mejor
        if lin in (None, 0) or (lin == 1 and linea_padre not in (None, 1)):
            return linea_padre if linea_padre is not None else 1
        return lin

    def _declarada(self, nombre, linea):
        sym = self.symbol_table.lookup(nombre)
        if sym is None:
            self.add_error(f"Variable '{nombre}' no declarada.", linea)
            return None
        self.symbol_table.add_reference(nombre, linea)
        return sym.data_type

    # ---------- punto de entrada ----------
    def analyze(self, ast_root):
        self.symbol_table = SymbolTable()
        self.errors = []
        if ast_root:
            self.visit(ast_root, None)
        return ast_root, self.symbol_table, self.errors

    # ---------- sentencias ----------
    def visit(self, nodo, linea_padre):
        if nodo is None:
            return
        et = str(nodo.node_type)
        linea = self._linea(nodo, linea_padre)

        if et.startswith("Decl_Variable"):
            m = re.search(r"\((\w+)\)", et)
            tipo_var = m.group(1) if m else 'int'
            self._anotar(nodo, tipo_var)
            for h in nodo.children:
                nombre = self._valor_etiqueta(str(h.node_type))
                lin_h = self._linea(h, linea)
                ok, err = self.symbol_table.insert(nombre, tipo_var, lin_h)
                if not ok:
                    self.errors.append(err)
                self._anotar(h, tipo_var)
        elif et.startswith("Nodo_Asignar"):
            nombre = self._nombre_en_etiqueta(et)
            tipo_var = self._declarada(nombre, linea) if nombre else None
            
            # Si la variable no está declarada, marcar el nodo explícitamente como 'error'
            if not tipo_var:
                self._anotar(nodo, 'error')
            else:
                self._anotar(nodo, tipo_var)

            for h in nodo.children:
                tipo_exp = self.tipo_expr(h, linea)
                if tipo_var and tipo_exp and tipo_exp != 'error':
                    if tipo_var != tipo_exp and not (tipo_var == 'float' and tipo_exp == 'int'):
                        self.add_error(f"No se puede asignar un valor '{tipo_exp}' a la variable '{nombre}' de tipo '{tipo_var}'.", linea)
                        self._anotar(nodo, 'error') # Propagar error si los tipos chocan
        # elif et.startswith("Nodo_Asignar"):
        #     nombre = self._nombre_en_etiqueta(et)
        #     tipo_var = self._declarada(nombre, linea) if nombre else None
        #     self._anotar(nodo, tipo_var)
        #     for h in nodo.children:
        #         tipo_exp = self.tipo_expr(h, linea)
        #         if tipo_var and tipo_exp and tipo_exp != 'error':
        #             if tipo_var != tipo_exp and not (tipo_var == 'float' and tipo_exp == 'int'):
        #                 self.add_error(f"No se puede asignar un valor '{tipo_exp}' a la variable "
        #                                f"'{nombre}' de tipo '{tipo_var}'.", linea)

        elif et.startswith("Nodo_Modificar"):
            nombre = self._nombre_en_etiqueta(et)
            tipo_var = self._declarada(nombre, linea) if nombre else None
            self._anotar(nodo, tipo_var)
            if tipo_var and tipo_var not in NUMERICOS:
                self.add_error(f"No se puede incrementar/decrementar '{nombre}' de tipo '{tipo_var}'.", linea)

        elif et.startswith("Stream_Entrada"):
            for h in nodo.children:
                if ":" in str(h.node_type):
                    nombre = self._valor_etiqueta(str(h.node_type))
                    self._anotar(h, self._declarada(nombre, self._linea(h, linea)))

        elif et == "Exp_Impresion":
            for h in nodo.children:
                self.tipo_expr(h, linea)

        elif et in ("Eval_Condicion", "Condicion_Ciclo", "Condicion_Termino"):
            for h in nodo.children:
                t = self.tipo_expr(h, linea)
                if t == 'string':
                    self.add_error("La condición no puede ser una cadena de texto.", linea)

        elif et.startswith(("Op_", "Literal", "Id_Token")):
            self.tipo_expr(nodo, linea)

        else:
            for h in nodo.children:
                self.visit(h, linea)

    # ---------- expresiones ----------
    def tipo_expr(self, nodo, linea_padre):
        if nodo is None:
            return None
        et = str(nodo.node_type)
        linea = self._linea(nodo, linea_padre)
        resultado = None

        if et.startswith("Literal"):
            valor = self._valor_etiqueta(et)
            if valor in ('true', 'false'):
                resultado = 'bool'
            else:
                resultado = 'float' if '.' in valor else 'int'

        elif et.startswith("Id_Token"):
            nombre = self._valor_etiqueta(et)
            resultado = self._declarada(nombre, linea) or 'error'

        elif et.startswith(("Op_Aritmetico", "Op_Multiplicativo", "Op_Potencia")):
            op = self._valor_etiqueta(et)
            tipos = [self.tipo_expr(h, linea) for h in nodo.children]
            if 'error' in tipos:
                resultado = 'error'
            elif any(t not in NUMERICOS for t in tipos if t):
                malo = next(t for t in tipos if t and t not in NUMERICOS)
                self.add_error(f"El operador '{op}' solo acepta operandos numéricos (se encontró '{malo}').", linea)
                resultado = 'error'
            else:
                resultado = 'float' if 'float' in tipos else 'int'

        elif et.startswith("Op_Relacional"):
            op = self._valor_etiqueta(et)
            tipos = [self.tipo_expr(h, linea) for h in nodo.children]
            if 'error' in tipos:
                resultado = 'error'
            else:
                if len(tipos) == 2 and tipos[0] != tipos[1] and not (
                        tipos[0] in NUMERICOS and tipos[1] in NUMERICOS):
                    self.add_error(f"Incompatibilidad de tipos en '{op}': '{tipos[0]}' y '{tipos[1]}'.", linea)
                resultado = 'bool'

        elif et.startswith("Op_Logico"):
            op = self._valor_etiqueta(et)
            tipos = [self.tipo_expr(h, linea) for h in nodo.children]
            if 'error' in tipos:
                resultado = 'error'
            else:
                if 'string' in tipos:
                    self.add_error(f"El operador '{op}' no acepta cadenas de texto.", linea)
                resultado = 'bool'

        else:
            for h in nodo.children:
                self.tipo_expr(h, linea)

        self._anotar(nodo, resultado)
        return resultado
