# semantico.py
# Analizador Semántico y Tabla de Símbolos para el Compilador.
# Trabaja sobre el AST real de parser_sintactico.py (nodos con etiquetas como
# "Decl_Variable (int)", "Nodo_Asignar (id: x)", "Op_Aritmetico: +", "Literal: 10"...).
import re
import math

NUMERICOS = ('int', 'float')


class _Desconocido:
    """Valor que no se puede conocer al compilar (viene de cin, de un ciclo, etc.)."""
    def __repr__(self):
        return '?'
    __str__ = __repr__


UNK = _Desconocido()


def formatear_valor(v):
    """Texto de un valor para mostrarlo en la interfaz ('' si no aplica, '?' si se desconoce)."""
    if v is None:
        return ''
    if v is UNK:
        return '?'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float):
        if v != v or v in (float('inf'), float('-inf')):
            return str(v)
        return repr(round(v, 10))
    return str(v)


class Symbol:
    """Representa una entrada en la Tabla de Símbolos."""
    def __init__(self, name, data_type, line, offset=0, col=None):
        self.name = name           # Nombre de la variable
        self.data_type = data_type # Tipo: 'int', 'float', 'bool'
        self.lines = [line] if line is not None else []        # Línea de declaración y de uso
        self.col = col             # Columna de la declaración
        self.offset = offset       # Dirección / Desplazamiento de memoria
        self.value = UNK           # Último valor conocido (se va "arrastrando" en el recorrido)

    @property
    def line(self):
        """Devuelve las líneas de uso ordenadas y separadas por comas."""
        return ", ".join(map(str, sorted(self.lines)))

    @property
    def value_text(self):
        return formatear_valor(self.value)

    def add_line(self, line):
        """Registra una línea nueva sin repetir las existentes."""
        if line is not None and line not in self.lines:
            self.lines.append(line)

    def __repr__(self):
        return f"Symbol(name='{self.name}', type='{self.data_type}', line={self.line}, offset={self.offset}, value={self.value_text})"


class SymbolTable:
    """Tabla de Símbolos basada en un diccionario."""
    def __init__(self):
        self.symbols = {}
        self.current_offset = 0

    def insert(self, name, data_type, line, col=None):
        """Inserta una variable. Retorna (True, None) o (False, mensaje_error)."""
        if name in self.symbols:
            return False, f"Error semántico [Línea {line}]: Declaración duplicada de la variable '{name}'."

        size = 8 if data_type == 'float' else (1 if data_type == 'bool' else 4)
        self.symbols[name] = Symbol(name, data_type, line, self.current_offset, col)
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


# Marca de atributo que se agrega a cada línea de la traza:
#   H = HEREDADO   (baja desde el padre / el entorno hacia el nodo)
#   S = SINTETIZADO (sube desde los hijos hacia el nodo)
SUFIJO_ATRIBUTO = {
    "DECLARACIÓN": "  [tipo: H]",
    "LITERAL":     "  [tipo, valor: S]",
    "USO":         "  [tipo, valor: S]",
    "EXPRESIÓN":   "  [tipo, valor: S]",
    "ASIGNACIÓN":  "  [tipo del destino: H | valor: S]",
}


class SemanticAnalyzer:
    """Recorre y anota el AST: tipos, valores conocidos, tabla de símbolos y errores."""
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []        # Textos "Error semántico [Línea X, Col Y]: ..."
        self.error_info = []    # Lo mismo, pero estructurado: {'linea','col','largo','msg'}
        self.trace = []         # Bitácora paso a paso de la relación AST <-> tabla de símbolos
        self.valores = {}       # { nombre: valor conocido }  (si falta, el valor se desconoce)

    # ---------- utilidades ----------
    def log(self, linea, col, fase, texto):
        pos = f"{linea}:{col}" if col else f"{linea}"
        sufijo = "" if "ERROR" in texto else SUFIJO_ATRIBUTO.get(fase, "")
        self.trace.append(f"[{pos}]".ljust(8) + f" {fase:<11} {texto}{sufijo}")

    def add_error(self, message, line, col=None, largo=None, nodo=None):
        pos = f"Línea {line}, Col {col}" if col else f"Línea {line}"
        self.errors.append(f"Error semántico [{pos}]: {message}")
        self.error_info.append({'linea': line, 'col': col, 'largo': largo, 'msg': message})
        if nodo is not None:
            nodo.tiene_error = True

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

    @staticmethod
    def _atributos_de(et):
        """Clasifica los atributos de cada nodo del AST en heredados (H) y sintetizados (S)."""
        if et.startswith("Raiz_Programa"):
            return [("TS", "H")]                          # la tabla de símbolos baja desde la raíz
        if et.startswith("Decl_Variable"):
            return [("tipo", "S")]                        # sale del token int / float / bool
        if et.startswith(("Nodo_Asignar", "Nodo_Modificar")):
            return [("tipo", "H"), ("valor", "S")]        # tipo del destino: viene de la TS
        if et in ("Eval_Condicion", "Condicion_Ciclo", "Condicion_Termino"):
            return [("tipo", "S"), ("valor", "S")]
        if et == "Exp_Impresion":
            return [("valor", "S")]
        if et.startswith(("Literal", "Id_Token", "Op_")):
            return [("tipo", "S"), ("valor", "S")]
        return []

    @staticmethod
    def valor_de(nodo):
        v = getattr(nodo, 'valor_calc', None)
        return UNK if v is None else v

    def _linea(self, nodo, linea_padre):
        lin = getattr(nodo, 'line', None)
        # 1 es el valor por defecto de ASTNode; se hereda la del padre si hay una mejor
        if lin in (None, 0) or (lin == 1 and linea_padre not in (None, 1)):
            return linea_padre if linea_padre is not None else 1
        return lin

    def _declarada(self, nombre, linea, col=None, nodo=None):
        """USO de un identificador: BUSCAR en la tabla y devolver su tipo."""
        sym = self.symbol_table.lookup(nombre)
        if sym is None:
            self.log(linea, col, "USO", f"{nombre}  → BUSCAR en tabla → NO ENCONTRADO  ✗ ERROR")
            self.add_error(f"Variable '{nombre}' no declarada.", linea, col, len(nombre), nodo)
            return None
        self.symbol_table.add_reference(nombre, linea)
        actual = formatear_valor(self.valores.get(nombre, UNK))
        self.log(linea, col, "USO", f"{nombre}  → BUSCAR en tabla → encontrado, tipo {sym.data_type}, valor actual {actual}")
        return sym.data_type

    # ---------- punto de entrada ----------
    def analyze(self, ast_root):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.error_info = []
        self.trace = []
        self.valores = {}
        if ast_root:
            self.visit(ast_root, None)
        for sym in self.symbol_table.get_all_symbols():
            sym.value = self.valores.get(sym.name, UNK)
        return ast_root, self.symbol_table, self.errors

    # ---------- variables modificadas dentro de un bloque ----------
    def _asignadas(self, nodo, acumulado=None):
        acumulado = set() if acumulado is None else acumulado
        et = str(nodo.node_type)
        if et.startswith(("Nodo_Asignar", "Nodo_Modificar")):
            n = self._nombre_en_etiqueta(et)
            if n:
                acumulado.add(n)
        elif et.startswith("Stream_Entrada"):
            for h in nodo.children:
                if ":" in str(h.node_type):
                    acumulado.add(self._valor_etiqueta(str(h.node_type)))
        for h in nodo.children:
            self._asignadas(h, acumulado)
        return acumulado

    # ---------- sentencias ----------
    def visit(self, nodo, linea_padre):
        if nodo is None:
            return
        et = str(nodo.node_type)
        linea = self._linea(nodo, linea_padre)
        col = getattr(nodo, 'col', None)
        nodo.atributos = self._atributos_de(et)

        if et.startswith("Decl_Variable"):
            m = re.search(r"\((\w+)\)", et)
            tipo_var = m.group(1) if m else 'int'
            self._anotar(nodo, tipo_var)
            for h in nodo.children:
                nombre = self._valor_etiqueta(str(h.node_type))
                lin_h = self._linea(h, linea)
                col_h = getattr(h, 'col', None)
                ok, _msg = self.symbol_table.insert(nombre, tipo_var, lin_h, col_h)
                if not ok:
                    previa = self.symbol_table.lookup(nombre)
                    donde = f"en la línea {previa.lines[0]}" + (f", col {previa.col}" if previa.col else "")
                    cambio = f" (con otro tipo tampoco se permite: antes era {previa.data_type})" if previa.data_type != tipo_var else ""
                    self.add_error(f"Declaración duplicada de la variable '{nombre}': ya fue declarada {donde}{cambio}.",
                                   lin_h, col_h, len(nombre), h)
                    self.log(lin_h, col_h, "DECLARACIÓN", f"{nombre} : {tipo_var}  → INSERTAR en tabla → ya existe  ✗ ERROR (duplicada)")
                    h.duplicado = True      # no se vuelve a dibujar en el árbol
                else:
                    off = self.symbol_table.lookup(nombre).offset
                    self.log(lin_h, col_h, "DECLARACIÓN", f"{nombre} : {tipo_var}  → INSERTAR en tabla (offset {off})")
                    self.valores.pop(nombre, None)
                self._anotar(h, tipo_var)
                h.atributos = [("tipo", "H")]       # int x, y  →  x.tipo = y.tipo = Decl_Variable.tipo
            # una variable duplicada aparece una sola vez en el árbol
            nodo.children[:] = [h for h in nodo.children if not getattr(h, 'duplicado', False)]
            if not nodo.children:
                nodo.duplicado = True

        elif et.startswith("Nodo_Asignar"):
            nombre = self._nombre_en_etiqueta(et)
            tipo_var = self._declarada(nombre, linea, col, nodo) if nombre else None

            # Si la variable no está declarada, marcar el nodo explícitamente como 'error'
            self._anotar(nodo, tipo_var if tipo_var else 'error')

            nuevo = UNK
            for h in nodo.children:
                tipo_exp = self.tipo_expr(h, linea)
                val_exp = self.valor_de(h)
                if tipo_var and tipo_exp and tipo_exp != 'error':
                    if tipo_var != tipo_exp and not (tipo_var == 'float' and tipo_exp == 'int'):
                        self.log(linea, col, "ASIGNACIÓN", f"{nombre} ({tipo_var}) := {tipo_exp}  → COMPARAR tipos → ✗ ERROR incompatibles")
                        self.add_error(f"No se puede asignar un valor '{tipo_exp}' a la variable '{nombre}' de tipo '{tipo_var}'.",
                                       linea, col, len(nombre), nodo)
                        self._anotar(nodo, 'error')  # Propagar error si los tipos chocan
                    else:
                        nota = "  (int → float permitido)" if tipo_var != tipo_exp else ""
                        self.log(linea, col, "ASIGNACIÓN", f"{nombre} ({tipo_var}) := {tipo_exp}  → COMPARAR tipos → OK{nota}")
                        if val_exp is not UNK and tipo_var == 'float' and not isinstance(val_exp, bool):
                            val_exp = float(val_exp)
                        nuevo = val_exp
                        anterior = formatear_valor(self.valores.get(nombre, UNK))
                        self.log(linea, col, "VALOR", f"{nombre}: {anterior} → {formatear_valor(nuevo)}")
            if nombre and tipo_var:
                if nuevo is UNK:
                    self.valores.pop(nombre, None)
                else:
                    self.valores[nombre] = nuevo
            nodo.valor_calc = nuevo

        elif et.startswith("Nodo_Modificar"):
            nombre = self._nombre_en_etiqueta(et)
            tipo_var = self._declarada(nombre, linea, col, nodo) if nombre else None
            self._anotar(nodo, tipo_var if tipo_var else 'error')
            nuevo = UNK
            if tipo_var and tipo_var not in NUMERICOS:
                self.add_error(f"No se puede incrementar/decrementar '{nombre}' de tipo '{tipo_var}'.", linea, col, len(nombre), nodo)
                self._anotar(nodo, 'error')
            elif tipo_var:
                texto = " ".join(f"{h.node_type} {h.value or ''}" for h in nodo.children)
                delta = 1 if '++' in texto else (-1 if '--' in texto else 0)
                actual = self.valores.get(nombre, UNK)
                if actual is not UNK and delta:
                    nuevo = actual + delta
                    self.valores[nombre] = nuevo
                else:
                    self.valores.pop(nombre, None)
                self.log(linea, col, "VALOR", f"{nombre}: {formatear_valor(actual)} → {formatear_valor(nuevo)}  ({'++' if delta > 0 else '--'})")
            nodo.valor_calc = nuevo

        elif et.startswith("Stream_Entrada"):
            for h in nodo.children:
                if ":" in str(h.node_type):
                    nombre = self._valor_etiqueta(str(h.node_type))
                    lin_h = self._linea(h, linea)
                    col_h = getattr(h, 'col', None)
                    tipo = self._declarada(nombre, lin_h, col_h, h)
                    self._anotar(h, tipo if tipo else 'error')
                    h.atributos = [("tipo", "H"), ("valor", "S")]
                    if tipo:
                        self.valores.pop(nombre, None)
                        h.valor_calc = UNK
                        self.log(lin_h, col_h, "ENTRADA", f"{nombre}  → el valor lo da el usuario (se desconoce al compilar)")

        elif et == "Exp_Impresion":
            for h in nodo.children:
                self.tipo_expr(h, linea)
                self.log(self._linea(h, linea), getattr(h, 'col', None), "SALIDA", f"valor mostrado: {formatear_valor(self.valor_de(h))}")

        elif et in ("Eval_Condicion", "Condicion_Ciclo", "Condicion_Termino"):
            valor = UNK
            tipos_cond = []
            for h in nodo.children:
                t = self.tipo_expr(h, linea)
                tipos_cond.append(t)
                valor = self.valor_de(h)
                if t == 'string':
                    self.add_error("La condición no puede ser una cadena de texto.", linea, getattr(h, 'col', None), 1, h)
            self._anotar(nodo, 'error' if 'error' in tipos_cond else 'bool')
            nodo.valor_calc = valor
            self.log(linea, col, "CONDICIÓN", f"valor de la condición: {formatear_valor(valor)}")

        elif et == "Sentencia_Control_IF":
            self._visitar_if(nodo, linea)

        elif et in ("Sentencia_Bucle_WHILE", "Sentencia_Bucle_DO_WHILE"):
            self._visitar_bucle(nodo, linea)

        elif et.startswith(("Op_", "Literal", "Id_Token")):
            self.tipo_expr(nodo, linea)

        else:
            for h in list(nodo.children):
                self.visit(h, linea)
            nodo.children[:] = [h for h in nodo.children if not getattr(h, 'duplicado', False)]

    def _visitar_if(self, nodo, linea):
        cond = next((h for h in nodo.children if h.node_type == "Eval_Condicion"), None)
        rama_then = next((h for h in nodo.children if h.node_type == "Rama_True_Then"), None)
        rama_else = next((h for h in nodo.children if h.node_type == "Rama_False_Else"), None)

        if cond is not None:
            self.visit(cond, linea)
        c = self.valor_de(cond) if cond is not None else UNK
        verdad = UNK if c is UNK else bool(c)

        base = dict(self.valores)
        self.valores = dict(base)
        if rama_then is not None:
            self.visit(rama_then, linea)
        estado_then = self.valores

        self.valores = dict(base)
        if rama_else is not None:
            self.visit(rama_else, linea)
        estado_else = self.valores

        if verdad is True:
            self.valores = estado_then       # la rama else es inalcanzable
            self.log(linea, getattr(nodo, 'col', None), "FLUJO", "condición verdadera → se arrastran los valores de la rama then")
        elif verdad is False:
            self.valores = estado_else       # la rama then es inalcanzable
            self.log(linea, getattr(nodo, 'col', None), "FLUJO", "condición falsa → se arrastran los valores de la rama else")
        else:
            # condición desconocida: solo se conserva lo que vale lo mismo en ambas ramas
            self.valores = {k: v for k, v in estado_then.items()
                            if k in estado_else and type(estado_else[k]) == type(v) and estado_else[k] == v}

    def _visitar_bucle(self, nodo, linea):
        modificadas = self._asignadas(nodo)
        for n in sorted(modificadas):
            if n in self.valores:
                self.valores.pop(n)
                self.log(linea, getattr(nodo, 'col', None), "CICLO", f"{n}  → deja de tener valor conocido (cambia dentro del ciclo)")
        for h in list(nodo.children):
            self.visit(h, linea)
        for n in modificadas:        # al salir del ciclo no se sabe cuántas vueltas dio
            self.valores.pop(n, None)

    # ---------- expresiones ----------
    @staticmethod
    def _div_ent(a, b):
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b > 0) else -q

    def _calcular(self, op, a, b, tipo, linea, col, nodo):
        try:
            if op == '+':
                r = a + b
            elif op == '-':
                r = a - b
            elif op == '*':
                r = a * b
            elif op == '/':
                if b == 0:
                    self.add_error("División entre cero.", linea, col, 1, nodo)
                    return UNK
                r = a / b if tipo == 'float' else self._div_ent(int(a), int(b))
            elif op == '%':
                if b == 0:
                    self.add_error("Módulo entre cero.", linea, col, 1, nodo)
                    return UNK
                r = math.fmod(a, b) if tipo == 'float' else int(a) - int(b) * self._div_ent(int(a), int(b))
            elif op == '^':
                r = float(a) ** b if (b < 0 or abs(b) > 64) else a ** b
            else:
                return UNK
            return float(r) if tipo == 'float' else int(r)
        except (OverflowError, ValueError, ZeroDivisionError):
            return UNK

    def tipo_expr(self, nodo, linea_padre):
        if nodo is None:
            return None
        et = str(nodo.node_type)
        linea = self._linea(nodo, linea_padre)
        col = getattr(nodo, 'col', None)
        resultado = None
        valor = UNK
        nodo.atributos = self._atributos_de(et)

        if et.startswith("Literal"):
            txt = self._valor_etiqueta(et)
            try:
                if txt in ('true', 'false'):
                    resultado, valor = 'bool', (txt == 'true')
                elif '.' in txt:
                    resultado, valor = 'float', float(txt)
                else:
                    resultado, valor = 'int', int(txt)
            except ValueError:
                resultado = 'float' if '.' in txt else 'int'
            self.log(linea, col, "LITERAL", f"{txt}  → tipo {resultado}")

        elif et.startswith("Id_Token"):
            nombre = self._valor_etiqueta(et)
            resultado = self._declarada(nombre, linea, col, nodo) or 'error'
            if resultado != 'error':
                valor = self.valores.get(nombre, UNK)

        elif et.startswith(("Op_Aritmetico", "Op_Multiplicativo", "Op_Potencia")):
            op = self._valor_etiqueta(et)
            tipos = [self.tipo_expr(h, linea) for h in nodo.children]
            vals = [self.valor_de(h) for h in nodo.children]
            if 'error' in tipos:
                resultado = 'error'
            elif any(t not in NUMERICOS for t in tipos if t):
                malo = next(t for t in tipos if t and t not in NUMERICOS)
                self.add_error(f"El operador '{op}' solo acepta operandos numéricos (se encontró '{malo}').", linea, col, len(op), nodo)
                resultado = 'error'
            else:
                resultado = 'float' if 'float' in tipos else 'int'
                detalle = ""
                if len(vals) == 2 and all(v is not UNK for v in vals):
                    valor = self._calcular(op, vals[0], vals[1], resultado, linea, col, nodo)
                    detalle = f";  {formatear_valor(vals[0])} {op} {formatear_valor(vals[1])} = {formatear_valor(valor)}"
                self.log(linea, col, "EXPRESIÓN", f"{f' {op} '.join(str(t) for t in tipos)}  → tipo {resultado}{detalle}")

        elif et.startswith("Op_Relacional"):
            op = self._valor_etiqueta(et)
            tipos = [self.tipo_expr(h, linea) for h in nodo.children]
            vals = [self.valor_de(h) for h in nodo.children]
            if 'error' in tipos:
                resultado = 'error'
            else:
                if len(tipos) == 2 and tipos[0] != tipos[1] and not (tipos[0] in NUMERICOS and tipos[1] in NUMERICOS):
                    self.add_error(f"Incompatibilidad de tipos en '{op}': '{tipos[0]}' y '{tipos[1]}'.", linea, col, len(op), nodo)
                elif len(vals) == 2 and all(v is not UNK for v in vals):
                    a, b = vals
                    valor = {'<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b, '==': a == b, '!=': a != b}.get(op, UNK)
                self.log(linea, col, "EXPRESIÓN", f"{f' {op} '.join(str(t) for t in tipos)}  → tipo bool;  valor {formatear_valor(valor)}")
                resultado = 'bool'

        elif et.startswith("Op_Logico"):
            op = self._valor_etiqueta(et)
            tipos = [self.tipo_expr(h, linea) for h in nodo.children]
            vals = [self.valor_de(h) for h in nodo.children]
            if 'error' in tipos:
                resultado = 'error'
            else:
                if 'string' in tipos:
                    self.add_error(f"El operador '{op}' no acepta cadenas de texto.", linea, col, len(op), nodo)
                elif all(v is not UNK for v in vals) and vals:
                    if op == '!':
                        valor = not vals[0]
                    elif op == '&&' and len(vals) == 2:
                        valor = bool(vals[0]) and bool(vals[1])
                    elif op == '||' and len(vals) == 2:
                        valor = bool(vals[0]) or bool(vals[1])
                self.log(linea, col, "EXPRESIÓN", f"operador '{op}'  → tipo bool;  valor {formatear_valor(valor)}")
                resultado = 'bool'

        else:
            for h in nodo.children:
                self.tipo_expr(h, linea)

        self._anotar(nodo, resultado)
        nodo.valor_calc = valor
        return resultado

