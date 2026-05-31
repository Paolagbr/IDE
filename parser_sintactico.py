from ast_node import NodoAST

class AnalizadorSintactico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.token_actual = self.tokens[self.pos] if len(tokens) > 0 else None
        self.errores = []

    def avanzar(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.token_actual = self.tokens[self.pos]
        else:
            self.token_actual = None

    def consumir(self, tipo_esperado, valor_esperado=None):
        if self.token_actual:
            # Validación flexible: Si buscamos un valor exacto (como 'then'), 
            # no importa si el lexer lo llamó IDENTIFICADOR o RESERVADA, lo que nos importa es el texto.
            if valor_esperado and self.token_actual['valor'] == valor_esperado:
                nodo = NodoAST(self.token_actual['tipo'], self.token_actual['valor'])
                self.avanzar()
                return nodo
            
            # Validación por tipo estándar
            if not valor_esperado and self.token_actual['tipo'] == tipo_esperado:
                nodo = NodoAST(self.token_actual['tipo'], self.token_actual['valor'])
                self.avanzar()
                return nodo

        # Si no coincide, reportamos error de forma amigable
        esperado_str = valor_esperado if valor_esperado else tipo_esperado
        encontrado_str = self.token_actual['valor'] if self.token_actual else "EOF"
        self.reportar_error(f"Se esperaba '{esperado_str}' pero se encontró '{encontrado_str}'")
        return None

    def reportar_error(self, mensaje):
        if self.token_actual:
            info_err = {
                'linea': self.token_actual['linea'],
                'col': self.token_actual['col'],
                'msg': f"Error Sintáctico en Línea {self.token_actual['linea']}, Col {self.token_actual['col']}: {mensaje}"
            }
        else:
            info_err = {'linea': 'EOF', 'col': 'EOF', 'msg': f"Error Sintáctico al final del archivo: {mensaje}"}
        self.errores.append(info_err)
        self.sincronizar()

    def sincronizar(self):
        # Avanzar hasta encontrar un punto y coma o fin de bloque para no ciclarse
        while self.token_actual:
            if self.token_actual['valor'] in [';', '}']:
                self.avanzar()
                break
            self.avanzar()

    # --- REGLAS GRAMATICALES ADAPTADAS ---

    def parsear(self):
        return self.programa()

    def programa(self):
        nodo = NodoAST("PROGRAMA")
        nodo_main = self.consumir("RESERVADA", "main")
        nodo_llave_i = self.consumir("SIMBOLO", "{")
        
        if nodo_main: nodo.agregar_hijo(nodo_main)
        if nodo_llave_i: nodo.agregar_hijo(nodo_llave_i)

        while self.token_actual and self.token_actual['valor'] != '}':
            nodo_decl = self.declaracion()
            if nodo_decl:
                nodo.agregar_hijo(nodo_decl)
            else:
                break

        nodo_llave_d = self.consumir("SIMBOLO", "}")
        if nodo_llave_d: nodo.agregar_hijo(nodo_llave_d)
        return nodo

    def declaracion(self):
        if self.token_actual and self.token_actual['valor'] in ['int', 'float', 'bool']:
            return self.declaracion_variable()
        else:
            return self.lista_sentencias()

    def declaracion_variable(self):
        nodo = NodoAST("DECLARACION_VARIABLE")
        nodo_tipo = self.consumir("RESERVADA") # int, float, bool
        nodo.agregar_hijo(nodo_tipo)

        nodo_id = self.consumir("IDENTIFICADOR")
        nodo.agregar_hijo(nodo_id)

        while self.token_actual and self.token_actual['valor'] == ',':
            self.consumir("SIMBOLO", ",")
            nodo.agregar_hijo(self.consumir("IDENTIFICADOR"))

        self.consumir("SIMBOLO", ";")
        return nodo

    def lista_sentencias(self):
        nodo = NodoAST("LISTA_SENTENCIAS")
        # Frenar si encuentra elementos de clausura de la gramática
        while self.token_actual and self.token_actual['valor'] not in ['end', 'while', 'else', '}']:
            nodo_sent = self.sentencia()
            if nodo_sent:
                nodo.agregar_hijo(nodo_sent)
            else:
                break
        return nodo

    def sentencia(self):
        if not self.token_actual: return None
        val = self.token_actual['valor']
        
        if val == 'if': return self.seleccion()
        elif val == 'while': return self.iteracion()
        elif val == 'do': return self.repeticion()
        elif val == 'cin': return self.sent_in()
        elif val == 'cout': return self.sent_out()
        elif self.token_actual['tipo'] == 'IDENTIFICADOR': return self.asignacion()
        else:
            return self.sent_expresion()

    def asignacion(self):
        nodo = NodoAST("ASIGNACION")
        nodo.agregar_hijo(self.consumir("IDENTIFICADOR"))
        nodo.agregar_hijo(self.consumir("ASIGNACION", "="))
        nodo.agregar_hijo(self.expresion())
        self.consumir("SIMBOLO", ";")
        return nodo

    def sent_expresion(self):
        nodo = NodoAST("SENT_EXPRESION")
        if self.token_actual and self.token_actual['valor'] != ';':
            nodo.agregar_hijo(self.expresion())
        self.consumir("SIMBOLO", ";")
        return nodo

    def seleccion(self):
        nodo = NodoAST("SELECCION_IF")
        nodo.agregar_hijo(self.consumir("RESERVADA", "if"))
        nodo.agregar_hijo(self.expresion())
        
        # 'then' se consume por valor directo sin importar qué tipo le dio tu lexer
        nodo.agregar_hijo(self.consumir(self.token_actual['tipo'] if self.token_actual else "", "then"))
        nodo.agregar_hijo(self.lista_sentencias())
        
        if self.token_actual and self.token_actual['valor'] == 'else':
            nodo.agregar_hijo(self.consumir("RESERVADA", "else"))
            nodo.agregar_hijo(self.lista_sentencias())
            
        nodo.agregar_hijo(self.consumir("RESERVADA", "end"))
        return nodo

    def iteracion(self):
        nodo = NodoAST("ITERACION_WHILE")
        nodo.agregar_hijo(self.consumir("RESERVADA", "while"))
        nodo.agregar_hijo(self.expresion())
        nodo.agregar_hijo(self.lista_sentencias())
        nodo.agregar_hijo(self.consumir("RESERVADA", "end"))
        return nodo

    def repeticion(self):
        nodo = NodoAST("REPETICION_DO")
        nodo.agregar_hijo(self.consumir("RESERVADA", "do"))
        nodo.agregar_hijo(self.lista_sentencias())
        nodo.agregar_hijo(self.consumir("RESERVADA", "while"))
        nodo.agregar_hijo(self.expresion())
        self.consumir("SIMBOLO", ";")
        return nodo

    def sent_in(self):
        nodo = NodoAST("CIN")
        nodo.agregar_hijo(self.consumir("RESERVADA", "cin"))
        nodo.agregar_hijo(self.consumir("OP_LOG_REL", ">>"))
        nodo.agregar_hijo(self.consumir("IDENTIFICADOR"))
        self.consumir("SIMBOLO", ";")
        return nodo

    def sent_out(self):
        nodo = NodoAST("COUT")
        nodo.agregar_hijo(self.consumir("RESERVADA", "cout"))
        nodo.agregar_hijo(self.consumir("OP_LOG_REL", "<<"))
        nodo.agregar_hijo(self.salida())
        return nodo

    def salida(self):
        nodo = NodoAST("SALIDA")
        # Validar si viene una cadena o una expresión común
        if self.token_actual and (self.token_actual['valor'].startswith('"') or self.token_actual['tipo'] == 'SIMBOLO' and self.token_actual['valor'] == '"'):
            nodo.agregar_hijo(NodoAST("CADENA", self.token_actual['valor']))
            self.avanzar()
        else:
            nodo.agregar_hijo(self.expresion())
            
        while self.token_actual and self.token_actual['valor'] == '<<':
            self.consumir("OP_LOG_REL", "<<")
            if self.token_actual and self.token_actual['valor'].startswith('"'):
                nodo.agregar_hijo(NodoAST("CADENA", self.token_actual['valor']))
                self.avanzar()
            else:
                nodo.agregar_hijo(self.expresion())
                
        self.consumir("SIMBOLO", ";")
        return nodo

    def expresion(self):
        nodo = NodoAST("EXPRESION")
        nodo.agregar_hijo(self.expresion_simple())
        if self.token_actual and self.token_actual['tipo'] == 'OP_LOG_REL' and self.token_actual['valor'] in ['<', '<=', '>', '>=', '==', '!=']:
            nodo.agregar_hijo(self.consumir("OP_LOG_REL"))
            nodo.agregar_hijo(self.expresion_simple())
        return nodo

    def expresion_simple(self):
        nodo = NodoAST("EXPRESION_SIMPLE")
        nodo.agregar_hijo(self.termino())
        while self.token_actual and self.token_actual['tipo'] == 'OP_ARITMETICO' and self.token_actual['valor'] in ['+', '-', '++', '--']:
            nodo.agregar_hijo(self.consumir("OP_ARITMETICO"))
            nodo.agregar_hijo(self.termino())
        return nodo

    def termino(self):
        nodo = NodoAST("TERMINO")
        nodo.agregar_hijo(self.factor())
        while self.token_actual and self.token_actual['tipo'] == 'OP_ARITMETICO' and self.token_actual['valor'] in ['*', '/', '%']:
            nodo.agregar_hijo(self.consumir("OP_ARITMETICO"))
            nodo.agregar_hijo(self.factor())
        return nodo

    def factor(self):
        nodo = NodoAST("FACTOR")
        nodo.agregar_hijo(self.componente())
        while self.token_actual and self.token_actual['valor'] == '^':
            nodo.agregar_hijo(self.consumir("OP_ARITMETICO", "^"))
            nodo.agregar_hijo(self.componente())
        return nodo

    def componente(self):
        nodo = NodoAST("COMPONENTE")
        if not self.token_actual: return nodo
        
        if self.token_actual['valor'] == '(':
            self.consumir("SIMBOLO", "(")
            nodo.agregar_hijo(self.expresion())
            self.consumir("SIMBOLO", ")")
        elif self.token_actual['tipo'] == 'NUMERO':
            nodo.agregar_hijo(self.consumir("NUMERO"))
        elif self.token_actual['tipo'] == 'IDENTIFICADOR':
            nodo.agregar_hijo(self.consumir("IDENTIFICADOR"))
        elif self.token_actual['valor'] in ['&&', '||', '!']:
            nodo.agregar_hijo(self.consumir("OP_LOG_REL"))
            nodo.agregar_hijo(self.componente())
        else:
            self.reportar_error(f"Componente inválido: {self.token_actual['valor']}")
        return nodo