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
            if valor_esperado and self.token_actual['valor'] == valor_esperado:
                nodo = NodoAST(self.token_actual['tipo'], self.token_actual['valor'])
                self.avanzar()
                return nodo
            if not valor_esperado and self.token_actual['tipo'] == tipo_esperado:
                nodo = NodoAST(self.token_actual['tipo'], self.token_actual['valor'])
                self.avanzar()
                return nodo

        esperado_str = valor_esperado if valor_esperado else tipo_esperado
        encontrado_str = self.token_actual['valor'] if self.token_actual else "EOF"
        self.reportar_error(f"Se esperaba '{esperado_str}' pero se encontró '{encontrado_str}'")
        
        # Retornamos un nodo falso en lugar de None para no romper la estructura del árbol
        return NodoAST("ERROR_SINTACTICO", esperado_str)

    def reportar_error(self, mensaje):
        if self.token_actual:
            info_err = {
                'linea': self.token_actual['linea'],
                'col': self.token_actual['col'],
                'msg': f"Error Sintactico en Linea {self.token_actual['linea']}, Col {self.token_actual['col']}: {mensaje}"
            }
        else:
            info_err = {'linea': 'EOF', 'col': 'EOF', 'msg': f"Error Sintactico al final del archivo: {mensaje}"}
        self.errores.append(info_err)
        
        # Sincronización suavizada: Solo saltamos hasta el final de la instrucción actual (;)
        # Evitamos saltar palabras clave como 'end' o '}' para no destruir bloques enteros del árbol.
        while self.token_actual and self.token_actual['valor'] not in [';', '}', 'end']:
            self.avanzar()
            
        if self.token_actual and self.token_actual['valor'] == ';':
            self.avanzar()

    # --- REGLAS GRAMATICALES ---

    def parsear(self):
        return self.programa()

    def programa(self):
        nodo = NodoAST("Raiz_Programa")
        try:
            self.consumir("RESERVADA", "main")
            
            if self.token_actual and self.token_actual['valor'] == '(':
                self.consumir("SIMBOLO", "(")
                self.consumir("SIMBOLO", ")")
                
            self.consumir("SIMBOLO", "{")

            while self.token_actual and self.token_actual['valor'] != '}':
                nodo_decl = self.declaracion()
                if nodo_decl:
                    nodo.agregar_hijo(nodo_decl)
                else:
                    if self.token_actual and self.token_actual['valor'] != '}':
                        self.avanzar()

            self.consumir("SIMBOLO", "}")
        except Exception as e:
            print(f"Error durante el parseo: {e}")
            
        return nodo  

    def declaracion(self):
        if self.token_actual and self.token_actual['valor'] in ['int', 'float', 'bool']:
            return self.declaracion_variable()
        else:
            return self.lista_sentencias()

    def declaracion_variable(self):
        nodo_tipo = self.token_actual['valor'] if self.token_actual else "tipo"
        nodo = NodoAST(f"Decl_Variable ({nodo_tipo})")
        self.avanzar() # Avanzamos de forma segura pasando el 'int' o 'float'

        nodo_id = self.consumir("IDENTIFICADOR")
        if nodo_id and nodo_id.tipo != "ERROR_SINTACTICO": 
            nodo.agregar_hijo(NodoAST(f"id: {nodo_id.valor}"))

        while self.token_actual and self.token_actual['valor'] == ',':
            self.consumir("SIMBOLO", ",")
            nodo_sig = self.consumir("IDENTIFICADOR")
            if nodo_sig and nodo_sig.tipo != "ERROR_SINTACTICO": 
                nodo.agregar_hijo(NodoAST(f"id: {nodo_sig.valor}"))

        self.consumir("SIMBOLO", ";")
        return nodo

    def lista_sentencias(self):
        nodo = NodoAST("Cuerpo_Instrucciones")
        # Quitamos 'while' de aquí para que los ciclos while normales puedan tener sub-sentencias sin romperse
        while self.token_actual and self.token_actual['valor'] not in ['end', 'else', '}', 'until']:
            pos_anterior = self.pos
            nodo_sent = self.sentencia()
            if nodo_sent:
                nodo.agregar_hijo(nodo_sent)
            if self.pos == pos_anterior:
                self.avanzar()
        
        if len(nodo.hijos) == 1:
            return nodo.hijos[0]
        return nodo if len(nodo.hijos) > 0 else None

    def sentencia(self):
        if not self.token_actual: 
            return None
        
        val = self.token_actual.get('valor', '')
        tipo = self.token_actual.get('tipo', '')
        
        if val == 'if': return self.seleccion()
        elif val == 'while': return self.iteracion()
        elif val == 'do': return self.repeticion()
        elif val == 'cin': return self.sent_in()
        elif val == 'cout': return self.sent_out()
        elif tipo == 'IDENTIFICADOR': 
            siguiente_token_val = ""
            siguiente_siguiente_val = ""
            if self.pos + 1 < len(self.tokens):
                siguiente_token_val = self.tokens[self.pos + 1].get('valor', '')
            if self.pos + 2 < len(self.tokens):
                siguiente_siguiente_val = self.tokens[self.pos + 2].get('valor', '')
                
            if siguiente_token_val in ['++', '--'] or (siguiente_token_val in ['+', '-'] and siguiente_siguiente_val == siguiente_token_val):
                return self.sent_incremento_decremento()
                
            return self.asignacion()
        else:
            return self.sent_expresion()
        
    def sent_incremento_decremento(self):
        nodo_id = self.consumir("IDENTIFICADOR")
        nodo = NodoAST(f"Nodo_Modificar (id: {nodo_id.valor if nodo_id else ''})")
        
        op = ""
        if self.token_actual and self.token_actual['valor'] in ['+', '-']:
            op += self.token_actual['valor']
            self.avanzar()
            if self.token_actual and self.token_actual['valor'] in ['+', '-']:
                op += self.token_actual['valor']
                self.avanzar()
        elif self.token_actual and self.token_actual['valor'] in ['++', '--']:
            op = self.token_actual['valor']
            self.avanzar()
            
        nodo.agregar_hijo(NodoAST(f"op: {op}"))
        self.consumir("SIMBOLO", ";")
        return nodo

    def asignacion(self):
        nodo_id = self.consumir("IDENTIFICADOR")
        nodo = NodoAST(f"Nodo_Asignar (id: {nodo_id.valor if nodo_id else ''})")
        self.consumir("ASIGNACION", "=")
        
        nodo_exp = self.expresion()
        if nodo_exp: 
            nodo.agregar_hijo(nodo_exp)
        self.consumir("SIMBOLO", ";")
        return nodo

    def sent_expresion(self):
        if self.token_actual and self.token_actual['valor'] == ';':
            self.consumir("SIMBOLO", ";")
            return None
            
        # Si nos topamos con una palabra estructural que abre bloques, salimos sin pedir ';'
        if self.token_actual and self.token_actual['valor'] in ['while', 'do', 'if', 'end', '}', 'then']:
            return None
            
        nodo_exp = self.expresion()
        
        # ¡EL CAMBIO AQUÍ!: Si después de la expresión sigue un 'do' o 'then', NO consumas ';'
        if self.token_actual and self.token_actual['valor'] in ['do', 'then']:
            return nodo_exp
            
        if nodo_exp:
            self.consumir("SIMBOLO", ";")
        return nodo_exp
    def seleccion(self):
        nodo = NodoAST("Sentencia_Control_IF")
        self.consumir("RESERVADA", "if")
        
        if self.token_actual and self.token_actual['valor'] == '(':
            self.consumir("SIMBOLO", "(")
            nodo_cond = self.expresion()
            self.consumir("SIMBOLO", ")")
        else:
            nodo_cond = self.expresion()
            
        if nodo_cond:
            nodo_bloque_cond = NodoAST("Eval_Condicion")
            nodo_bloque_cond.agregar_hijo(nodo_cond)
            nodo.agregar_hijo(nodo_bloque_cond)
            
        self.consumir(self.token_actual['tipo'] if self.token_actual else "", "then")
        
        nodo_then = self.lista_sentencias()
        if nodo_then:
            nodo_bloque_then = NodoAST("Rama_True_Then")
            nodo_bloque_then.agregar_hijo(nodo_then)
            nodo.agregar_hijo(nodo_bloque_then)
            
        if self.token_actual and self.token_actual['valor'] == 'else':
            self.consumir("RESERVADA", "else")
            nodo_else = self.lista_sentencias()
            if nodo_else:
                nodo_bloque_else = NodoAST("Rama_False_Else")
                nodo_bloque_else.agregar_hijo(nodo_else)
                nodo.agregar_hijo(nodo_bloque_else)
                
        self.consumir("RESERVADA", "end")
        return nodo

    def iteracion(self):
        nodo = NodoAST("Sentencia_Bucle_WHILE")
        self.consumir("RESERVADA", "while")
        
        if self.token_actual and self.token_actual['valor'] == '(':
            self.consumir("SIMBOLO", "(")
            nodo_cond = self.expresion()
            self.consumir("SIMBOLO", ")")
        else:
            nodo_cond = self.expresion()
            
        if nodo_cond:
            nodo_c = NodoAST("Condicion_Ciclo")
            nodo_c.agregar_hijo(nodo_cond)
            nodo.agregar_hijo(nodo_c)
        
        if self.token_actual and self.token_actual['valor'] == 'do':
            self.consumir("RESERVADA", "do") 
        
        nodo_Cuerpo = self.lista_sentencias()
        if nodo_Cuerpo:
            nodo_cp = NodoAST("Cuerpo_Ciclo")
            nodo_cp.agregar_hijo(nodo_Cuerpo)
            nodo.agregar_hijo(nodo_cp)
        
        self.consumir("RESERVADA", "end")
        return nodo

    # def repeticion(self):
    #     nodo = NodoAST("Sentencia_Bucle_DO_WHILE")
    #     self.consumir("RESERVADA", "do")
        
    #     # Procesamos el cuerpo. Si se topa con el 'while' de abajo, se detendrá si manejamos bien los tokens.
    #     nodo_cuerpo = self.lista_sentencias()
    #     if nodo_cuerpo:
    #         nodo_b = NodoAST("Bloque_Repetir")
    #         nodo_b.agregar_hijo(nodo_cuerpo)
    #         nodo.agregar_hijo(nodo_b)
            
    #     self.consumir("RESERVADA", "while")
        
    #     if self.token_actual and self.token_actual['valor'] == '(':
    #         self.consumir("SIMBOLO", "(")
    #         nodo_cond = self.expresion()
    #         self.consumir("SIMBOLO", ")")
    #     else:
    #         nodo_cond = self.expresion()
            
    #     if nodo_cond:
    #         nodo_t = NodoAST("Condicion_Termino")
    #         nodo_t.agregar_hijo(nodo_cond)
    #         nodo.agregar_hijo(nodo_t)
        
    #     self.consumir("SIMBOLO", ";")
    #     return nodo
    def repeticion(self):
        nodo = NodoAST("Sentencia_Bucle_DO_WHILE")
        self.consumir("RESERVADA", "do")

        nodo_b = NodoAST("Bloque_Repetir")

        while self.token_actual and self.token_actual['valor'] != 'while':
            nodo_sent = self.sentencia()
            if nodo_sent:
                nodo_b.agregar_hijo(nodo_sent)

        nodo.agregar_hijo(nodo_b)

        self.consumir("RESERVADA", "while")

        if self.token_actual and self.token_actual['valor'] == '(':
            self.consumir("SIMBOLO", "(")
            nodo_cond = self.expresion()
            self.consumir("SIMBOLO", ")")
        else:
            nodo_cond = self.expresion()

        nodo_t = NodoAST("Condicion_Termino")
        if nodo_cond:
            nodo_t.agregar_hijo(nodo_cond)

        nodo.agregar_hijo(nodo_t)

        self.consumir("SIMBOLO", ";")

        return nodo

    def sent_in(self):
        nodo = NodoAST("Stream_Entrada (cin)")
        self.consumir("RESERVADA", "cin")
        
        if self.token_actual and self.token_actual['valor'] == '>>':
            self.avanzar()
        elif self.token_actual and self.token_actual['valor'] == '>':
            self.avanzar()
            if self.token_actual and self.token_actual['valor'] == '>': 
                self.avanzar()
                
        nodo_id = self.consumir("IDENTIFICADOR")
        if nodo_id and nodo_id.tipo != "ERROR_SINTACTICO": 
            nodo.agregar_hijo(NodoAST(f"Destino_id: {nodo_id.valor}"))
        self.consumir("SIMBOLO", ";")
        return nodo

    def sent_out(self):
        nodo = NodoAST("Stream_Salida (cout)")
        self.consumir("RESERVADA", "cout")
        
        if self.token_actual and self.token_actual['valor'] == '<<':
            self.avanzar()
        elif self.token_actual and self.token_actual['valor'] == '<':
            self.avanzar()
            if self.token_actual and self.token_actual['valor'] == '<': 
                self.avanzar()
                
        nodo.agregar_hijo(self.salida())
        return nodo

    def salida(self):
        nodo = NodoAST("Exp_Impresion")
        
        if self.token_actual and (self.token_actual['valor'].startswith('"') or (self.token_actual['tipo'] == 'SIMBOLO' and self.token_actual['valor'] == '"')):
            nodo.agregar_hijo(NodoAST(f"Cadena Texto: {self.token_actual['valor']}"))
            self.avanzar()
        else:
            nodo_exp = self.expresion()
            if nodo_exp: 
                nodo.agregar_hijo(nodo_exp)
            
        while self.token_actual and self.token_actual['valor'] in ['<<', '<']:
            if self.token_actual['valor'] == '<<':
                self.avanzar()
            else:
                self.avanzar()
                if self.token_actual and self.token_actual['valor'] == '<': 
                    self.avanzar()
                
            if self.token_actual and self.token_actual['valor'].startswith('"'):
                nodo.agregar_hijo(NodoAST(f"Cadena Texto: {self.token_actual['valor']}"))
                self.avanzar()
            else:
                nodo_exp = self.expresion()
                if nodo_exp: 
                    nodo.agregar_hijo(nodo_exp)
                
        self.consumir("SIMBOLO", ";")
        return nodo

    # --- EXPRESIONES ---
    # --- EXPRESIONES ---
    
    # Nivel 1: Operadores Lógicos (Mayor jerarquía en la evaluación de condiciones)
    def expresion(self):
        # Primero evaluamos la parte relacional
        nodo_izq = self.expresion_relacional()
        
        # Después unimos con operadores lógicos si existen (&&, ||)
        while self.token_actual and self.token_actual['valor'] not in ['do', 'then', ';', ')', '('] and (self.token_actual['tipo'] in ['OP_LOG_REL', 'SIMBOLO'] and self.token_actual['valor'] in ['&&', '||']):
            nodo_op = NodoAST(f"Op_Logico: {self.token_actual['valor']}")
            self.avanzar()
            nodo_der = self.expresion_relacional()
            if nodo_izq: nodo_op.agregar_hijo(nodo_izq)
            if nodo_der: nodo_op.agregar_hijo(nodo_der)
            nodo_izq = nodo_op
        return nodo_izq

    # Nivel 2: Operadores Relacionales (Se resuelven ANTES que los lógicos)
    def expresion_relacional(self):
        # Bajamos a las operaciones aritméticas simples (+, -)
        nodo_izq = self.expresion_simple()
        
        # Evaluamos los comparadores tradicionales (<, <=, >, >=, ==, !=)
        while self.token_actual and self.token_actual['valor'] not in ['do', 'then', ';', ')', '('] and (self.token_actual['tipo'] in ['OP_LOG_REL', 'SIMBOLO'] and self.token_actual['valor'] in ['<', '<=', '>', '>=', '==', '!=']):
            nodo_op = NodoAST(f"Op_Relacional: {self.token_actual['valor']}")
            self.avanzar()
            nodo_der = self.expresion_simple()
            if nodo_izq: nodo_op.agregar_hijo(nodo_izq)
            if nodo_der: nodo_op.agregar_hijo(nodo_der)
            nodo_izq = nodo_op
        return nodo_izq

    # Nivel 3: Sumas y Restas
    def expresion_simple(self):
        nodo_izq = self.termino()
        while self.token_actual and self.token_actual['valor'] not in ['do', 'then', ';', ')', '('] and (self.token_actual['tipo'] in ['OP_ARITMETICO', 'SIMBOLO']) and self.token_actual['valor'] in ['+', '-']:
            nodo_op = NodoAST(f"Op_Aritmetico: {self.token_actual['valor']}")
            self.avanzar()
            nodo_der = self.termino()
            if nodo_izq: nodo_op.agregar_hijo(nodo_izq)
            if nodo_der: nodo_op.agregar_hijo(nodo_der)
            nodo_izq = nodo_op
        return nodo_izq

    # Nivel 4: Multiplicaciones y Divisiones
    def termino(self):
        nodo_izq = self.factor()
        while self.token_actual and self.token_actual['valor'] not in ['do', 'then', ';', ')', '('] and (self.token_actual['tipo'] in ['OP_ARITMETICO', 'SIMBOLO']) and self.token_actual['valor'] in ['*', '/', '%']:
            nodo_op = NodoAST(f"Op_Multiplicativo: {self.token_actual['valor']}")
            self.avanzar()
            nodo_der = self.factor()
            if nodo_izq: nodo_op.agregar_hijo(nodo_izq)
            if nodo_der: nodo_op.agregar_hijo(nodo_der)
            nodo_izq = nodo_op
        return nodo_izq

    def factor(self):
        nodo_izq = self.componente()
        while self.token_actual and self.token_actual['valor'] == '^':
            nodo_op = NodoAST("Op_Potencia: ^")
            self.avanzar()
            nodo_der = self.componente()
            if nodo_izq: nodo_op.agregar_hijo(nodo_izq)
            if nodo_der: nodo_op.agregar_hijo(nodo_der)
            nodo_izq = nodo_op
        return nodo_izq

    def componente(self):
        if not self.token_actual: 
            return None
        
        if self.token_actual['valor'] == '(':
            self.consumir("SIMBOLO", "(")
            nodo = self.expresion()
            self.consumir("SIMBOLO", ")")
            return nodo
        elif self.token_actual['tipo'] == 'NUMERO':
            val = self.token_actual['valor']
            self.avanzar()
            return NodoAST(f"Literal: {val}")
        elif self.token_actual['tipo'] == 'IDENTIFICADOR':
            val = self.token_actual['valor']
            self.avanzar()
            return NodoAST(f"Id_Token: {val}")
        elif self.token_actual['valor'] == '!':
            nodo_op = NodoAST("Op_Logico: !")
            self.avanzar()
            nodo_comp = self.componente()
            if nodo_comp: 
                nodo_op.agregar_hijo(nodo_comp)
            return nodo_op
        else:
            return None