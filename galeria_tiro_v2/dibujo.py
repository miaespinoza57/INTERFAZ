"""Utilidades de dibujo estilo caricatura: contornos gruesos, degradados, resortes y brillos."""

import math
from functools import lru_cache

import pygame

from config import TINTA

_fuentes = {}

_FAMILIAS_TITULO = ["impact", "anton", "arialblack", "dejavusanscondensed", "dejavusans"]
_FAMILIAS_TEXTO = ["comicsansms", "comicneue", "trebuchetms", "verdana", "dejavusans"]


# --- Texto -------------------------------------------------------------------

def fuente(tamano, titulo=False):
    """Fuente del sistema con acentos; si no hay ninguna, usa la de pygame."""
    clave = (tamano, titulo)
    if clave not in _fuentes:
        familias = _FAMILIAS_TITULO if titulo else _FAMILIAS_TEXTO
        ruta = pygame.font.match_font(familias, bold=True)
        _fuentes[clave] = pygame.font.Font(ruta, tamano)
    return _fuentes[clave]


@lru_cache(maxsize=512)
def texto_borde(tipo, texto, color, borde=TINTA, grosor=2):
    """Renderiza texto con contorno, como en los carteles de feria.

    El resultado se comparte: copiarlo antes de modificarlo.
    """
    base = tipo.render(texto, True, color)
    contorno = tipo.render(texto, True, borde)
    ancho, alto = base.get_size()
    superficie = pygame.Surface((ancho + grosor * 2, alto + grosor * 2), pygame.SRCALPHA)
    for dx in range(-grosor, grosor + 1):
        for dy in range(-grosor, grosor + 1):
            if dx * dx + dy * dy <= grosor * grosor + 1:
                superficie.blit(contorno, (grosor + dx, grosor + dy))
    superficie.blit(base, (grosor, grosor))
    return superficie


# --- Color -------------------------------------------------------------------

def mezclar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def oscurecer(color, factor=0.78):
    return tuple(int(v * factor) for v in color[:3])


def aclarar(color, cantidad=0.35):
    return tuple(int(v + (255 - v) * cantidad) for v in color[:3])


# --- Figuras con contorno ----------------------------------------------------

def contorno_cerrado(s, pts, borde, color=TINTA):
    """Línea gruesa cerrada con uniones redondeadas."""
    pygame.draw.lines(s, color, True, pts, borde)
    for p in pts:
        pygame.draw.circle(s, color, p, borde / 2)


def linea_redonda(s, color, pts, ancho):
    """Línea abierta gruesa con puntas y uniones redondeadas."""
    pygame.draw.lines(s, color, False, pts, int(ancho))
    for p in pts:
        pygame.draw.circle(s, color, p, ancho / 2)


def poligono(s, color, pts, borde=6):
    pygame.draw.polygon(s, color, pts)
    if borde:
        contorno_cerrado(s, pts, borde)


def elipse(s, color, rect, borde=6):
    rect = pygame.Rect(rect)
    if borde:
        pygame.draw.ellipse(s, TINTA, rect.inflate(borde * 2, borde * 2))
    pygame.draw.ellipse(s, color, rect)


def bola(s, color, rect, borde=6):
    """Elipse con sombreado simple: base oscura y encima la luz, corrida arriba a la izquierda."""
    x, y, w, h = rect
    elipse(s, oscurecer(color), rect, borde)
    pygame.draw.ellipse(s, color, (x + w * 0.03, y + h * 0.03, w * 0.88, h * 0.88))


def circulo(s, color, centro, radio, borde=6):
    if borde:
        pygame.draw.circle(s, TINTA, centro, radio + borde)
    pygame.draw.circle(s, color, centro, radio)


def capsula(s, color, a, b, ancho, borde=6):
    """Segmento con puntas redondas; sirve para brazos, dedos y palos."""
    for tono, grosor in ((TINTA, ancho + borde * 2), (color, ancho)):
        if tono == TINTA and not borde:
            continue
        pygame.draw.line(s, tono, a, b, int(grosor))
        pygame.draw.circle(s, tono, a, grosor / 2)
        pygame.draw.circle(s, tono, b, grosor / 2)


def rect_redondo(s, color, rect, radio=12, borde=6):
    rect = pygame.Rect(rect)
    if borde:
        pygame.draw.rect(s, TINTA, rect.inflate(borde * 2, borde * 2), border_radius=radio + borde)
    pygame.draw.rect(s, color, rect, border_radius=radio)


def estrella(cx, cy, r_ext, r_int, puntas=5, giro=-math.pi / 2):
    """Vértices de una estrella."""
    pts = []
    for i in range(puntas * 2):
        r = r_ext if i % 2 == 0 else r_int
        a = giro + math.pi * i / puntas
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


# --- Curvas ------------------------------------------------------------------

def bezier(p0, p1, p2, p3, pasos=18):
    """Puntos de una curva cúbica de Bézier."""
    puntos = []
    for i in range(pasos + 1):
        t = i / pasos
        u = 1 - t
        puntos.append((
            u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
        ))
    return puntos


def trazo_conico(curva, ancho_inicial, ancho_final):
    """Convierte una curva en un polígono que se adelgaza a lo largo del trazo."""
    izquierda, derecha = [], []
    for i, (x, y) in enumerate(curva):
        ax, ay = curva[max(i - 1, 0)]
        bx, by = curva[min(i + 1, len(curva) - 1)]
        largo = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / largo, (bx - ax) / largo
        ancho = ancho_inicial + (ancho_final - ancho_inicial) * i / (len(curva) - 1)
        izquierda.append((x + nx * ancho / 2, y + ny * ancho / 2))
        derecha.append((x - nx * ancho / 2, y - ny * ancho / 2))
    return izquierda + derecha[::-1]


# --- Superficies -------------------------------------------------------------

def suavizar(superficie, factor=2):
    """Reduce una superficie dibujada en grande: así los bordes salen suaves."""
    ancho, alto = superficie.get_size()
    return pygame.transform.smoothscale(superficie, (ancho // factor, alto // factor))


def degradado(ancho, alto, inicio, fin, horizontal=False):
    """Degradado lineal (de arriba a abajo, o de izquierda a derecha). Acepta RGB o RGBA."""
    pasos = 64
    tira = pygame.Surface((1, pasos), pygame.SRCALPHA)
    for i in range(pasos):
        t = i / (pasos - 1)
        color = [int(inicio[k] + (fin[k] - inicio[k]) * t) for k in range(len(inicio))]
        tira.set_at((0, i), color if len(color) == 4 else color + [255])
    if horizontal:
        tira = pygame.transform.rotate(tira, 90)
    return pygame.transform.smoothscale(tira, (int(ancho), int(alto)))


def desenfocar(superficie, fuerza=6):
    """Desenfoque barato: reducir y volver a ampliar."""
    ancho, alto = superficie.get_size()
    chica = pygame.transform.smoothscale(superficie, (max(1, ancho // fuerza), max(1, alto // fuerza)))
    return pygame.transform.smoothscale(chica, (ancho, alto))


@lru_cache(maxsize=64)
def sombra_elipse(ancho, alto, alfa=90):
    """Sombra suave de contacto."""
    s = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, alfa), (ancho * 0.14, alto * 0.14, ancho * 0.72, alto * 0.72))
    return desenfocar(s, 5)


@lru_cache(maxsize=128)
def brillo(radio, color, intensidad=150):
    """Halo radial para mezclar en modo aditivo."""
    superficie = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
    paso = max(1, radio // 60)
    for r in range(radio, 0, -paso):
        fuerza = (1 - r / radio) ** 2 * intensidad / 255
        tono = tuple(int(v * fuerza) for v in color)
        pygame.draw.circle(superficie, tono + (255,), (radio, radio), r)
    return superficie


def destello(radio, puntas=10, color=(255, 250, 210)):
    """Estrella de impacto de cómic."""
    k = 2
    superficie = pygame.Surface((radio * 2 * k, radio * 2 * k), pygame.SRCALPHA)
    centro = radio * k
    poligono(superficie, color, estrella(centro, centro, radio * k * 0.92, radio * k * 0.48, puntas, 0), 6)
    poligono(superficie, (255, 255, 255), estrella(centro, centro, radio * k * 0.55, radio * k * 0.26, puntas, 0), 0)
    return suavizar(superficie, k)


def rayos(radio, cantidad=14, color=(255, 214, 90)):
    """Abanico de rayos que se desvanece hacia afuera, para el brillo del premio.

    Devuelve una superficie sobre negro para mezclar en modo aditivo (es lo más rápido).
    """
    k = 2
    r = radio * k
    superficie = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    paso = 2 * math.pi / cantidad
    for i in range(cantidad):
        a = i * paso
        b = a + paso / 2
        pygame.draw.polygon(superficie, color + (125,), [
            (r, r), (r + math.cos(a) * r, r + math.sin(a) * r), (r + math.cos(b) * r, r + math.sin(b) * r)])
    mascara = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for radio_m in range(r, 0, -16):
        pygame.draw.circle(mascara, (255, 255, 255, int(255 * (1 - (radio_m / r) ** 2))), (r, r), radio_m)
    superficie.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    aditiva = pygame.Surface((radio * 2, radio * 2))
    aditiva.blit(suavizar(superficie, k), (0, 0))
    return aditiva


# --- Movimiento --------------------------------------------------------------

def limitar(valor, minimo=0.0, maximo=1.0):
    return max(minimo, min(maximo, valor))


def suave(t):
    """Arranque y frenado suaves, de 0 a 1."""
    t = limitar(t)
    return t * t * (3 - 2 * t)


def rebote_salida(t):
    """De 0 a 1 pasándose un poco antes de asentarse."""
    t = limitar(t)
    return 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def acercar(actual, objetivo, velocidad, dt):
    """Interpolación exponencial: igual de suave a cualquier cantidad de FPS."""
    return objetivo + (actual - objetivo) * math.exp(-velocidad * dt)


class Resorte:
    """Resorte amortiguado: persigue un objetivo y se pasa un poco antes de asentarse.

    Da el efecto de inercia de la animación tradicional (el bigote, el sombrero y
    las manos llegan tarde y rebotan) sin programar cada movimiento a mano.
    """

    def __init__(self, valor=0.0, rigidez=170.0, amortiguacion=15.0):
        self.x = valor
        self.v = 0.0
        self.rigidez = rigidez
        self.amortiguacion = amortiguacion

    def actualizar(self, objetivo, dt):
        # Pasos cortos para que no se vuelva inestable si un cuadro tarda de más
        pasos = int(dt / 0.006) + 1
        h = dt / pasos
        for _ in range(pasos):
            self.v += ((objetivo - self.x) * self.rigidez - self.v * self.amortiguacion) * h
            self.x += self.v * h
        return self.x
