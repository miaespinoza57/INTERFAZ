"""Recuadro para capturar las 3 letras del jugador antes de empezar la partida.

Se abre cuando el micro avisa ASK (se presionó INICIAR). Teclado: letras A-Z, Retroceso
y Enter; también se puede hacer clic en ACEPTAR. Al aceptar devuelve las 3 letras.
"""

import math

import pygame

import config as c
from dibujo import acercar, fuente, rect_redondo, suavizar, texto_borde

K = 2
LETRAS = 3
ANCHO, ALTO = 440, 300
MARGEN = 10                     # Margen de la sombra alrededor del cuerpo
CENTRO = (c.ANCHO // 2, 330)    # Centro del cuerpo del recuadro en pantalla
CASILLA = (74, 92)
SEPARACION = 16
CASILLAS_Y = 118                # Arriba de las casillas, dentro del cuerpo
BOTON = (210, 50)
BOTON_Y = 250                   # Centro del botón, dentro del cuerpo

CUERPO = pygame.Rect(CENTRO[0] - ANCHO // 2, CENTRO[1] - ALTO // 2, ANCHO, ALTO)
BOTON_PANTALLA = pygame.Rect(0, 0, *BOTON)
BOTON_PANTALLA.center = (CUERPO.centerx, CUERPO.y + BOTON_Y)

FONDO_CASILLA = (30, 16, 16)
GRIS = (96, 76, 70)


def _rect_casilla(i):
    total = LETRAS * CASILLA[0] + (LETRAS - 1) * SEPARACION
    x = (ANCHO - total) // 2 + i * (CASILLA[0] + SEPARACION)
    return pygame.Rect(x, CASILLAS_Y, *CASILLA)


class Iniciales:
    def __init__(self):
        self.letras = ""
        self._abierto = False
        self._presencia = 0.0
        self._t = 0.0
        self._temblor = 0.0
        self._base = self._crear_base()
        self._botones = {
            "listo": self._crear_boton(c.VERDE, c.CREMA),
            "encima": self._crear_boton((84, 196, 112), c.CREMA),
            "falta": self._crear_boton(GRIS, (170, 150, 140)),
        }
        self._velo = pygame.Surface((c.ANCHO, c.ALTO))
        self._velo.fill((0, 0, 0))

    @property
    def abierto(self):
        return self._abierto

    def abrir(self):
        self.letras = ""
        self._abierto = True
        self._t = 0.0

    def cerrar(self):
        self._abierto = False

    # -- Entrada --
    def tecla(self, evento):
        """Procesa una tecla. Devuelve las 3 letras si el jugador aceptó, o None."""
        if evento.key == pygame.K_BACKSPACE:
            self.letras = self.letras[:-1]
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self._aceptar()
        else:
            letra = evento.unicode.upper()
            if len(letra) == 1 and "A" <= letra <= "Z" and len(self.letras) < LETRAS:
                self.letras += letra
        return None

    def clic(self, posicion):
        if BOTON_PANTALLA.collidepoint(posicion):
            return self._aceptar()
        return None

    def _aceptar(self):
        if len(self.letras) == LETRAS:
            letras = self.letras
            self.cerrar()
            return letras
        self._temblor = 0.35     # Faltan letras: el recuadro se sacude
        return None

    # -- Dibujo --
    def _crear_base(self):
        w, h = ANCHO, ALTO
        s = pygame.Surface(((w + MARGEN * 2) * K, (h + MARGEN * 2) * K), pygame.SRCALPHA)
        cuerpo = pygame.Rect(MARGEN * K, MARGEN * K, w * K, h * K)
        sombra = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 120), cuerpo.move(4 * K, 7 * K), border_radius=18 * K)
        s.blit(sombra, (0, 0))
        rect_redondo(s, c.ROJO_OSCURO, cuerpo, 16 * K, 4 * K)
        pygame.draw.rect(s, c.ROJO, (cuerpo.x, cuerpo.y, cuerpo.w, 16 * K), border_top_left_radius=16 * K,
                         border_top_right_radius=16 * K)
        panel = cuerpo.inflate(-22 * K, -22 * K)
        pygame.draw.rect(s, (48, 24, 22), panel, border_radius=10 * K)
        pygame.draw.rect(s, c.ORO, cuerpo.inflate(-12 * K, -12 * K), 2 * K, border_radius=12 * K)
        y = (MARGEN + 76) * K
        pygame.draw.line(s, c.ORO, (panel.x + 14 * K, y), (panel.right - 14 * K, y), 2 * K)
        for i in range(LETRAS):
            r = _rect_casilla(i)
            r = pygame.Rect((r.x + MARGEN) * K, (r.y + MARGEN) * K, r.w * K, r.h * K)
            pygame.draw.rect(s, FONDO_CASILLA, r, border_radius=10 * K)
            pygame.draw.rect(s, (150, 112, 100), r, 3 * K, border_radius=10 * K)
        s = suavizar(s, K)
        titulo = texto_borde(fuente(34, True), "TUS 3 LETRAS", c.MOSTAZA)
        s.blit(titulo, titulo.get_rect(center=(MARGEN + ANCHO // 2, MARGEN + 46)))
        ayuda = fuente(18).render("Escríbelas con el teclado", True, c.CREMA)
        s.blit(ayuda, ayuda.get_rect(center=(MARGEN + ANCHO // 2, MARGEN + 100)))
        return s

    @staticmethod
    def _crear_boton(color, color_texto):
        w, h = BOTON
        s = pygame.Surface(((w + 8) * K, (h + 8) * K), pygame.SRCALPHA)
        r = pygame.Rect(4 * K, 4 * K, w * K, h * K)
        rect_redondo(s, color, r, 14 * K, 3 * K)
        pygame.draw.rect(s, (255, 255, 255, 60), (r.x + 8 * K, r.y + 4 * K, r.w - 16 * K, 8 * K),
                         border_radius=4 * K)
        s = suavizar(s, K)
        texto = texto_borde(fuente(26, True), "ACEPTAR", color_texto)
        s.blit(texto, texto.get_rect(center=(s.get_width() // 2, s.get_height() // 2)))
        return s

    def actualizar(self, dt):
        self._t += dt
        self._temblor = max(0.0, self._temblor - dt)
        self._presencia = acercar(self._presencia, 1.0 if self._abierto else 0.0, 12.0, dt)

    def dibujar(self, s):
        if self._presencia < 0.02:
            return
        avance = 1.0 if self._presencia > 0.99 else self._presencia
        self._velo.set_alpha(int(120 * avance))
        s.blit(self._velo, (0, 0))

        panel = self._base.copy()
        activa = len(self.letras)
        for i in range(LETRAS):
            r = _rect_casilla(i).move(MARGEN, MARGEN)
            if i < activa:
                letra = texto_borde(fuente(62, True), self.letras[i], c.ORO, grosor=3)
                panel.blit(letra, letra.get_rect(center=(r.centerx, r.centery - 2)))
            elif i == activa and int(self._t * 2.2) % 2 == 0:   # Cursor parpadeante
                pygame.draw.rect(panel, c.CREMA, (r.x + 14, r.bottom - 20, r.w - 28, 5), border_radius=2)
            if i == activa:
                pygame.draw.rect(panel, c.ORO, r, 3, border_radius=10)

        listo = activa == LETRAS
        encima = listo and BOTON_PANTALLA.collidepoint(pygame.mouse.get_pos())
        boton = self._botones["encima" if encima else "listo" if listo else "falta"]
        panel.blit(boton, boton.get_rect(center=(MARGEN + ANCHO // 2, MARGEN + BOTON_Y)))

        panel.set_alpha(int(255 * avance))
        sacudida = math.sin(self._temblor * 60) * 9 * (self._temblor / 0.35)
        x = CUERPO.x - MARGEN + sacudida
        y = CUERPO.y - MARGEN + (1 - avance) * 30
        s.blit(panel, (x, y))
