import re

class AnalizadorLexico:
    def __init__(self):
        # Definición de patrones según los requerimientos del PDF [cite: 97-105]
        self.specs = [
            ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),          # Color 3 [cite: 98]
            ('COMENTARIO_SIMPLE', r'//.*'),                   # Color 3 [cite: 98]
            ('NUMERO_REAL',      r'\d+\.\d+'),                # Color 1 [cite: 97]
            ('NUMERO_ENTERO',    r'\d+'),                     # Color 1 [cite: 97]
            ('RESERVADA',        r'\b(if|else|end|do|while|switch|case|int|float|main|cin|cout)\b'), # Color 4 [cite: 99]
            ('IDENTIFICADOR',    r'[a-zA-Z][a-zA-Z0-9]*'),    # Color 2 [cite: 98]
            ('OP_ARITMETICO',    r'\+\+|--|\+|-|\*|/|%|\^'),   # Color 5 [cite: 100]
            ('OP_LOG_REL',       r'<=|>=|!=|==|&&|\|\||<|>|!|and|or|not'), # Color 6 [cite: 101, 102]
            ('ASIGNACION',       r'='),                       # [cite: 105]
            ('SIMBOLO',          r'\(|\)|\{|\}|,|;|"|\''),   # [cite: 104]
            ('ESPACIO',          r'[ \t]+'),                  # Ignorar
            ('NUEVA_LINEA',      r'\n'),                      # Control de línea
            ('ERROR',            r'.'),                       # Carácter inválido [cite: 109]
        ]
        self.regex = '|'.join(f'(?P<{name}>{pat})' for name, pat in self.specs)

    def analizar(self, codigo_fuente):
        lista_tokens = []
        lista_errores = []
        linea_actual = 1
        inicio_linea = 0

        for mo in re.finditer(self.regex, codigo_fuente):
            tipo = mo.lastgroup
            valor = mo.group()
            columna = mo.start() - inicio_linea + 1

            if tipo == 'NUEVA_LINEA':
                linea_actual += 1
                inicio_linea = mo.end()
                continue
            elif tipo == 'ESPACIO':
                continue
            
            # Manejo de Errores Léxicos [cite: 109]
            if tipo == 'ERROR':
                error_msg = f"Error: Carácter '{valor}' no reconocido en Fila {linea_actual}, Col {columna}"
                lista_errores.append({'linea': linea_actual, 'col': columna, 'msg': error_msg})
            else:
                lista_tokens.append({
                    'tipo': tipo,
                    'valor': valor,
                    'linea': linea_actual,
                    'col': columna
                })
        
        return lista_tokens, lista_errores

# Ejemplo de ejecución
scanner = AnalizadorLexico()
codigo = "int x = 10; // Ejemplo \n float y = 20.5; $ @ "
tokens, errores = scanner.analizar(codigo)

print("--- TOKENS ENCONTRADOS ---")
for t in tokens: print(t)

print("\n--- ERRORES LÉXICOS ---")
for e in errores: print(e)