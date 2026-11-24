"""Datos en pantalla: letrero, dianas, efectos de impacto, globo, resultados y confeti."""

import math
import random

import pygame

import config as c
from dibujo import (Resorte, acercar, aclarar, brillo, degradado, destello, estrella, fuente,
                    limitar, oscurecer, poligono, rebote_salida, rect_redondo, suave, suavizar,
                    texto_borde)
from scene import DIANAS_X, Foquitos, MOSTRADOR_Y

K = 2
LETRERO = pygame.Rect(350, 8, 580, 92)
TABLERO = pygame.Rect(748, 138, 226, 394)    # Mejores puntajes, a la derecha del estante
CAMPOS = (("TIEMPO", 447), ("PUNTAJE", 640), ("RÉCORD", 833))
INDICADOR_Y = MOSTRADOR_Y + 36
PAPEL = (255, 252, 240)


class GloboDialogo:
    """Globo de cómic con efecto de máquina de escribir."""

    ANCHO_TEXTO = 340
    DERECHA = 1010
    DERECHA_TABLERO = TABLERO.left - 26    # Con el tablero a la vista, el globo se corre a la izquierda
    ABAJO = 258
    PERMANENCIA = 3.5    # Segundos que queda visible al terminar de escribir
    MARGEN = 16

    def __init__(self):
        self.tipo = fuente(23)
        self.lineas = []
        self.total = 0
        self.letras = 0.0
        self.espera = 0.0
        self.visible = False
        self._t = 0.0
        self._escala = Resorte(0.0, 260.0, 17.0)    # Aparece con un rebote
        self._fondo = None
        self._cache = (-1, None)
        self._tam = (0, 0)
        self.junto_al_tablero = False
        self._der = float(self.DERECHA)

    @property
    def _marco(self):
        ancho, alto = self._tam
        return pygame.Rect(round(self._der) - ancho, self.ABAJO - alto, ancho, alto)

    def _objetivo_der(self):
        return self.DERECHA_TABLERO if self.junto_al_tablero else self.DERECHA

    @property
    def escribiendo(self):
        return self.visible and self.letras < self.total

    @property
    def letra_actual(self):
        """Letra que se acaba de escribir; el feriante la usa para mover la boca."""
        if not self.escribiendo:
            return ""
        texto = "".join(self.lineas)
        return texto[min(int(self.letras), len(texto) - 1)]

    def mostrar(self, texto, permanencia=None):
        self.lineas = self._partir(texto)
        self.total = sum(len(linea) for linea in self.lineas)
        self.letras = 0.0
        self.espera = self.PERMANENCIA if permanencia is None else permanencia
        self.visible = True
        self._escala.x, self._escala.v = 0.5, 0.0
        ancho = max(self.tipo.size(linea)[0] for linea in self.lineas) + 44
        alto = self.tipo.get_linesize() * len(self.lineas) + 30
        self._tam = (ancho, alto)
        self._der = float(self._objetivo_der())
        self._fondo = self._crear_fondo(ancho, alto)
        self._cache = (-1, None)

    def ocultar(self):
        self.visible = False

    def _partir(self, texto):
        lineas, actual = [], ""
        for palabra in texto.split():
            prueba = f"{actual} {palabra}".strip()
            if self.tipo.size(prueba)[0] <= self.ANCHO_TEXTO:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
        return lineas

    def _crear_fondo(self, ancho, alto):
        m = self.MARGEN
        capa = pygame.Surface(((ancho + m * 2) * K, (alto + m * 2) * K), pygame.SRCALPHA)
        sombra = pygame.Surface(capa.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (20, 0, 30, 90), ((m + 5) * K, (m + 7) * K, ancho * K, alto * K), border_radius=20 * K)
        capa.blit(sombra, (0, 0))
        rect_redondo(capa, PAPEL, (m * K, m * K, ancho * K, alto * K), 20 * K, 4 * K)
        pygame.draw.rect(capa, (255, 255, 255), ((m + 8) * K, (m + 5) * K, (ancho - 16) * K, 6 * K), border_radius=3 * K)
        return suavizar(capa, K)

    def actualizar(self, dt):
        if not self.visible:
            return
        self._t += dt
        self._der = acercar(self._der, self._objetivo_der(), 9.0, dt)
        self._escala.actualizar(1.0, dt)
        if self.escribiendo:
            self.letras = min(self.total, self.letras + c.LETRAS_POR_SEG * dt)
        else:
            self.espera -= dt
            if self.espera <= 0:
                self.visible = False

    def _imagen(self):
        escritas = int(self.letras)
        if self._cache[0] != escritas:
            imagen = self._fondo.copy()
            restantes = escritas
            y = self.MARGEN + 15
            for linea in self.lineas:
                parte = linea[:max(0, restantes)]
                restantes -= len(linea)
                if parte:
                    imagen.blit(self.tipo.render(parte, True, c.TINTA), (self.MARGEN + 22, y))
                y += self.tipo.get_linesize()
            self._cache = (escritas, imagen)
        return self._cache[1]

    def dibujar(self, s, punta):
        if not self.visible:
            return
        if self.junto_al_tablero:
            punta = (min(punta[0], TABLERO.left - 6), punta[1])    # La cola no pasa sobre el tablero
        marco = self._marco.move(0, round(math.sin(self._t * 2.2) * 2.5))    # Flota un poco
        imagen = self._imagen()
        escala = self._escala.x
        asentado = abs(escala - 1) < 0.01
        if not asentado:
            imagen = pygame.transform.smoothscale(
                imagen, (max(2, int(imagen.get_width() * escala)), max(2, int(imagen.get_height() * escala))))
        # Cola curva hacia la boca
        base = marco.right - 62
        cola = [(base - 24, marco.bottom - 3), (base + 20, marco.bottom - 3),
                (base + 26 + (punta[0] - base) * 0.5, marco.bottom + (punta[1] - marco.bottom) * 0.45), punta,
                (base - 4 + (punta[0] - base) * 0.4, marco.bottom + (punta[1] - marco.bottom) * 0.62)]
        poligono(s, PAPEL, cola, 4)
        s.blit(imagen, imagen.get_rect(center=marco.center))
        # Tapa la unión para que la cola y el globo se vean como una sola pieza
        if asentado:
            pygame.draw.polygon(s, PAPEL, [(base - 21, marco.bottom - 4), (base + 17, marco.bottom - 4),
                                           (base + 15, marco.bottom + 4), (base - 16, marco.bottom + 4)])


class Rodante:
    """Número cuyas cifras ruedan como en un marcador mecánico."""

    DURACION = 0.3

    def __init__(self, tipo):
        self.tipo = tipo
        self.actual = "0"
        self.previo = "0"
        self.t = 1.0

    def fijar(self, valor, animar=True):
        texto = str(valor)
        if texto != self.actual:
            self.previo, self.actual = self.actual, texto
            self.t = 0.0 if animar else 1.0

    def actualizar(self, dt):
        self.t = min(1.0, self.t + dt / self.DURACION)

    def dibujar(self, s, centro, color):
        celda = self.tipo.size("0")[0] + 5
        alto = self.tipo.get_linesize()
        n = len(self.actual)
        x0 = centro[0] - n * celda / 2
        previo = self.previo.rjust(n)[-n:]
        avance = suave(self.t)
        recorte = s.get_clip()
        s.set_clip(pygame.Rect(x0 - 6, centro[1] - alto / 2 + 3, n * celda + 12, alto - 6))
        for i, cifra in enumerate(self.actual):
            x = x0 + celda * (i + 0.5)
            if self.t < 1.0 and previo[i] != cifra:
                if previo[i] != " ":
                    vieja = texto_borde(self.tipo, previo[i], color)
                    s.blit(vieja, vieja.get_rect(center=(x, centro[1] - avance * alto)))
                y = centro[1] + (1 - avance) * alto
            else:
                y = centro[1]
            imagen = texto_borde(self.tipo, cifra, color)
            s.blit(imagen, imagen.get_rect(center=(x, y)))
        s.set_clip(recorte)


class TextoFlotante:
    """El "+10" que brinca sobre el indicador de la diana y sube desvaneciéndose."""

    VIDA = 1.2

    def __init__(self, x, y, texto):
        self.x = x
        self.y = y
        self.t = 0.0
        self.imagen = texto_borde(fuente(58, True), texto, c.ORO, grosor=3).copy()
        self._giro = random.uniform(-9, 9)

    @property
    def vivo(self):
        return self.t < self.VIDA

    def actualizar(self, dt):
        self.t += dt
        self.y -= (150 * math.exp(-self.t * 3.5) + 30) * dt

    def dibujar(self, s):
        escala = 0.3 + 0.7 * rebote_salida(self.t / 0.2)
        imagen = pygame.transform.rotozoom(self.imagen, self._giro * (1 - limitar(self.t * 2)), escala)
        imagen.set_alpha(int(255 * limitar((self.VIDA - self.t) * 2.5)))
        s.blit(imagen, imagen.get_rect(center=(self.x, self.y)))


class Destello:
    """Estrella de impacto de cómic que gira y crece."""

    VIDA = 0.34

    def __init__(self, centro, imagen):
        self.centro = centro
        self.imagen = imagen
        self.t = 0.0
        self._giro = random.uniform(0, 36)

    @property
    def vivo(self):
        return self.t < self.VIDA

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, s):
        avance = self.t / self.VIDA
        imagen = pygame.transform.rotozoom(self.imagen, self._giro + avance * 30, 0.45 + avance * 0.85)
        imagen.set_alpha(int(255 * (1 - avance ** 2)))
        s.blit(imagen, imagen.get_rect(center=self.centro))


class Confeti:
    COLORES = [c.ROJO, c.MOSTAZA, c.AZUL, c.VERDE, (240, 110, 210), (255, 255, 255)]

    def __init__(self):
        self.piezas = []
        self.tiempo = 0.0   # Segundos que falta seguir soltando confeti

    def lanzar(self, segundos):
        self.tiempo = segundos
        self.canonazo()

    def canonazo(self):
        """Dos cañones de confeti disparan desde las esquinas de abajo."""
        for x, direccion in ((40, 1), (c.ANCHO - 40, -1)):
            for _ in range(70):
                angulo = random.uniform(0.9, 1.45)
                fuerza = random.uniform(500, 1150)
                self._crear(x, c.ALTO - 20, direccion * math.cos(angulo) * fuerza, -math.sin(angulo) * fuerza)

    def _crear(self, x, y, vx, vy):
        self.piezas.append({
            "x": x, "y": y, "vx": vx, "vy": vy, "caida": random.uniform(130, 260),
            "giro": random.uniform(0, 6.28), "vel_giro": random.uniform(-8, 8),
            "lado": random.uniform(7, 13), "color": random.choice(self.COLORES),
            "cinta": random.random() < 0.3,
        })

    def detener(self):
        self.tiempo = 0.0
        self.piezas.clear()

    def actualizar(self, dt):
        self.tiempo = max(0.0, self.tiempo - dt)
        if self.tiempo > 0:
            for _ in range(random.randint(1, 3)):
                self._crear(random.uniform(0, c.ANCHO), random.uniform(-40, -8), random.uniform(-40, 40), 200)
        for p in self.piezas:
            # El aire frena el disparo hasta dejarlo caer planeando
            p["vx"] = acercar(p["vx"], 0.0, 1.6, dt)
            p["vy"] = acercar(p["vy"], p["caida"], 2.2, dt)
            p["x"] += (p["vx"] + math.sin(p["giro"]) * 50) * dt
            p["y"] += p["vy"] * dt
            p["giro"] += p["vel_giro"] * dt
        self.piezas = [p for p in self.piezas if p["y"] < c.ALTO + 20]

    def dibujar(self, s):
        for p in self.piezas:
            # El ancho varía con el giro: parece un papel que da vueltas y enseña su reverso
            vuelta = math.cos(p["giro"])
            color = p["color"] if vuelta > 0 else oscurecer(p["color"], 0.7)
            ancho = max(1.5, abs(vuelta) * p["lado"])
            alto = p["lado"] * (1.9 if p["cinta"] else 0.7)
            inclina = math.sin(p["giro"] * 0.7) * alto * 0.4
            x, y = p["x"], p["y"]
            pygame.draw.polygon(s, color, [(x - ancho / 2 + inclina, y - alto / 2), (x + ancho / 2 + inclina, y - alto / 2),
                                           (x + ancho / 2 - inclina, y + alto / 2), (x - ancho / 2 - inclina, y + alto / 2)])


class Tablero:
    """Letrero con los mejores puntajes (los manda el micro en la línea TOP).

    Cada entrada es (puntaje, nombre). Por ahora el nombre va vacío y solo se muestra el
    puntaje; para mostrar nombres basta pasar la lista a fijar(puntajes, nombres).
    """

    FILAS = 10
    MARGEN = 10             # Margen de la capa de sombra (igual que el letrero)
    PRIMERA_FILA = 70       # Centro vertical de la fila 1, dentro del letrero
    ALTO_FILA = 32
    COLORES = ((255, 208, 64), (222, 228, 238), (232, 150, 92))    # Oro, plata y bronce
    APAGADO = (150, 112, 100)

    def __init__(self):
        self.entradas = [(0, "")] * self.FILAS
        self._tipo = fuente(27, True)
        self._tipo_nombre = fuente(21, True)
        self._base = self._crear_base()
        self._imagen = None         # Letrero con sus filas; se rehace solo si cambian los datos
        self._presencia = 0.0

    def fijar(self, puntajes=None, nombres=None):
        """Actualiza puntajes y/o iniciales; lo que se pasa como None se queda como estaba."""
        if puntajes is None:
            puntajes = [e[0] for e in self.entradas]
        if nombres is None:
            nombres = [e[1] for e in self.entradas]
        entradas = [(puntajes[i] if i < len(puntajes) else 0, nombres[i] if i < len(nombres) else "")
                    for i in range(self.FILAS)]
        if entradas != self.entradas:
            self.entradas = entradas
            self._imagen = None

    @classmethod
    def _crear_base(cls):
        m = cls.MARGEN
        w, h = TABLERO.size
        s = pygame.Surface(((w + m * 2) * K, (h + m * 2) * K), pygame.SRCALPHA)
        cuerpo = pygame.Rect(m * K, m * K, w * K, h * K)
        sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 110), cuerpo.move(4 * K, 6 * K), border_radius=16 * K)
        s.blit(sombra, (0, 0))
        rect_redondo(s, c.ROJO_OSCURO, cuerpo, 14 * K, 4 * K)
        pygame.draw.rect(s, c.ROJO, (cuerpo.x, cuerpo.y, cuerpo.w, 14 * K), border_top_left_radius=14 * K,
                         border_top_right_radius=14 * K)
        panel = cuerpo.inflate(-20 * K, -20 * K)
        pygame.draw.rect(s, (48, 24, 22), panel, border_radius=9 * K)
        pygame.draw.rect(s, c.ORO, cuerpo.inflate(-12 * K, -12 * K), 2 * K, border_radius=11 * K)
        linea = (m + 52) * K
        pygame.draw.line(s, c.ORO, (panel.x + 12 * K, linea), (panel.right - 12 * K, linea), 2 * K)
        s = suavizar(s, K)
        titulo = texto_borde(fuente(20, True), "MEJORES TIRADORES", c.MOSTAZA)
        maximo = w - 40
        if titulo.get_width() > maximo:
            titulo = pygame.transform.smoothscale(
                titulo, (maximo, round(titulo.get_height() * maximo / titulo.get_width())))
        s.blit(titulo, titulo.get_rect(center=(m + w // 2, m + 31)))
        return s

    def _componer(self):
        s = self._base.copy()
        m, w = self.MARGEN, TABLERO.w
        derecha = m + w - 24
        for i, (puntaje, nombre) in enumerate(self.entradas):
            y = m + self.PRIMERA_FILA + i * self.ALTO_FILA
            color = self.APAGADO if puntaje <= 0 else self.COLORES[i] if i < 3 else c.CREMA
            rango = texto_borde(self._tipo, f"{i + 1}.", color)
            s.blit(rango, rango.get_rect(midright=(m + 56, y)))
            valor = texto_borde(self._tipo, str(puntaje) if puntaje > 0 else "---", color)
            s.blit(valor, valor.get_rect(midright=(derecha, y)))
            if nombre and puntaje > 0:
                imagen = texto_borde(self._tipo_nombre, nombre.upper(), color)
                libre = derecha - valor.get_width() - 8 - (m + 64)
                if imagen.get_width() > libre:
                    imagen = pygame.transform.smoothscale(
                        imagen, (libre, round(imagen.get_height() * libre / imagen.get_width())))
                s.blit(imagen, imagen.get_rect(midleft=(m + 64, y)))
        return s

    def actualizar(self, dt, visible):
        self._presencia = acercar(self._presencia, 1.0 if visible else 0.0, 7.0, dt)

    def dibujar(self, s):
        if self._presencia < 0.02:
            return
        if self._imagen is None:
            self._imagen = self._componer()
        avance = 1.0 if self._presencia > 0.99 else self._presencia
        self._imagen.set_alpha(int(255 * avance))
        # Al aparecer baja un poco mientras se hace visible
        s.blit(self._imagen, (TABLERO.x - self.MARGEN, TABLERO.y - self.MARGEN - (1 - avance) * 36))


class Cartel:
    """Cartel de resultados: cae colgado de dos cuerdas y se queda meciéndose."""

    ANCHO, ALTO = 400, 372
    CENTRO_X = 290
    ARRIBA = 112
    ASENTADO = 4.5       # Después de esto ya no cambia y se reutiliza la imagen

    def __init__(self, puntaje, record, nuevo, premio):
        self.puntaje = puntaje
        self.record = record
        self.nuevo = nuevo
        self.premio = premio
        self.t = 0.0
        self._giro = Resorte(7.0, 34.0, 5.0)
        self._base = self._crear_base()
        self._estrellas = [self._crear_estrella(c.ORO), self._crear_estrella((200, 186, 160))]
        self._final = None

    def _crear_base(self):
        s = pygame.Surface((self.ANCHO * K, self.ALTO * K), pygame.SRCALPHA)
        marco = pygame.Rect(6 * K, 6 * K, (self.ANCHO - 12) * K, (self.ALTO - 12) * K)
        rect_redondo(s, oscurecer(c.CREMA, 0.86), marco, 16 * K, 5 * K)
        pygame.draw.rect(s, c.CREMA, marco.inflate(-6 * K, -6 * K).move(-K, -K), border_radius=14 * K)
        pygame.draw.rect(s, c.ROJO, marco.inflate(-22 * K, -22 * K), 5 * K, border_radius=9 * K)
        pygame.draw.rect(s, c.MOSTAZA, marco.inflate(-36 * K, -36 * K), 2 * K, border_radius=6 * K)
        for x in (60, self.ANCHO - 60):     # Ojales de las cuerdas
            pygame.draw.circle(s, c.TINTA, (x * K, 20 * K), 8 * K)
            pygame.draw.circle(s, (150, 150, 160), (x * K, 20 * K), 5 * K)
        s = suavizar(s, K)
        titulo = "¡CAMPEÓN!" if self.nuevo else "FIN DEL JUEGO"
        imagen = texto_borde(fuente(44, True), titulo, c.ORO if self.nuevo else c.ROJO, grosor=3)
        s.blit(imagen, imagen.get_rect(center=(self.ANCHO // 2, 66)))
        for etiqueta, y in (("PUNTAJE", 116), ("RÉCORD", 200), ("PREMIO", 284)):
            texto = fuente(21, True).render(etiqueta, True, c.ROJO_OSCURO)
            s.blit(texto, texto.get_rect(center=(self.ANCHO // 2, y)))
        return s

    @staticmethod
    def _crear_estrella(color):
        s = pygame.Surface((56 * K, 56 * K), pygame.SRCALPHA)
        poligono(s, oscurecer(color, 0.82), estrella(28 * K, 28 * K, 24 * K, 10.5 * K), 3 * K)
        pygame.draw.polygon(s, color, estrella(27 * K, 27 * K, 19 * K, 8.5 * K))
        return suavizar(s, K)

    def actualizar(self, dt):
        self.t += dt
        self._giro.actualizar(0.0, dt)

    def _componer(self):
        if self._final:
            return self._final
        s = self._base.copy()
        # Los números suben contando (solo es animación: el valor lo mandó el micro)
        for valor, y, retraso in ((self.puntaje, 156, 0.5), (self.record, 240, 0.9)):
            visible = round(valor * suave((self.t - retraso) / 0.8))
            numero = texto_borde(fuente(52, True), str(visible), c.MOSTAZA)
            s.blit(numero, numero.get_rect(center=(self.ANCHO // 2, y)))
        # Estrellas del premio: aparecen una por una
        for i in range(4):
            x = self.ANCHO // 2 + (i - 1.5) * 58
            s.blit(self._estrellas[1], self._estrellas[1].get_rect(center=(x, 326)))
            aparece = (self.t - 1.7 - i * 0.28) / 0.25
            if i <= self.premio and aparece > 0:
                escala = rebote_salida(aparece) * (1 + 0.5 * (1 - limitar(aparece)))
                imagen = pygame.transform.rotozoom(self._estrellas[0], (1 - limitar(aparece)) * 40, escala)
                s.blit(imagen, imagen.get_rect(center=(x, 326)))
        if self.t > self.ASENTADO:
            self._final = s
        return s

    def dibujar(self, s):
        caida = rebote_salida(self.t * 1.8)
        arriba = -self.ALTO - 30 + (self.ARRIBA + self.ALTO + 30) * caida
        angulo = self._giro.x
        rad = math.radians(angulo)
        imagen = self._componer()
        if abs(angulo) > 0.2:
            imagen = pygame.transform.rotozoom(imagen, angulo, 1.0)
        centro = (self.CENTRO_X + math.sin(rad) * self.ALTO / 2, arriba + math.cos(rad) * self.ALTO / 2)
        for lado in (-1, 1):
            x = self.CENTRO_X + lado * 140
            ojal = (x * 1.0 + math.sin(rad) * 20, arriba + 20 - lado * math.sin(rad) * 140)
            pygame.draw.line(s, c.TINTA, (x, 96), ojal, 7)
            pygame.draw.line(s, (214, 180, 120), (x, 96), ojal, 3)
        s.blit(imagen, imagen.get_rect(center=centro))


class Hud:
    def __init__(self):
        self.tiempo = None          # None = no hay partida
        self.tiempo_total = 0
        self.puntaje = 0
        self.record = 0
        self.nuevo_record = False
        self.dianas_arriba = [True, True, True]
        self.globo = GloboDialogo()
        self.confeti = Confeti()
        self.efectos = []
        self.cartel = None          # Cartel de resultados
        self.tablero = Tablero()    # Top 10: solo se ve en la pantalla de espera

        self._pop = 0.0
        self._barra = 1.0
        self._t = 0.0
        self._lampara_flash = [0.0, 0.0, 0.0]
        self._letrero = self._crear_letrero()
        self.foquitos = Foquitos(self._foquitos_letrero(), radio=5)
        self._destello = destello(110)
        self._tipo_valor = fuente(46, True)
        self._marcador = Rodante(self._tipo_valor)
        self._tipo_indicador = fuente(17)
        self._tipo_aviso = fuente(16)
        self._lamparas = {True: self._lampara((80, 230, 110)), False: self._lampara((230, 60, 50))}
        self._halos = {True: brillo(30, (60, 220, 100), 130), False: brillo(30, (255, 60, 40), 150)}
        self._halo_puntaje = brillo(90, (255, 200, 70), 200)
        self._placa = self._crear_placa()
        self._letras = [texto_borde(fuente(36, True), letra, c.ORO, grosor=3) for letra in "¡PASE A JUGAR!"]

    # -- Construcción --
    @staticmethod
    def _crear_letrero():
        margen = 10
        s = pygame.Surface(((LETRERO.w + margen * 2) * K, (LETRERO.h + margen * 2) * K), pygame.SRCALPHA)
        cuerpo = pygame.Rect(margen * K, margen * K, LETRERO.w * K, LETRERO.h * K)
        sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 110), cuerpo.move(4 * K, 6 * K), border_radius=16 * K)
        s.blit(sombra, (0, 0))
        rect_redondo(s, c.ROJO_OSCURO, cuerpo, 14 * K, 4 * K)
        pygame.draw.rect(s, c.ROJO, (cuerpo.x, cuerpo.y, cuerpo.w, 26 * K), border_top_left_radius=14 * K,
                         border_top_right_radius=14 * K)
        pygame.draw.rect(s, c.ORO, cuerpo.inflate(-18 * K, -16 * K), 2 * K, border_radius=9 * K)
        for _, x in CAMPOS:
            # Ventanilla hundida para cada número
            ventana = pygame.Rect((x - LETRERO.x + margen - 82) * K, (margen + 34) * K, 164 * K, 46 * K)
            rect_redondo(s, (48, 24, 22), ventana, 7 * K, 3 * K)
            s.blit(degradado(ventana.w - 8 * K, 12 * K, (0, 0, 0, 130), (0, 0, 0, 0)), (ventana.x + 4 * K, ventana.y))
        s = suavizar(s, K)
        for nombre, x in CAMPOS:
            etiqueta = texto_borde(fuente(16, True), nombre, c.MOSTAZA)
            s.blit(etiqueta, etiqueta.get_rect(center=(x - LETRERO.x + margen, margen + 23)))
        return s

    @staticmethod
    def _foquitos_letrero():
        r = LETRERO.inflate(-4, -4)
        pasos = range(r.left + 14, r.right - 8, 32)
        return [(x, r.top) for x in pasos] + [(x, r.bottom) for x in pasos]

    @staticmethod
    def _lampara(color):
        s = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(s, c.TINTA, (24, 24), 21)
        pygame.draw.circle(s, oscurecer(color, 0.7), (24, 24), 16)
        pygame.draw.circle(s, color, (22, 22), 13)
        pygame.draw.circle(s, aclarar(color, 0.8), (17, 17), 5)
        return suavizar(s, K)

    @staticmethod
    def _crear_placa():
        s = pygame.Surface((164 * K, 44 * K), pygame.SRCALPHA)
        rect_redondo(s, c.MADERA_OSCURA, (5 * K, 5 * K, 154 * K, 34 * K), 9 * K, 3 * K)
        pygame.draw.rect(s, (136, 84, 48), (7 * K, 6 * K, 150 * K, 5 * K), border_radius=4 * K)
        return suavizar(s, K)

    # -- Eventos --
    def reiniciar(self, segundos=None):
        """Limpia la pantalla; sin segundos significa que no hay partida en curso."""
        self.tiempo = segundos
        self.tiempo_total = segundos or 0
        self._barra = 1.0
        self.puntaje = 0
        self._marcador.fijar(0, animar=False)
        self.nuevo_record = False
        self.dianas_arriba = [True, True, True]
        self.cartel = None
        self.confeti.detener()

    def impacto(self, numero, puntaje, centro):
        self.dianas_arriba[numero - 1] = False
        self._lampara_flash[numero - 1] = 1.0
        self.puntaje = puntaje
        self._marcador.fijar(puntaje)
        self._pop = 1.0
        self.efectos.append(Destello(centro, self._destello))
        self.efectos.append(TextoFlotante(centro[0], centro[1] - 40, c.TEXTO_IMPACTO))

    def levantar(self, numero):
        self.dianas_arriba[numero - 1] = True
        self._lampara_flash[numero - 1] = 1.0

    def fijar_top(self, puntajes=None, nombres=None):
        self.tablero.fijar(puntajes, nombres)

    def mostrar_resultado(self, puntaje, record, nuevo, premio):
        self.tiempo = 0
        self.puntaje = puntaje
        self._marcador.fijar(puntaje, animar=False)
        self.record = record
        self.nuevo_record = nuevo
        self.cartel = Cartel(puntaje, record, nuevo, premio)
        self.confeti.detener()
        if nuevo:
            self.confeti.lanzar(c.RESULTADOS_RECORD_SEG - 2)

    # -- Bucle --
    def actualizar(self, dt, en_espera=True):
        self._t += dt
        self.tablero.actualizar(dt, en_espera)
        self.globo.junto_al_tablero = en_espera
        self._pop = max(0.0, self._pop - dt * 2.8)
        if self.tiempo is not None and self.tiempo_total:
            self._barra = acercar(self._barra, limitar(self.tiempo / self.tiempo_total), 6.0, dt)
        for i in range(3):
            self._lampara_flash[i] = max(0.0, self._lampara_flash[i] - dt * 3)
        self._marcador.actualizar(dt)
        self.foquitos.actualizar(dt)
        self.globo.actualizar(dt)
        self.confeti.actualizar(dt)
        if self.cartel:
            self.cartel.actualizar(dt)
        for efecto in self.efectos:
            efecto.actualizar(dt)
        self.efectos = [e for e in self.efectos if e.vivo]

    def dibujar_efectos(self, s):
        """Destellos y "+10": van dentro de la escena, para que tiemblen con ella."""
        for efecto in self.efectos:
            efecto.dibujar(s)

    def dibujar_tablero(self, s):
        """Va dentro de la escena y antes del feriante, para que su brazo quede encima."""
        self.tablero.dibujar(s)

    def dibujar(self, s, en_espera):
        self._dibujar_letrero(s)
        if en_espera:
            self._dibujar_invitacion(s)
        else:
            self._dibujar_indicadores(s)
        if self.cartel:
            self.cartel.dibujar(s)

    def _dibujar_letrero(self, s):
        s.blit(self._letrero, (LETRERO.x - 10, LETRERO.y - 10))
        self.foquitos.dibujar(s)
        if self.nuevo_record:
            pygame.draw.rect(s, (48, 24, 22), LETRERO.inflate(-30, -26), border_radius=8)
            # Cada letra brinca por su cuenta
            x = LETRERO.centerx - 190
            for i, letra in enumerate("¡NUEVO RÉCORD!"):
                imagen = texto_borde(fuente(46, True), letra, c.ORO, grosor=3)
                brinco = abs(math.sin(self._t * 6 - i * 0.45)) * 9
                s.blit(imagen, imagen.get_rect(midbottom=(x + imagen.get_width() / 2, LETRERO.bottom - 12 - brinco)))
                x += imagen.get_width() - 5 if letra != " " else 16
            return

        tiempo = "--" if self.tiempo is None else str(self.tiempo)
        urgente = self.tiempo is not None and 0 < self.tiempo <= c.ULTIMOS_SEGUNDOS
        color = (255, 90, 70) if urgente else c.CREMA
        latido = 1 + 0.16 * abs(math.sin(self._t * math.pi)) if urgente else 1.0
        self._valor(s, tiempo, CAMPOS[0][1], color, latido)
        if self.tiempo is not None and self.tiempo_total:
            # Barra de tiempo: pasa de verde a rojo conforme se acaba
            ancho = int(148 * self._barra)
            tono = (90, 220, 110) if self._barra > 0.5 else (250, 200, 60) if self._barra > 0.2 else (255, 80, 60)
            pygame.draw.rect(s, c.TINTA, (CAMPOS[0][1] - 76, 83, 152, 7), border_radius=3)
            if ancho > 2:
                pygame.draw.rect(s, tono, (CAMPOS[0][1] - 74, 84, ancho, 5), border_radius=2)
        if self._pop > 0:
            self._halo_puntaje.set_alpha(None)
            halo = self._halo_puntaje if self._pop > 0.5 else brillo(90, (255, 200, 70), 100)
            s.blit(halo, halo.get_rect(center=(CAMPOS[1][1], 66)), special_flags=pygame.BLEND_RGB_ADD)
        self._marcador.dibujar(s, (CAMPOS[1][1], 66), c.ORO if self._pop > 0 else c.CREMA)
        self._valor(s, str(self.record), CAMPOS[2][1], c.CREMA, 1.0)

    def _valor(self, s, texto, x, color, escala):
        imagen = texto_borde(self._tipo_valor, texto, color)
        if escala != 1.0:
            imagen = pygame.transform.smoothscale(
                imagen, (int(imagen.get_width() * escala), int(imagen.get_height() * escala)))
        s.blit(imagen, imagen.get_rect(center=(x, 66)))

    def _dibujar_indicadores(self, s):
        for i, x in enumerate(DIANAS_X):
            arriba = self.dianas_arriba[i]
            s.blit(self._placa, self._placa.get_rect(center=(x, INDICADOR_Y)))
            lampara = (x - 58, INDICADOR_Y)
            pulso = 0.5 + 0.5 * math.sin(self._t * (3 if arriba else 9))
            if pulso > 0.35 or self._lampara_flash[i] > 0:
                halo = self._halos[arriba]
                s.blit(halo, halo.get_rect(center=lampara), special_flags=pygame.BLEND_RGB_ADD)
            s.blit(self._lamparas[arriba], self._lamparas[arriba].get_rect(center=lampara))
            texto = f"{i + 1}: {'ARRIBA' if arriba else 'DERRIBADA'}"
            imagen = self._tipo_indicador.render(texto, True, c.CREMA)
            s.blit(imagen, imagen.get_rect(midleft=(x - 42, INDICADOR_Y)))

    def _dibujar_invitacion(self, s):
        """En espera, el lugar de los indicadores invita a jugar: las letras hacen la ola."""
        ancho = sum(letra.get_width() - 5 for letra in self._letras)
        x = 490 - ancho / 2
        for i, letra in enumerate(self._letras):
            onda = math.sin(self._t * 4 - i * 0.5)
            s.blit(letra, (x, INDICADOR_Y - letra.get_height() / 2 - max(0.0, onda) * 7))
            x += letra.get_width() - 5

    def dibujar_avisos(self, s, aviso, ayuda):
        """Aviso de conexión y ayuda del simulador: chicos y sin estorbar."""
        if aviso:
            imagen = self._tipo_aviso.render(aviso, True, (255, 230, 200))
            fondo = pygame.Surface((imagen.get_width() + 20, imagen.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(fondo, (30, 10, 10, 190), fondo.get_rect(), border_radius=8)
            fondo.blit(imagen, (10, 4))
            s.blit(fondo, (10, 10))
        if ayuda:
            imagen = self._tipo_aviso.render(ayuda, True, (255, 240, 210))
            fondo = pygame.Surface((imagen.get_width() + 16, imagen.get_height() + 6), pygame.SRCALPHA)
            pygame.draw.rect(fondo, (20, 10, 10, 150), fondo.get_rect(), border_radius=6)
            fondo.blit(imagen, (8, 3))
            s.blit(fondo, (8, c.ALTO - fondo.get_height() - 6))