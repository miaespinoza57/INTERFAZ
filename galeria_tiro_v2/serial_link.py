"""Enlace con el microcontrolador: parseo del protocolo, lectura serie y simulador.

EnlaceSerie y SimuladorMicro ofrecen la misma interfaz (leer, actualizar, cerrar,
conectado), así que el resto del programa no distingue cuál de los dos está usando.
"""

import queue
import threading
from collections import deque
from typing import NamedTuple

import config

MAX_LINEA = 128    # Una línea más larga que esto es basura: se descarta
MAX_DIGITOS = 10


class Mensaje(NamedTuple):
    tipo: str
    valores: tuple


TOP_CANTIDAD = 10

# Cantidad de campos numéricos que lleva cada mensaje
_CAMPOS = {"READY": 0, "ASK": 0, "START": 1, "T": 1, "HIT": 2, "UP": 1, "END": 4, "REC": 1,
           "TOP": TOP_CANTIDAD}
# NOM,<3 caracteres>,... (diez) lleva las iniciales del top 10: son texto, no números


def _entero(texto):
    """Convierte a entero sin signo; devuelve None si no es un número limpio."""
    if texto.isascii() and texto.isdigit() and len(texto) <= MAX_DIGITOS:
        return int(texto)
    return None


def _rangos_validos(tipo, valores):
    if tipo == "HIT" or tipo == "UP":
        return 1 <= valores[0] <= 3
    if tipo == "END":
        return valores[2] in (0, 1) and valores[3] <= 3
    return True


def _nombre_valido(nombre):
    return len(nombre) == 3 and nombre.isascii() and all(ch.isalnum() or ch == "-" for ch in nombre)


def parsear_linea(linea):
    """Devuelve un Mensaje, o None si la línea está mal formada o es desconocida."""
    partes = linea.strip().split(",")
    tipo = partes[0]
    if tipo == "NOM":
        nombres = tuple(partes[1:])
        if len(nombres) == TOP_CANTIDAD and all(_nombre_valido(n) for n in nombres):
            return Mensaje(tipo, nombres)
        return None
    if tipo not in _CAMPOS or len(partes) - 1 != _CAMPOS[tipo]:
        return None
    valores = tuple(_entero(p) for p in partes[1:])
    if None in valores or not _rangos_validos(tipo, valores):
        return None
    return Mensaje(tipo, valores)


class EnlaceSerie:
    """Lee el puerto en un hilo aparte para que la animación nunca se congele."""

    def __init__(self, puerto, baudios):
        self.puerto = puerto
        self.baudios = baudios
        self.conectado = False
        self._puerto = None
        self._cola = queue.Queue()
        self._parar = threading.Event()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def _bucle(self):
        import serial  # Aquí para que --sim funcione aunque no esté pyserial

        while not self._parar.is_set():
            try:
                with serial.Serial(self.puerto, self.baudios, timeout=0.1) as puerto:
                    self._puerto = puerto
                    self.conectado = True
                    self._leer_hasta_desconexion(puerto)
            except (serial.SerialException, OSError):
                pass  # Puerto ausente o desconectado: se reintenta abajo
            self._puerto = None
            self.conectado = False
            self._parar.wait(config.RECONEXION_SEG)

    def _leer_hasta_desconexion(self, puerto):
        # Se arma la línea a mano: readline() con timeout puede devolver medio mensaje
        pendiente = bytearray()
        while not self._parar.is_set():
            pendiente += puerto.read(puerto.in_waiting or 1)
            while b"\n" in pendiente:
                crudo, _, resto = pendiente.partition(b"\n")
                pendiente = bytearray(resto)
                mensaje = parsear_linea(crudo.decode("ascii", errors="replace"))
                if mensaje:
                    self._cola.put(mensaje)
            if len(pendiente) > MAX_LINEA:
                pendiente.clear()

    def leer(self):
        """Devuelve los mensajes recibidos desde la última llamada, sin bloquear."""
        mensajes = []
        while True:
            try:
                mensajes.append(self._cola.get_nowait())
            except queue.Empty:
                return mensajes

    def actualizar(self, dt):
        pass

    def tecla(self, caracter):
        pass

    def enviar(self, texto):
        """Manda una orden al micro (por ejemplo "N,ABC\\n"). Si no hay conexión, se pierde."""
        puerto = self._puerto
        if puerto is None:
            return
        try:
            puerto.write(texto.encode("ascii", errors="ignore"))
        except (OSError, ValueError):
            pass  # El hilo lector detecta la desconexión y reconecta

    def cerrar(self):
        self._parar.set()
        self._hilo.join(timeout=1.0)


class SimuladorMicro:
    """Hace el papel del ATmega328P: genera las mismas líneas de texto del protocolo.

    Las líneas pasan por parsear_linea, igual que las del puerto real.
    Teclas: S = botón INICIAR (pide las 3 letras), Tab = botón REINICIAR.
    """

    conectado = True

    def __init__(self):
        self._lineas = deque()
        puntajes = sorted(config.SIM_TOP_INICIAL, reverse=True)[:TOP_CANTIDAD]
        nombres = list(config.SIM_NOMBRES_INICIAL)
        self._top = [(p, nombres[i] if i < len(nombres) else "---") for i, p in enumerate(puntajes)]
        self._top += [(0, "---")] * (TOP_CANTIDAD - len(self._top))   # (puntaje, iniciales)
        self._record = self._top[0][0]
        self._jugador = "SIM"
        self._pidiendo = False
        self._puntaje = 0
        self._restante = 0
        self._jugando = False
        self._acumulado = 0.0
        self._premio_prueba = 0
        self._por_levantar = {}   # diana -> segundos que faltan para subir
        self._avisar_listo()

    def _enviar(self, linea):
        self._lineas.append(linea + "\n")

    def _enviar_top(self):
        self._enviar("TOP," + ",".join(str(p) for p, _ in self._top))
        self._enviar("NOM," + ",".join(n for _, n in self._top))

    def _avisar_listo(self):
        self._enviar("READY")
        self._enviar(f"REC,{self._record}")
        self._enviar_top()

    def _terminar(self, puntaje, nuevo, premio):
        self._jugando = False
        self._por_levantar.clear()
        if puntaje > 0 and puntaje > self._top[-1][0]:    # Entra al top 10; los empates quedan debajo
            posicion = sum(1 for p, _ in self._top if p >= puntaje)
            self._top.insert(posicion, (puntaje, self._jugador))
            del self._top[TOP_CANTIDAD:]
        self._record = self._top[0][0]
        self._enviar(f"END,{puntaje},{self._record},{int(nuevo)},{premio}")
        self._enviar_top()

    def _premio_por_puntaje(self):
        if self._puntaje >= 100:
            return 2
        return 1 if self._puntaje >= 50 else 0

    def tecla(self, caracter):
        """S = iniciar, Tab = reiniciar, 1/2/3 = impacto, E = fin de prueba, R = fin con récord."""
        if caracter == "\t":
            self._reiniciar()
            return
        caracter = caracter.upper()
        if caracter == "S":
            self._pedir_letras()
        elif caracter in ("1", "2", "3"):
            self._impacto(int(caracter))
        elif caracter == "E":
            # Cada E entrega un nivel distinto para poder ver los tres
            premio = self._premio_prueba
            self._premio_prueba = (premio + 1) % 3
            self._terminar(self._puntaje or 40, False, premio)
        elif caracter == "R":
            self._terminar(max(self._puntaje, self._record) + 10, True, 3)

    def enviar(self, texto):
        """Recibe las órdenes de la interfaz, igual que el micro por el puerto serie."""
        texto = texto.strip()
        if texto == "R":
            self._reiniciar()
        elif texto.startswith("N,") and len(texto) == 5 and self._pidiendo:
            self._jugador = texto[2:].upper()
            self._pidiendo = False
            self._iniciar()

    def _pedir_letras(self):
        if not self._jugando:
            self._pidiendo = True
            self._enviar("ASK")

    def _reiniciar(self):
        self._jugando = False
        self._pidiendo = False
        self._puntaje = 0
        self._por_levantar.clear()
        self._avisar_listo()

    def _iniciar(self):
        self._puntaje = 0
        self._restante = config.SIM_TIEMPO_PARTIDA
        self._acumulado = 0.0
        self._jugando = True
        self._por_levantar.clear()
        self._enviar(f"START,{self._restante}")

    def _impacto(self, diana):
        # El micro ignora disparos fuera de partida o a una diana ya derribada
        if self._jugando and diana not in self._por_levantar:
            self._puntaje += config.SIM_PUNTOS_ACIERTO
            self._por_levantar[diana] = config.SIM_SEG_PARA_LEVANTAR
            self._enviar(f"HIT,{diana},{self._puntaje}")

    def actualizar(self, dt):
        if not self._jugando:
            return
        for diana in list(self._por_levantar):
            self._por_levantar[diana] -= dt
            if self._por_levantar[diana] <= 0:
                del self._por_levantar[diana]
                self._enviar(f"UP,{diana}")
        self._acumulado += dt
        while self._acumulado >= 1.0 and self._jugando:
            self._acumulado -= 1.0
            self._restante -= 1
            self._enviar(f"T,{self._restante}")
            if self._restante <= 0:
                nuevo = self._puntaje > self._record
                self._terminar(self._puntaje, nuevo, 3 if nuevo else self._premio_por_puntaje())

    def leer(self):
        mensajes = [parsear_linea(linea) for linea in self._lineas]
        self._lineas.clear()
        return [m for m in mensajes if m]

    def cerrar(self):
        pass