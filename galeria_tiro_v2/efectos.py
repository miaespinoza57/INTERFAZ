"""Efectos: partículas, sacudida de cámara, telón, fuegos artificiales y rótulos."""

import math
import random

import pygame

import config as c
from dibujo import (acercar, brillo, degradado, estrella, fuente, limitar, poligono,
                    rebote_salida, suave, texto_borde)


class _Particula:
    __slots__ = ("x", "y", "vx", "vy", "t", "vida", "tam", "color", "giro", "vel_giro",
                 "gravedad", "forma", "freno")


class Particulas:
    """Sistema de partículas compartido por la escena, el feriante y los fuegos."""

    def __init__(self):
        self._lista = []

    def emitir(self, x, y, cantidad=10, colores=((255, 255, 255),), velocidad=(80, 260),
               vida=(0.4, 0.9), tam=(4, 9), gravedad=700.0, forma="rect",
               angulo=(0.0, math.tau), freno=0.0):
        for _ in range(cantidad):
            p = _Particula()
            a = random.uniform(*angulo)
            v = random.uniform(*velocidad)
            p.x, p.y = x, y
            p.vx, p.vy = math.cos(a) * v, math.sin(a) * v
            p.t = 0.0
            p.vida = random.uniform(*vida)
            p.tam = random.uniform(*tam)
            p.color = random.choice(colores)
            p.giro = random.uniform(0, math.tau)
            p.vel_giro = random.uniform(-9, 9)
            p.gravedad = gravedad
            p.forma = forma
            p.freno = freno
            self._lista.append(p)

    def limpiar(self):
        self._lista.clear()

    def actualizar(self, dt):
        for p in self._lista:
            p.t += dt
            p.vy += p.gravedad * dt
            if p.freno:
                p.vx = acercar(p.vx, 0.0, p.freno, dt)
                p.vy = acercar(p.vy, 0.0, p.freno, dt)
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.giro += p.vel_giro * dt
        self._lista = [p for p in self._lista if p.t < p.vida]

    def dibujar(self, s):
        for p in self._lista:
            resto = 1 - p.t / p.vida
            tam = p.tam * min(1.0, resto * 2.5)     # Se encoge al final de su vida
            if tam < 1:
                continue
            if p.forma == "brillo":
                halo = brillo(max(2, int(tam) // 2 * 2), p.color, 255)
                s.blit(halo, halo.get_rect(center=(p.x, p.y)), special_flags=pygame.BLEND_RGB_ADD)
            elif p.forma == "estrella":
                poligono(s, p.color, estrella(p.x, p.y, tam, tam * 0.45, 5, p.giro), 2)
            elif p.forma == "circulo":
                pygame.draw.circle(s, p.color, (p.x, p.y), tam / 2)
            elif p.forma == "gota":
                pygame.draw.circle(s, c.TINTA, (p.x, p.y), tam / 2 + 2)
                pygame.draw.polygon(s, c.TINTA, [(p.x - tam / 2 - 1, p.y), (p.x + tam / 2 + 1, p.y),
                                                 (p.x, p.y - tam * 1.4 - 2)])
                pygame.draw.polygon(s, p.color, [(p.x - tam / 2 + 1, p.y), (p.x + tam / 2 - 1, p.y),
                                                 (p.x, p.y - tam * 1.2)])
                pygame.draw.circle(s, p.color, (p.x, p.y), tam / 2)
            else:
                cs, sn = math.cos(p.giro) * tam, math.sin(p.giro) * tam
                ancho = 0.45
                pygame.draw.polygon(s, p.color, [
                    (p.x + cs - sn * ancho, p.y + sn + cs * ancho), (p.x + cs + sn * ancho, p.y + sn - cs * ancho),
                    (p.x - cs + sn * ancho, p.y - sn - cs * ancho), (p.x - cs - sn * ancho, p.y - sn + cs * ancho)])


class Sacudida:
    """Temblor breve de cámara al impactar."""

    def __init__(self):
        self.fuerza = 0.0
        self._t = 0.0

    def golpe(self, fuerza):
        self.fuerza = max(self.fuerza, fuerza)

    def actualizar(self, dt):
        self._t += dt
        self.fuerza = acercar(self.fuerza, 0.0, 9.0, dt)

    @property
    def desplazamiento(self):
        if self.fuerza < 0.4:
            return 0, 0
        return round(math.sin(self._t * 71) * self.fuerza), round(math.cos(self._t * 53) * self.fuerza)


class Telon:
    """Telón de terciopelo: abre la función y separa una partida de la siguiente."""

    DURACION = 0.6

    def __init__(self, titulo):
        self._ancho = c.ANCHO // 2 + 36
        self._izq = self._crear_hoja()
        self._der = pygame.transform.flip(self._izq, True, False)
        self._titulo = self._crear_titulo(titulo)
        self.fase = "cerrado"       # La función empieza con el telón cerrado
        self.cierre = 1.0
        self._t = 0.0
        self._pausa = 1.3
        self._al_cerrar = None

    def _crear_hoja(self):
        s = pygame.Surface((self._ancho, c.ALTO), pygame.SRCALPHA)
        for x in range(self._ancho):
            # Pliegues: la luz sube y baja como en una tela colgada
            pliegue = 0.5 + 0.5 * math.sin(x / 21.0) * math.cos(x / 67.0 + 1.0)
            f = 0.5 + 0.5 * pliegue
            pygame.draw.line(s, (int(176 * f), int(18 * f), int(36 * f)), (x, 0), (x, c.ALTO))
        s.blit(degradado(self._ancho, 240, (0, 0, 0, 150), (0, 0, 0, 0)), (0, 0))
        s.blit(degradado(self._ancho, 120, (0, 0, 0, 0), (0, 0, 0, 110)), (0, c.ALTO - 120))
        # Orilla dorada y flecos
        pygame.draw.rect(s, c.TINTA, (self._ancho - 20, 0, 20, c.ALTO))
        pygame.draw.rect(s, c.ORO, (self._ancho - 17, 0, 12, c.ALTO))
        pygame.draw.rect(s, (255, 236, 150), (self._ancho - 15, 0, 3, c.ALTO))
        pygame.draw.rect(s, c.TINTA, (0, c.ALTO - 46, self._ancho, 26))
        pygame.draw.rect(s, c.ORO, (0, c.ALTO - 43, self._ancho, 20))
        for x in range(6, self._ancho, 12):
            pygame.draw.line(s, c.TINTA, (x, c.ALTO - 22), (x, c.ALTO - 2), 7)
            pygame.draw.line(s, c.MOSTAZA, (x, c.ALTO - 22), (x, c.ALTO - 4), 3)
        return s

    @staticmethod
    def _crear_titulo(titulo):
        lineas = [texto_borde(fuente(88, True), parte, c.ORO, grosor=5) for parte in titulo]
        ancho = max(l.get_width() for l in lineas)
        s = pygame.Surface((ancho, sum(l.get_height() for l in lineas)), pygame.SRCALPHA)
        y = 0
        for linea in lineas:
            s.blit(linea, linea.get_rect(midtop=(ancho // 2, y)))
            y += linea.get_height()
        return s

    @property
    def ocupado(self):
        return self.fase != "abierto"

    def cerrar_y_abrir(self, al_cerrar=None, pausa=0.3):
        """Cierra, avisa con al_cerrar cuando ya no se ve la escena y vuelve a abrir."""
        if self.fase == "abierto":
            self.fase = "cerrando"
            self._t = 0.0
            self._pausa = pausa
            self._al_cerrar = al_cerrar

    def actualizar(self, dt):
        if self.fase == "abierto":
            return
        self._t += dt
        if self.fase == "cerrando":
            self.cierre = suave(self._t / self.DURACION)
            if self._t >= self.DURACION:
                self.fase, self._t = "cerrado", 0.0
                if self._al_cerrar:
                    self._al_cerrar()
                    self._al_cerrar = None
        elif self.fase == "cerrado":
            self.cierre = 1.0
            if self._t >= self._pausa:
                self.fase, self._t = "abriendo", 0.0
        else:
            self.cierre = 1 - suave(self._t / (self.DURACION * 1.3))
            if self.cierre <= 0:
                self.fase = "abierto"
                self._titulo = None     # El título solo sale en la apertura de la función

    def dibujar(self, s):
        if self.fase == "abierto":
            return
        s.blit(self._izq, (-self._ancho + self._ancho * self.cierre, 0))
        s.blit(self._der, (c.ANCHO - self._ancho * self.cierre, 0))
        if self._titulo and self.fase == "cerrado":
            s.blit(self._titulo, self._titulo.get_rect(center=(c.ANCHO // 2, c.ALTO // 2 - 10)))


class Fuegos:
    """Fuegos artificiales para el nuevo récord."""

    COLORES = [(255, 90, 70), (255, 210, 70), (90, 200, 255), (130, 240, 130), (255, 130, 230)]

    def __init__(self, particulas):
        self._fx = particulas
        self.tiempo = 0.0
        self._prox = 0.0

    def lanzar(self, segundos):
        self.tiempo = segundos
        self._prox = 0.0

    def detener(self):
        self.tiempo = 0.0

    def actualizar(self, dt):
        if self.tiempo <= 0:
            return
        self.tiempo -= dt
        self._prox -= dt
        if self._prox <= 0:
            self._prox = random.uniform(0.3, 0.65)
            color = random.choice(self.COLORES)
            self._fx.emitir(random.uniform(110, 880), random.uniform(130, 330), 34,
                            (color, color, (255, 255, 255)), velocidad=(110, 310), vida=(0.7, 1.25),
                            tam=(10, 18), gravedad=170, forma="brillo", freno=2.2)


class Motas:
    """Polvo dorado flotando en la luz de los foquitos: le da aire a la escena."""

    def __init__(self, cantidad=22):
        self._motas = [[random.uniform(60, 950), random.uniform(120, 570), random.uniform(-10, 10),
                        random.uniform(-16, -5), random.uniform(0, 6.28)] for _ in range(cantidad)]
        self._sprites = [brillo(7, (255, 226, 160), fuerza) for fuerza in (50, 90, 130)]
        self._t = 0.0

    def actualizar(self, dt):
        self._t += dt
        for m in self._motas:
            m[0] += (m[2] + math.sin(self._t * 0.7 + m[4]) * 12) * dt
            m[1] += m[3] * dt
            if m[1] < 110:
                m[0], m[1] = random.uniform(60, 950), 575

    def dibujar(self, s):
        for m in self._motas:
            nivel = int(1.5 + 1.49 * math.sin(self._t * 1.9 + m[4]))
            sprite = self._sprites[nivel]
            s.blit(sprite, (m[0] - 7, m[1] - 7), special_flags=pygame.BLEND_RGB_ADD)


class Rotulo:
    """Texto grande que entra de golpe y se desvanece (¡A TIRAR!, 3, 2, 1...)."""

    def __init__(self, texto, color, centro, tamano=120, duracion=1.0):
        self.imagen = texto_borde(fuente(tamano, True), texto, color, grosor=5).copy()
        self.centro = centro
        self.duracion = duracion
        self.t = 0.0

    @property
    def vivo(self):
        return self.t < self.duracion

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, s):
        escala = 0.3 + 0.7 * rebote_salida(self.t / 0.22)
        resto = self.duracion - self.t
        if resto < 0.3:
            escala *= 1 + (0.3 - resto) * 1.2      # Al irse, crece y se desvanece
        ancho, alto = self.imagen.get_size()
        imagen = pygame.transform.smoothscale(self.imagen, (max(2, int(ancho * escala)), max(2, int(alto * escala))))
        imagen.set_alpha(int(255 * limitar(resto / 0.3)))
        s.blit(imagen, imagen.get_rect(center=self.centro))


def crear_luz():
    """Capa de iluminación: centro cálido y orillas en penumbra (se mezcla multiplicando)."""
    chica = pygame.Surface((160, 90))
    for y in range(90):
        for x in range(160):
            d = min(1.0, math.hypot((x - 72) / 100, (y - 42) / 64))
            g = d ** 2.4
            chica.set_at((x, y), (int(255 - 96 * g), int(255 - 118 * g), int(255 - 84 * g)))
    return pygame.transform.smoothscale(chica, (c.ANCHO, c.ALTO))
