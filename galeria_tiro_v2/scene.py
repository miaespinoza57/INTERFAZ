"""Escena: puesto de feria, estantes con premios, foquitos y mostrador.

Las dianas son físicas: aquí solo se marca dónde cayó cada impacto."""

import math
import random

import pygame

import config as c
from dibujo import (aclarar, bola, brillo, capsula, circulo, degradado, elipse,
                    estrella, fuente, limitar, linea_redonda, oscurecer, poligono, rayos,
                    rect_redondo, sombra_elipse, suavizar, texto_borde, acercar)

K = 2  # Lo estático se dibuja al doble de tamaño y se reduce para suavizar bordes

# Pisos de los cuatro estantes (nivel -> altura en pantalla)
PISO_ESTANTE = {3: 250, 2: 328, 1: 390, 0: 442}
ESTANTE_X = (70, 725)        # El estante es angosto: a la derecha va el tablero de puntajes
DIANAS_X = (230, 490, 750)   # Columna de cada diana física en el mostrador
IMPACTO_Y = 536              # Altura donde se dibuja el destello de un impacto
MOSTRADOR_Y = 578
FESTONES = 16           # Ondas del faldón del toldo

COLORES_FOCO = [(255, 70, 60), (255, 200, 50), (70, 200, 255), (110, 230, 110), (255, 120, 220)]


# --- Premios ---------------------------------------------------------------
# Cada premio se dibuja una vez en un lienzo de 400x400 y luego se escala.

def _lienzo():
    return pygame.Surface((400, 400), pygame.SRCALPHA)


def _peluche(cuerpo, panza, orejas="oso", mono=None):
    s = _lienzo()
    b = 10
    sombra = oscurecer(cuerpo, 0.7)
    # Piernas con plantas
    for x in (86, 218):
        bola(s, cuerpo, (x, 300, 96, 84), b)
        elipse(s, panza, (x + 22, 328, 52, 40), 0)
        for dx in (30, 48, 66):
            pygame.draw.circle(s, sombra, (x + dx, 318), 6)
    # Brazos
    capsula(s, sombra, (118, 230), (72, 282), 46, b)
    capsula(s, sombra, (282, 230), (328, 282), 46, b)
    capsula(s, cuerpo, (114, 228), (70, 278), 34, 0)
    capsula(s, cuerpo, (278, 228), (324, 278), 34, 0)
    # Cuerpo, panza y costura
    bola(s, cuerpo, (110, 200, 180, 170), b)
    elipse(s, panza, (146, 238, 108, 112), 0)
    for y in range(252, 340, 20):
        pygame.draw.line(s, oscurecer(panza, 0.8), (200, y), (200, y + 10), 4)
    # Orejas
    if orejas == "conejo":
        for x in (118, 226):
            bola(s, cuerpo, (x, 4, 56, 130), b)
            elipse(s, panza, (x + 16, 26, 24, 90), 0)
    else:
        for x in (76, 240):
            bola(s, cuerpo, (x, 24, 84, 84), b)
            pygame.draw.circle(s, panza, (x + 42, 66), 22)
    # Cabeza
    bola(s, cuerpo, (92, 44, 216, 182), b)
    elipse(s, panza, (150, 128, 100, 78), 0)
    elipse(s, (250, 150, 150), (108, 132, 36, 24), 0)
    elipse(s, (250, 150, 150), (256, 132, 36, 24), 0)
    for x in (156, 244):
        pygame.draw.circle(s, c.TINTA, (x, 114), 15)
        pygame.draw.circle(s, (255, 255, 255), (x + 5, 108), 6)
        pygame.draw.circle(s, (255, 255, 255), (x - 5, 120), 3)
    elipse(s, c.TINTA, (180, 134, 40, 26), 0)
    elipse(s, (120, 110, 120), (188, 138, 14, 7), 0)
    pygame.draw.line(s, c.TINTA, (200, 158), (200, 170), 6)
    pygame.draw.arc(s, c.TINTA, (172, 146, 30, 36), math.pi * 1.1, math.pi * 2.0, 6)
    pygame.draw.arc(s, c.TINTA, (198, 146, 30, 36), math.pi * 1.0, math.pi * 1.9, 6)
    if mono:
        oscuro = oscurecer(mono, 0.7)
        for signo in (-1, 1):
            poligono(s, mono, [(200, 226), (200 + signo * 62, 194), (200 + signo * 62, 260)], b)
            pygame.draw.polygon(s, oscuro, [(200, 226), (200 + signo * 56, 236), (200 + signo * 56, 254)])
        circulo(s, oscuro, (200, 226), 18, b)
        pygame.draw.circle(s, mono, (196, 222), 12)
    return s


def _trofeo(claro, medio, oscuro):
    s = _lienzo()
    b = 10
    # Asas
    for x in (92, 308):
        pygame.draw.circle(s, c.TINTA, (x, 120), 62, 30)
        pygame.draw.circle(s, medio, (x, 120), 54, 14)
        pygame.draw.arc(s, claro, (x - 54, 66, 108, 108), math.pi * 0.6, math.pi * 1.1, 6)
    # Base de madera con placa
    rect_redondo(s, c.MADERA_OSCURA, (104, 346, 192, 46), 6, b)
    pygame.draw.rect(s, c.MADERA, (104, 346, 192, 14), border_radius=6)
    rect_redondo(s, claro, (160, 364, 80, 18), 3, 4)
    rect_redondo(s, oscuro, (138, 308, 124, 38), 6, b)
    pygame.draw.rect(s, medio, (138, 308, 124, 12), border_radius=6)
    poligono(s, medio, [(178, 220), (222, 220), (236, 308), (164, 308)], b)
    pygame.draw.polygon(s, oscuro, [(206, 224), (222, 224), (234, 306), (214, 306)])
    # Copa con bandas de luz, como metal pulido
    copa = [(84, 26), (316, 26), (300, 130), (258, 200), (200, 226), (142, 200), (100, 130)]
    poligono(s, medio, copa, b)
    pygame.draw.polygon(s, claro, [(108, 36), (158, 36), (160, 176), (128, 130)])
    pygame.draw.polygon(s, (255, 255, 255), [(120, 40), (136, 40), (140, 128), (126, 108)])
    pygame.draw.polygon(s, oscuro, [(262, 36), (306, 36), (292, 128), (254, 190), (228, 210), (256, 120)])
    pygame.draw.polygon(s, aclarar(medio, 0.3), [(286, 40), (298, 40), (286, 118), (276, 130)])
    elipse(s, oscuro, (84, 10, 232, 36), b)
    pygame.draw.ellipse(s, oscurecer(oscuro, 0.75), (104, 18, 192, 22))
    poligono(s, claro, estrella(204, 112, 40, 17), 6)
    return s


def _patito():
    s = _lienzo()
    b = 10
    amarillo = (255, 216, 60)
    poligono(s, amarillo, [(330, 210), (378, 148), (360, 250)], b)
    bola(s, amarillo, (56, 190, 300, 180), b)
    elipse(s, (255, 240, 150), (96, 222, 150, 60), 0)
    pygame.draw.arc(s, c.TINTA, (150, 236, 150, 96), math.pi * 1.0, math.pi * 1.9, 8)
    bola(s, amarillo, (60, 56, 180, 176), b)
    elipse(s, (255, 244, 170), (84, 76, 74, 44), 0)
    poligono(s, c.NARANJA, [(70, 126), (4, 146), (70, 178)], b)
    pygame.draw.line(s, c.TINTA, (10, 150), (68, 152), 5)
    pygame.draw.circle(s, c.TINTA, (120, 118), 16)
    pygame.draw.circle(s, (255, 255, 255), (125, 112), 6)
    elipse(s, (255, 170, 140), (124, 146, 34, 20), 0)
    return s


def _pelota():
    s = _lienzo()
    circulo(s, c.CREMA, (200, 210), 170, 10)
    for i, tono in enumerate((c.ROJO, c.AZUL, c.MOSTAZA)):
        a = i * 2 * math.pi / 3
        pts = [(200, 210)]
        for j in range(13):
            ang = a + j * (math.pi / 3) / 12
            pts.append((200 + math.cos(ang) * 168, 210 + math.sin(ang) * 168))
        pygame.draw.polygon(s, tono, pts)
    # Sombra en media luna y brillo
    capa = pygame.Surface((400, 400), pygame.SRCALPHA)
    pygame.draw.circle(capa, (40, 0, 40, 70), (200, 210), 169)
    pygame.draw.circle(capa, (0, 0, 0, 0), (176, 184), 160)
    s.blit(capa, (0, 0))
    circulo(s, c.CREMA, (200, 210), 32, 8)
    elipse(s, (255, 255, 255), (108, 88, 76, 46), 0)
    return s


def _llavero():
    s = _lienzo()
    plata = (200, 205, 215)
    pygame.draw.circle(s, c.TINTA, (200, 74), 62, 24)
    pygame.draw.circle(s, plata, (200, 74), 56, 12)
    pygame.draw.arc(s, (255, 255, 255), (148, 22, 104, 104), math.pi * 0.55, math.pi * 1.0, 5)
    for y in range(146, 216, 26):
        elipse(s, plata, (188, y, 24, 28), 7)
    poligono(s, oscurecer(c.ROJO, 0.75), estrella(200, 284, 112, 50), 10)
    pygame.draw.polygon(s, c.ROJO, estrella(194, 278, 98, 44))
    pygame.draw.polygon(s, aclarar(c.ROJO, 0.45), estrella(178, 258, 30, 13))
    return s


def _paleta():
    s = _lienzo()
    capsula(s, c.CREMA, (200, 230), (200, 388), 16, 8)
    rosa = (255, 110, 170)
    circulo(s, oscurecer(rosa, 0.8), (200, 140), 128, 10)
    pygame.draw.circle(s, rosa, (194, 134), 118)
    espiral = []
    for i in range(70):
        a = i * 0.26
        r = 6 + i * 1.6
        espiral.append((200 + math.cos(a) * r, 140 + math.sin(a) * r))
    linea_redonda(s, (255, 244, 248), espiral, 15)
    elipse(s, (255, 255, 255), (122, 52, 60, 34), 0)
    return s


ORO_TONOS = ((255, 244, 170), (255, 200, 50), (196, 130, 20))
PLATA_TONOS = ((245, 248, 252), (192, 200, 212), (122, 132, 150))


def _crear_arte():
    return {
        "pelota": _pelota(),
        "llavero": _llavero(),
        "patito": _patito(),
        "paleta": _paleta(),
        "osito": _peluche((206, 140, 84), (244, 212, 164), mono=c.AZUL),
        "conejito": _peluche((240, 170, 200), (255, 232, 238), "conejo", c.ROJO),
        "osito_azul": _peluche((96, 170, 224), (214, 238, 250), mono=c.MOSTAZA),
        "oso_mediano": _peluche((170, 104, 60), (236, 200, 150), mono=c.VERDE),
        "conejo_mediano": _peluche((236, 232, 224), (250, 190, 200), "conejo", c.AZUL),
        "trofeo_plata": _trofeo(*PLATA_TONOS),
        "oso_gigante": _peluche((182, 104, 50), (250, 214, 160), mono=c.ROJO),
        "trofeo_oro": _trofeo(*ORO_TONOS),
    }


class Premio:
    def __init__(self, arte, nombre, nivel, x, alto, indice):
        self.nombre = nombre
        self.nivel = nivel
        self.x = x
        self.alto = alto
        self.indice = indice        # Posición dentro de su estante (para la ola)
        self.grande = arte[nombre]
        # Sprite del estante: el premio con su sombra de contacto
        self.chico = pygame.Surface((alto + 16, alto + 8), pygame.SRCALPHA)
        sombra = sombra_elipse(alto + 16, max(14, alto // 4), 130)
        self.chico.blit(sombra, (0, alto + 8 - sombra.get_height()))
        self.chico.blit(pygame.transform.smoothscale(self.grande, (alto, alto)), (8, 0))
        self.pos = (x - alto // 2 - 8, PISO_ESTANTE[nivel] - alto + 3)
        self.oculto = False

    @property
    def centro(self):
        return self.x, PISO_ESTANTE[self.nivel] - self.alto // 2


def _colocar_premios(arte):
    premios = []

    def fila(nivel, nombres, x_inicial, paso, alto):
        for i, nombre in enumerate(nombres):
            premios.append(Premio(arte, nombre, nivel, x_inicial + i * paso, alto, i))

    fila(0, ["pelota", "patito", "llavero", "paleta"] * 2 + ["pelota", "patito"], 110, 60, 44)
    fila(1, ["osito", "conejito", "osito_azul"] * 2 + ["osito", "conejito"], 110, 78, 56)
    fila(2, ["oso_mediano", "trofeo_plata", "conejo_mediano", "trofeo_plata", "oso_mediano", "trofeo_plata"],
         120, 104, 72)
    premios.append(Premio(arte, "oso_gigante", 3, 190, 128, 0))
    premios.append(Premio(arte, "trofeo_oro", 3, 340, 112, 1))
    return premios


class PremioEnVuelo:
    """Un premio que sale del estante y se acerca a la cámara."""

    DURACION = 1.5

    def __init__(self, premio, destino, alto_final, retraso=0.0):
        self.premio = premio
        self.destino = destino
        self.alto_final = alto_final
        self.t = -retraso
        self.llego = False
        self._final = None      # Imagen ya escalada, para no repetir el trabajo

    def actualizar(self, dt):
        self.t += dt

    @property
    def avance(self):
        x = limitar(self.t / self.DURACION)
        # Curva con un pequeño rebote al llegar
        return 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2

    @property
    def posicion(self):
        p = self.avance
        ox, oy = self.premio.centro
        x = ox + (self.destino[0] - ox) * p
        # Sube un poco a mitad del camino, como si saltara del estante
        y = oy + (self.destino[1] - oy) * p - math.sin(min(p, 1) * math.pi) * 40
        if self.t > self.DURACION:
            y += math.sin((self.t - self.DURACION) * 2.4) * 7     # Flota mientras lo entregan
        return x, y

    def dibujar(self, s):
        p = self.avance
        lado = max(8, int(self.premio.alto + (self.alto_final - self.premio.alto) * p))
        if self.t > self.DURACION:
            if self._final is None:
                self._final = pygame.transform.smoothscale(self.premio.grande, (self.alto_final,) * 2)
            imagen = self._final
        else:
            imagen = pygame.transform.smoothscale(self.premio.grande, (lado, lado))
        s.blit(imagen, imagen.get_rect(center=self.posicion))


# --- Foquitos ---------------------------------------------------------------

class Foquitos:
    """Tira de focos de colores: una ola de luz los recorre y destellan con los impactos."""

    def __init__(self, posiciones, radio=7):
        self.posiciones = posiciones
        self.velocidad = 3.0
        self._t = 0.0
        self._flash = 0.0
        self._prendido = []
        self._apagado = []
        self._halo = []
        for color in COLORES_FOCO:
            self._prendido.append(self._foco(color, radio, True))
            self._apagado.append(self._foco(oscurecer(color, 0.36), radio, False))
            self._halo.append([brillo(radio * 4, color, fuerza) for fuerza in (70, 125, 185)])

    @staticmethod
    def _foco(color, radio, prendido):
        lado = (radio + 5) * 2 * K
        s = pygame.Surface((lado, lado), pygame.SRCALPHA)
        cx = cy = lado // 2
        r = radio * K
        # Casquillo y bombilla
        rect_redondo(s, (70, 64, 74), (cx - r * 0.5, cy - r - 3 * K, r, 5 * K), 2, 2 * K)
        circulo(s, oscurecer(color, 0.8), (cx, cy), r, 2 * K)
        pygame.draw.circle(s, color, (cx - 1, cy - 1), r - 2)
        if prendido:
            pygame.draw.circle(s, aclarar(color, 0.55), (cx, cy), int(r * 0.55))
        pygame.draw.circle(s, aclarar(color, 0.85 if prendido else 0.35), (cx - r // 3, cy - r // 3), max(2, r // 3))
        return suavizar(s, K)

    def destello(self):
        """Todos los focos se prenden de golpe y se van apagando."""
        self._flash = 1.0

    def actualizar(self, dt):
        self._t += dt * self.velocidad
        self._flash = max(0.0, self._flash - dt * 2.6)

    def dibujar(self, s):
        fase = self._t * 2.1
        for i, pos in enumerate(self.posiciones):
            color = i % len(COLORES_FOCO)
            onda = 0.5 + 0.5 * math.cos(i * 2.0944 - fase)       # Un foco de cada tres
            fuerza = max(limitar((onda - 0.2) * 1.8), self._flash)
            apagado = self._apagado[color]
            rect = apagado.get_rect(center=pos)
            s.blit(apagado, rect)
            if fuerza > 0.08:
                halo = self._halo[color][min(2, int(fuerza * 3))]
                s.blit(halo, halo.get_rect(center=pos), special_flags=pygame.BLEND_RGB_ADD)
                prendido = self._prendido[color]
                prendido.set_alpha(int(255 * fuerza))
                s.blit(prendido, rect)


# --- Escena completa --------------------------------------------------------

class Escena:
    def __init__(self, particulas):
        self._fx = particulas
        self._azar = random.Random(11)      # Vetas y nudos siempre iguales
        self.fondo = self._crear_fondo()
        self.toldo = self._crear_toldo()
        self._festones = self._crear_festones()
        self.frente = self._crear_mostrador()
        self.premios = _colocar_premios(_crear_arte())
        self.foquitos = Foquitos(self._posiciones_foquitos())
        self.vuelos = []
        self.en_espera = True
        self._rayos = rayos(340)
        self._halo = brillo(250, (255, 196, 90), 135)
        self._giro = 0.0
        self._velo = 0.0           # Oscurecimiento de la pantalla de resultados
        self._velo_objetivo = 0.0
        self._capa_velo = pygame.Surface((c.ANCHO, c.ALTO))
        self._chispas = [self._crear_chispa(14), self._crear_chispa(9)]
        self._t = 0.0
        self._olas = {}            # nivel -> segundos desde que empezó la ola
        self._prox_ola = 3.0
        self._temblor = 0.0

    @staticmethod
    def _crear_chispa(radio):
        s = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pygame.draw.polygon(s, (255, 255, 230), estrella(radio, radio, radio, radio * 0.2, 4, 0))
        return s

    @staticmethod
    def _posiciones_foquitos():
        # La tira de arriba cuelga en curvas entre ganchos, como un cable de verdad
        arriba = [(x, Escena._altura_cable(x)) for x in range(60, c.ANCHO - 30, 58)]
        izquierda = [(22, y) for y in range(190, MOSTRADOR_Y, 58)]
        derecha = [(c.ANCHO - 22, y) for y in range(190, MOSTRADOR_Y, 58)]
        return arriba + izquierda + derecha

    @staticmethod
    def _altura_cable(x):
        u = (x % 232) / 232
        return 112 + 64 * u * (1 - u)

    # -- Construcción del arte estático --
    def _crear_fondo(self):
        s = pygame.Surface((c.ANCHO * K, c.ALTO * K))
        azar = self._azar

        def R(x, y, w, h):
            return pygame.Rect(int(x * K), int(y * K), int(w * K), int(h * K))

        # Cielo de atardecer con estrellas, se asoma junto al toldo
        s.blit(degradado(c.ANCHO * K, 130 * K, (26, 20, 66), (150, 70, 110)), (0, 0))
        for _ in range(40):
            pygame.draw.circle(s, (255, 240, 210), (azar.randrange(c.ANCHO * K), azar.randrange(80 * K)),
                               azar.choice((1, 2, 2, 3)))

        # Pared de tablones pintados, con vetas y nudos
        tonos = [(128, 46, 38), (140, 52, 40), (118, 42, 36)]
        for i, x in enumerate(range(0, c.ANCHO, 64)):
            base = tonos[i % 3]
            pygame.draw.rect(s, base, R(x, 90, 64, 520))
            for _ in range(6):
                gx = x + azar.uniform(5, 59)
                tono = oscurecer(base, 0.88) if azar.random() < 0.6 else aclarar(base, 0.08)
                pygame.draw.line(s, tono, (gx * K, 90 * K), ((gx + azar.uniform(-4, 4)) * K, 610 * K), K)
            if azar.random() < 0.6:
                nx, ny = x + azar.uniform(16, 48), azar.uniform(150, 560)
                pygame.draw.ellipse(s, oscurecer(base, 0.7), R(nx - 6, ny - 9, 12, 18))
                pygame.draw.ellipse(s, base, R(nx - 3, ny - 5, 6, 10))
            pygame.draw.line(s, (72, 24, 26), (x * K, 90 * K), (x * K, 610 * K), 3 * K)
            pygame.draw.line(s, aclarar(base, 0.14), ((x + 2.5) * K, 90 * K), ((x + 2.5) * K, 610 * K), K)
            for y in (170, 400):
                pygame.draw.circle(s, (60, 22, 24), ((x + 12) * K, y * K), 2 * K)

        # Mueble de estantes con tapiz de rombos
        x0, x1 = ESTANTE_X
        interior = R(x0, 112, x1 - x0, 342)
        pygame.draw.rect(s, (62, 28, 50), interior)
        s.set_clip(interior)
        for fila, y in enumerate(range(100, 470, 30)):
            for x in range(x0 - 44 + (fila % 2) * 22, x1 + 44, 44):
                pygame.draw.polygon(s, (92, 46, 78), [((x + 22) * K, y * K), ((x + 44) * K, (y + 30) * K),
                                                      ((x + 22) * K, (y + 60) * K), (x * K, (y + 30) * K)], 0 if fila % 2 else 2 * K)
        s.set_clip(None)
        s.blit(degradado(interior.w, 150 * K, (10, 0, 20, 170), (10, 0, 20, 0)), interior.topleft)
        for nivel, piso in PISO_ESTANTE.items():
            # Luz cálida que baja de cada repisa y sombra debajo
            s.blit(degradado(interior.w, 30 * K, (0, 0, 0, 120), (0, 0, 0, 0)), (x0 * K, (piso + 12) * K))
            s.blit(degradado(interior.w, 46 * K, (255, 190, 110, 0), (255, 190, 110, 52)), (x0 * K, (piso - 46) * K))
            rect_redondo(s, c.MADERA_CLARA, R(x0 - 12, piso, x1 - x0 + 24, 12), 3 * K, 3 * K)
            pygame.draw.rect(s, aclarar(c.MADERA_CLARA, 0.3), R(x0 - 10, piso, x1 - x0 + 20, 2.5))
            pygame.draw.rect(s, c.MADERA, R(x0 - 12, piso + 7, x1 - x0 + 24, 5))
        for x in (x0 - 8, x1 - 8):
            rect_redondo(s, c.MADERA, R(x, 112, 16, 346), 2 * K, 3 * K)
            pygame.draw.rect(s, c.MADERA_CLARA, R(x + 2, 112, 4, 346))

        # Cartel en forma de flecha que señala el gran premio
        cartel = texto_borde(fuente(24 * K, True), "¡GRAN PREMIO!", c.ORO, grosor=3 * K)
        rect = cartel.get_rect(center=(530 * K, 190 * K))
        caja = rect.inflate(30 * K, 16 * K)
        flecha = [(caja.left, caja.top), (caja.right, caja.top), (caja.right, caja.bottom), (caja.left, caja.bottom),
                  (caja.left, caja.bottom + 8 * K), (caja.left - 34 * K, caja.centery), (caja.left, caja.top - 8 * K)]
        poligono(s, c.ROJO_OSCURO, flecha, 3 * K)
        pygame.draw.polygon(s, c.ROJO, [(caja.left, caja.top), (caja.right, caja.top), (caja.right, caja.top + 9 * K),
                                        (caja.left, caja.top + 9 * K)])
        for i in range(9):
            bx = caja.left + 10 * K + i * (caja.w - 20 * K) / 8
            for by in (caja.top - 1, caja.bottom + 1):
                circulo(s, c.ORO, (bx, by), 3 * K, 2 * K)
        s.blit(cartel, rect)

        # Postes laterales tipo caramelo, con volumen
        for x in (0, c.ANCHO - 44):
            poste = R(x, 90, 44, 530)
            pygame.draw.rect(s, c.CREMA, poste)
            s.set_clip(poste)
            for y in range(40, 680, 56):
                pygame.draw.polygon(s, c.ROJO, [(x * K, y * K), ((x + 44) * K, (y - 34) * K),
                                                ((x + 44) * K, (y - 6) * K), (x * K, (y + 28) * K)])
            s.set_clip(None)
            s.blit(degradado(18 * K, poste.h, (30, 0, 20, 150), (30, 0, 20, 0), True), poste.topleft)
            s.blit(degradado(18 * K, poste.h, (30, 0, 20, 0), (30, 0, 20, 170), True), ((x + 26) * K, poste.y))
            pygame.draw.rect(s, (255, 255, 255), R(x + 17, 90, 3, 530))
            pygame.draw.rect(s, c.TINTA, poste, 3 * K)

        # Sombra del toldo sobre la pared
        s.blit(degradado(c.ANCHO * K, 80 * K, (0, 0, 0, 130), (0, 0, 0, 0)), (0, 108 * K))

        # Cable de los foquitos
        cable = [(x * K, (self._altura_cable(x) - 5) * K) for x in range(0, c.ANCHO + 1, 4)]
        for tramo in range(0, len(cable) - 1, 58):
            pygame.draw.lines(s, (30, 22, 30), False, cable[tramo:tramo + 59], 2 * K)
        return suavizar(s, K)

    @staticmethod
    def _crear_toldo():
        """Toldo a rayas en perspectiva; va en su propia capa, delante del faldón."""
        s = pygame.Surface((c.ANCHO * K, 100 * K), pygame.SRCALPHA)
        ancho_abajo = c.ANCHO / FESTONES
        ancho_arriba = (c.ANCHO - 200) / FESTONES
        corte = 0.45        # Hasta aquí llega la franja de sombra
        for i in range(FESTONES):
            tono = c.ROJO if i % 2 == 0 else c.CREMA
            a0, a1 = 100 + i * ancho_arriba, 100 + (i + 1) * ancho_arriba
            b0, b1 = i * ancho_abajo, (i + 1) * ancho_abajo
            m0, m1 = a0 + (b0 - a0) * corte, a1 + (b1 - a1) * corte
            ym = -10 + (92 * K + 10) * corte
            pygame.draw.polygon(s, oscurecer(tono, 0.74), [(a0 * K, -10), (a1 * K, -10), (m1 * K, ym), (m0 * K, ym)])
            pygame.draw.polygon(s, tono, [(m0 * K, ym), (m1 * K, ym), (b1 * K, 92 * K), (b0 * K, 92 * K)])
            pygame.draw.polygon(s, aclarar(tono, 0.3), [((b0 + (a0 - b0) * 0.12) * K, 81 * K), ((b1 + (a1 - b1) * 0.12) * K, 81 * K),
                                                        (b1 * K, 92 * K), (b0 * K, 92 * K)])
            pygame.draw.line(s, c.TINTA, (a0 * K, -10), (b0 * K, 92 * K), 3 * K)
        pygame.draw.line(s, c.TINTA, (0, 92 * K), (c.ANCHO * K, 92 * K), 4 * K)
        return suavizar(s, K)

    @staticmethod
    def _crear_festones():
        """Las ondas del faldón, una roja y una crema; se mecen con el viento."""
        ancho = c.ANCHO / FESTONES
        sprites = []
        for tono in (c.ROJO, c.CREMA):
            s = pygame.Surface((int(ancho + 8) * K, 52 * K), pygame.SRCALPHA)
            rect = pygame.Rect(4 * K, 2 * K, int(ancho * K), 44 * K)
            elipse(s, oscurecer(tono, 0.72), rect, 3 * K)
            pygame.draw.ellipse(s, tono, rect.inflate(-8 * K, -8 * K).move(0, -4 * K))
            pygame.draw.rect(s, tono, (rect.x, 0, rect.w, 24 * K))
            pygame.draw.rect(s, oscurecer(tono, 0.8), (rect.x, 20 * K, rect.w, 5 * K))
            sprites.append(suavizar(s, K))
        return sprites

    def _crear_mostrador(self):
        alto = c.ALTO - MOSTRADOR_Y + 6
        azar = self._azar
        s = pygame.Surface((c.ANCHO * K, alto * K), pygame.SRCALPHA)
        # Frente de tablones con vetas
        tonos = [c.MADERA, (162, 100, 52), (186, 120, 66)]
        for i, x in enumerate(range(0, c.ANCHO, 80)):
            base = tonos[i % 3]
            pygame.draw.rect(s, base, (x * K, 26 * K, 80 * K, alto * K))
            for _ in range(7):
                gx = x + azar.uniform(6, 74)
                pygame.draw.line(s, oscurecer(base, 0.86), (gx * K, 26 * K), ((gx + azar.uniform(-5, 5)) * K, alto * K), K)
            pygame.draw.line(s, c.MADERA_OSCURA, (x * K, 26 * K), (x * K, alto * K), 3 * K)
            pygame.draw.line(s, aclarar(base, 0.2), ((x + 2.5) * K, 26 * K), ((x + 2.5) * K, alto * K), K)
        s.blit(degradado(c.ANCHO * K, 30 * K, (0, 0, 0, 120), (0, 0, 0, 0)), (0, 26 * K))
        s.blit(degradado(c.ANCHO * K, 50 * K, (0, 0, 0, 0), (0, 0, 0, 90)), (0, (alto - 50) * K))
        # Cubierta
        rect_redondo(s, c.MADERA_CLARA, (-20, 6 * K, (c.ANCHO + 20) * K, 20 * K), 3 * K, 3 * K)
        pygame.draw.rect(s, aclarar(c.MADERA_CLARA, 0.35), (0, 6 * K, c.ANCHO * K, 4 * K))
        pygame.draw.rect(s, c.MADERA, (0, 19 * K, c.ANCHO * K, 7 * K))
        # Tablero pintado con el nombre del puesto
        tablero = pygame.Rect(150 * K, 68 * K, 680 * K, 50 * K)
        rect_redondo(s, c.ROJO_OSCURO, tablero, 10 * K, 3 * K)
        pygame.draw.rect(s, c.ORO, tablero.inflate(-8 * K, -8 * K), 2 * K, border_radius=7 * K)
        letrero = texto_borde(fuente(32 * K, True), "GALERÍA DE TIRO LÁSER", c.MOSTAZA, grosor=3 * K)
        s.blit(letrero, letrero.get_rect(center=tablero.center))
        for x in (tablero.left + 34 * K, tablero.right - 34 * K):
            poligono(s, c.ORO, estrella(x, tablero.centery, 13 * K, 5.5 * K), 2 * K)
        return suavizar(s, K)

    # -- Eventos --
    @staticmethod
    def punto_impacto(numero):
        return DIANAS_X[numero - 1], IMPACTO_Y

    def ola(self, nivel=None):
        """Los premios de un estante brincan uno tras otro."""
        self._olas[random.randrange(4) if nivel is None else nivel] = 0.0

    def impacto(self, numero):
        """Chispas y estrellas sobre el indicador de esa diana, y un temblor en los estantes."""
        x, y = self.punto_impacto(numero)
        self._fx.emitir(x, y, 14, (c.ROJO, c.CREMA, c.MADERA_CLARA), velocidad=(160, 460), vida=(0.5, 0.9),
                        tam=(5, 10), gravedad=1100, angulo=(math.pi, math.tau))
        self._fx.emitir(x, y, 7, (c.ORO, (255, 255, 255)), velocidad=(120, 330), vida=(0.5, 0.8),
                        tam=(9, 15), gravedad=500, forma="estrella")
        self._fx.emitir(x, y, 10, ((255, 190, 90),), velocidad=(60, 260), vida=(0.3, 0.6), tam=(14, 26),
                        gravedad=0, forma="brillo", freno=4)
        self._temblor = 1.0
        self.foquitos.destello()

    def iniciar_premio(self, nivel):
        """Saca del estante el premio del nivel indicado y lo trae a la cámara."""
        self.retirar_premio()
        candidatos = [p for p in self.premios if p.nivel == nivel]
        if nivel == 3:
            oso, trofeo = candidatos
            self.vuelos.append(PremioEnVuelo(oso, (640, 420), 300))
            self.vuelos.append(PremioEnVuelo(trofeo, (800, 475), 190, 0.25))
        else:
            self.vuelos.append(PremioEnVuelo(random.choice(candidatos), (690, 430), 270))
        for vuelo in self.vuelos:
            vuelo.premio.oculto = True
        self._velo_objetivo = 165

    def retirar_premio(self):
        for vuelo in self.vuelos:
            vuelo.premio.oculto = False
        self.vuelos.clear()
        self._velo_objetivo = 0

    # -- Bucle --
    def actualizar(self, dt):
        self._t += dt
        self._giro = (self._giro + 24 * dt) % 360
        self._velo = acercar(self._velo, self._velo_objetivo, 5.0, dt)
        self._temblor = max(0.0, self._temblor - dt * 3)
        self.foquitos.actualizar(dt)
        for nivel in list(self._olas):
            self._olas[nivel] += dt
            if self._olas[nivel] > 2.2:
                del self._olas[nivel]
        if self.en_espera:
            self._prox_ola -= dt
            if self._prox_ola <= 0:
                self._prox_ola = random.uniform(2.5, 5.0)
                self.ola()
        self._actualizar_vuelos(dt)

    def _actualizar_vuelos(self, dt):
        colores = (c.ORO, (255, 255, 255), (255, 236, 150))
        for vuelo in self.vuelos:
            vuelo.actualizar(dt)
            if vuelo.t < 0:
                continue
            x, y = vuelo.posicion
            if not vuelo.llego and vuelo.t >= vuelo.DURACION * 0.8:
                vuelo.llego = True
                self._fx.emitir(x, y, 22, colores, velocidad=(140, 420), vida=(0.6, 1.1), tam=(9, 16),
                                gravedad=260, forma="estrella")
            elif not vuelo.llego and random.random() < dt * 40:
                self._fx.emitir(x, y, 1, colores, velocidad=(10, 60), vida=(0.3, 0.6), tam=(12, 22),
                                gravedad=0, forma="brillo")
            elif vuelo.llego and random.random() < dt * 5:
                radio = vuelo.alto_final * 0.45
                self._fx.emitir(x + random.uniform(-radio, radio), y + random.uniform(-radio, radio), 1,
                                colores, velocidad=(0, 12), vida=(0.4, 0.7), tam=(7, 12), gravedad=0, forma="estrella")

    def _desplazamiento(self, premio):
        """Brinco de la ola y temblor por impacto de cada premio."""
        dx = dy = 0.0
        if premio.nivel in self._olas:
            u = self._olas[premio.nivel] * 2.4 - premio.indice * 0.13
            if 0 < u < 1:
                dy = -math.sin(u * math.pi) * (7 + premio.alto * 0.06)
        if self._temblor > 0:
            dx = math.sin(self._t * 55 + premio.x) * 2.5 * self._temblor
        return dx, dy

    def dibujar(self, s):
        s.blit(self.fondo, (0, 0))
        for premio in self.premios:
            if not premio.oculto:
                dx, dy = self._desplazamiento(premio)
                s.blit(premio.chico, (premio.pos[0] + dx, premio.pos[1] + dy))
        self._dibujar_chispas(s)
        s.blit(self.frente, (0, MOSTRADOR_Y - 6))
        # Faldón del toldo meciéndose
        ancho = c.ANCHO / FESTONES
        for i in range(FESTONES):
            vaiven = math.sin(self._t * 2.3 + i * 0.8) * 2.5 + math.sin(self._t * 1.1 + i * 0.3) * 1.5
            s.blit(self._festones[i % 2], (i * ancho - 4 + vaiven * 0.4, 70 + vaiven))
        s.blit(self.toldo, (0, 0))
        self.foquitos.dibujar(s)

    def _dibujar_chispas(self, s):
        """Destellos intermitentes sobre el trofeo dorado."""
        trofeo = next(p for p in self.premios if p.nombre == "trofeo_oro")
        if trofeo.oculto:
            return
        for i, chispa in enumerate(self._chispas):
            fase = (self._t * 0.8 + i * 0.5) % 1.0
            if fase < 0.3:
                escala = math.sin(fase / 0.3 * math.pi)
                lado = max(2, int(chispa.get_width() * escala))
                imagen = pygame.transform.smoothscale(chispa, (lado, lado))
                x = trofeo.x + (-28 if i == 0 else 30)
                y = trofeo.centro[1] + (-34 if i == 0 else -8)
                s.blit(imagen, imagen.get_rect(center=(x, y)))

    def dibujar_premio(self, s):
        """Velo oscuro, halo, rayos y premios en vuelo (van sobre la escena)."""
        if self._velo > 1:
            # Oscurecer multiplicando es mucho más rápido que una capa transparente
            v = 255 - int(self._velo * 0.9)
            self._capa_velo.fill((v, int(v * 0.9), v))
            s.blit(self._capa_velo, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if not self.vuelos:
            return
        avance = limitar(self.vuelos[0].avance)
        if avance > 0.1:
            cx = sum(v.destino[0] for v in self.vuelos) / len(self.vuelos)
            cy = sum(v.destino[1] for v in self.vuelos) / len(self.vuelos)
            rayos_giro = pygame.transform.rotate(self._rayos, self._giro)
            if avance < 0.98:
                fuerza = int(255 * avance)
                rayos_giro.fill((fuerza, fuerza, fuerza), special_flags=pygame.BLEND_RGB_MULT)
            else:
                s.blit(self._halo, self._halo.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)
            s.blit(rayos_giro, rayos_giro.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)
        for vuelo in self.vuelos:
            if vuelo.t >= 0:
                vuelo.dibujar(s)