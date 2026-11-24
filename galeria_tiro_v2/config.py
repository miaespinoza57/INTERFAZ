"""Configuración general de la interfaz de la galería de tiro."""

# --- Modo de arranque -------------------------------------------------------
# True: sin argumentos arranca en simulación (no hace falta el Arduino).
# Cuando el hardware esté listo, cámbialo a False o ejecuta con --serial.
MODO_SIMULACION = False

# --- Puerto serie -----------------------------------------------------------
PUERTO = "COM5"          # En Linux suele ser /dev/ttyACM0 o /dev/ttyUSB0
BAUDIOS = 9600
RECONEXION_SEG = 2.0     # Espera entre intentos de reconexión

# --- Ventana ----------------------------------------------------------------
ANCHO = 1280
ALTO = 720
FPS = 60
TITULO = "Galería de Tiro Láser"
# True en computadoras lentas: el feriante se redibuja a la mitad de cuadros y se
# quita la capa de iluminación. Con F3 se ven los FPS para decidir.
MODO_RAPIDO = False

# --- Tiempos de la interfaz (segundos) --------------------------------------
RESULTADOS_SEG = 12.0        # Duración de la pantalla de resultados
RESULTADOS_RECORD_SEG = 15.0  # Igual, pero con nuevo récord
ESPERA_FRASE_SEG = (7.0, 10.0)   # Cada cuánto habla en la pantalla de espera
BURLA_FRASE_SEG = (5.0, 8.0)     # Cada cuánto se burla si no aciertas
PRESION_FRASE_SEG = 4.0          # Cada cuánto presiona en los últimos segundos
ULTIMOS_SEGUNDOS = 10            # A partir de aquí mete presión
PAUSA_ENTRE_ACIERTOS = 2.0       # Evita pisar la frase de acierto anterior
LETRAS_POR_SEG = 38              # Velocidad de la máquina de escribir

# --- Texto flotante al acertar ----------------------------------------------
TEXTO_IMPACTO = "+10"

# --- Simulador (solo modo --sim; imita lo que hará el micro) ----------------
SIM_TIEMPO_PARTIDA = 60
SIM_PUNTOS_ACIERTO = 10
SIM_TOP_INICIAL = (120, 100, 90, 80, 70, 60, 50, 40, 30, 20)   # El primero es el récord
SIM_NOMBRES_INICIAL = ("MIA", "ANA", "LUZ", "BTO", "RAY", "SOL", "TON", "KIK", "PAZ", "LEO")
SIM_SEG_PARA_LEVANTAR = 3.0

# --- Paleta de la feria -----------------------------------------------------
TINTA = (28, 18, 20)
ROJO = (214, 40, 40)
ROJO_OSCURO = (140, 22, 30)
CREMA = (252, 240, 214)
MOSTAZA = (246, 186, 48)
ORO = (255, 208, 64)
NARANJA = (240, 120, 40)
AZUL = (40, 110, 190)
VERDE = (60, 170, 90)
MADERA = (176, 112, 60)
MADERA_CLARA = (214, 150, 86)
MADERA_OSCURA = (112, 66, 36)