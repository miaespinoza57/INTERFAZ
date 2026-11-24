"""El feriante: personaje dibujado por código, animado con poses, resortes y gestos.

Cada estado define una pose (un diccionario de valores numéricos). La pose actual
persigue a la del estado: las partes pesadas (cabeza, mano, bigote, sombrero) lo hacen
con resortes, así que llegan con inercia y rebotan un poco, como en la animación
tradicional. Las partes fijas (torso, piernas, cráneo) se dibujan una sola vez.
"""

import math
import random

import pygame

import config as c
from dibujo import (Resorte, acercar, aclarar, bezier, capsula, circulo, contorno_cerrado,
                    degradado, desenfocar, elipse, fuente, limitar, linea_redonda,
                    oscurecer, poligono, rect_redondo, texto_borde, trazo_conico)

REPOSO = "reposo"
HABLANDO = "hablando"
BURLANDOSE = "burlandose"
SORPRENDIDO = "sorprendido"
DERROTADO = "derrotado"
APURANDO = "apurando"

K = 2                    # Dibujo al doble de tamaño para suavizar bordes
ANCHO, ALTO = 460, 572   # Lienzo del personaje (sin escalar)
CX = 290                 # Eje vertical del cuerpo dentro del lienzo
HOMBRO_FRENTE = (CX - 80, 268)
HOMBRO_ATRAS = (CX + 80, 268)
CABEZA = (CX, 158)       # Centro de la cabeza dentro del lienzo
LIENZO_CABEZA = (260, 260)
OJOS_X = (-33, 35)       # La cara mira un poco hacia las dianas

PIEL = (247, 202, 160)
PIEL_SOMBRA = (226, 168, 128)
PARPADO = (236, 184, 144)
CAMISA = (250, 246, 236)
CAMISA_SOMBRA = (212, 206, 204)
PELO = (74, 44, 30)
BIGOTE = (66, 38, 26)
PANTALON = (58, 52, 70)
PAJA = (240, 208, 122)
PAJA_SOMBRA = (204, 166, 84)

# ceja: altura; inclina: + ceño presumido, - cejas tristes; parpado: 0 abierto, 1 cerrado
POSES = {
    REPOSO: dict(boca=0.0, sonrisa=0.5, ceja=0.0, inclina=0.2, parpado=0.12, tam_ojo=1.0,
                 cabeza_rot=0.0, cabeza_dy=0.0, bigote=0.45, risa=0.0, senal=0.0, abierta=0.25,
                 sombrero=0.0, mano_x=CX - 66, mano_y=372, codo=1.0, tristeza=0.0, reloj=0.0),
    HABLANDO: dict(boca=0.0, sonrisa=0.7, ceja=0.35, inclina=0.3, parpado=0.05, tam_ojo=1.0,
                   cabeza_rot=3.0, cabeza_dy=0.0, bigote=0.6, risa=0.0, senal=0.0, abierta=1.0,
                   sombrero=0.0, mano_x=CX - 150, mano_y=312, codo=-1.0, tristeza=0.0, reloj=0.0),
    BURLANDOSE: dict(boca=0.8, sonrisa=1.0, ceja=0.5, inclina=0.5, parpado=1.0, tam_ojo=1.0,
                     cabeza_rot=-8.0, cabeza_dy=-4.0, bigote=1.0, risa=1.0, senal=1.0, abierta=0.0,
                     sombrero=0.0, mano_x=CX - 262, mano_y=250, codo=-1.0, tristeza=0.0, reloj=0.0),
    SORPRENDIDO: dict(boca=0.8, sonrisa=-0.3, ceja=1.0, inclina=-0.3, parpado=0.0, tam_ojo=1.4,
                      cabeza_rot=5.0, cabeza_dy=-12.0, bigote=0.9, risa=0.0, senal=0.0, abierta=1.0,
                      sombrero=0.0, mano_x=CX - 156, mano_y=200, codo=-1.0, tristeza=0.0, reloj=0.0),
    DERROTADO: dict(boca=0.16, sonrisa=-1.0, ceja=-0.5, inclina=-1.0, parpado=0.5, tam_ojo=1.0,
                    cabeza_rot=-9.0, cabeza_dy=16.0, bigote=-1.0, risa=0.0, senal=0.0, abierta=0.0,
                    sombrero=1.0, mano_x=CX - 36, mano_y=376, codo=1.0, tristeza=1.0, reloj=0.0),
    APURANDO: dict(boca=0.0, sonrisa=0.9, ceja=0.7, inclina=0.7, parpado=0.25, tam_ojo=1.0,
                   cabeza_rot=-5.0, cabeza_dy=0.0, bigote=0.85, risa=0.0, senal=0.0, abierta=0.0,
                   sombrero=0.0, mano_x=CX - 150, mano_y=236, codo=-1.0, tristeza=0.0, reloj=1.0),
}
CON_RESORTE = ("cabeza_rot", "cabeza_dy", "mano_x", "mano_y", "bigote")

SUBIR_MANO_SEG = 0.55    # Lo que tarda en tomar el sombrero antes de bajarlo al pecho
GESTOS = {"bigote": 1.8, "sombrero": 1.5, "reloj": 3.0}    # Gestos de reposo y su duración

_SIN_ACENTO = str.maketrans("áéíóúü", "aeiouu")
_VISEMAS = {"a": (0.8, 1.0), "e": (0.5, 1.12), "i": (0.3, 1.2), "o": (0.72, 0.62), "u": (0.42, 0.5)}


def _visema(letra):
    """Forma de la boca (apertura, ancho) para la letra que se está escribiendo."""
    letra = letra.lower().translate(_SIN_ACENTO)
    if letra in _VISEMAS:
        return _VISEMAS[letra]
    if letra and letra in "mbp":
        return 0.0, 0.9
    if letra.isalpha():
        return 0.22, 0.95
    return 0.05, 1.0


def _resolver_codo(hombro, mano, largo1, largo2, lado):
    """Cinemática inversa de dos segmentos: ubica el codo a partir de la mano.

    lado va de -1 a 1 y es continuo, para que el codo no brinque al cambiar de pose.
    """
    dx, dy = mano[0] - hombro[0], mano[1] - hombro[1]
    distancia = max(abs(largo1 - largo2) + 1, min(math.hypot(dx, dy), largo1 + largo2 - 1))
    coseno = (largo1**2 + distancia**2 - largo2**2) / (2 * largo1 * distancia)
    angulo = math.atan2(dy, dx) + lado * math.acos(max(-1, min(1, coseno)))
    return hombro[0] + math.cos(angulo) * largo1, hombro[1] + math.sin(angulo) * largo1


def _E(punto):
    return punto[0] * K, punto[1] * K


class Feriante:
    def __init__(self, x, y, particulas):
        self.x = x
        self.y = y
        self.estado = REPOSO
        self.ofreciendo = False     # Extiende el brazo para entregar el premio
        self.hablando = False       # Lo actualiza main según el globo de diálogo
        self.letra = ""             # Letra que se está escribiendo: mueve la boca
        self.gestos = True          # Gestos espontáneos en reposo (solo en la espera)
        self.pose = dict(POSES[REPOSO])
        self._fx = particulas
        self._resortes = {clave: Resorte(self.pose[clave]) for clave in CON_RESORTE}
        self._resortes["bigote"] = Resorte(self.pose["bigote"], 240.0, 11.0)
        self._puntas = [Resorte(0.0, 210.0, 9.0), Resorte(0.0, 150.0, 8.0)]   # Puntas del bigote
        self._sombrero_pos = [Resorte(CX, 320.0, 17.0), Resorte(70, 320.0, 17.0), Resorte(0.0, 200.0, 12.0)]
        self._mono_rot = Resorte(0.0, 190.0, 7.0)
        self._estira = Resorte(1.0, 230.0, 11.0)        # Estirar y encoger todo el cuerpo
        self._duracion = None       # Segundos que dura el estado actual
        self._t_estado = 0.0
        self._t = 0.0
        self._parpadeo = 0.0
        self._prox_parpadeo = 2.5
        self._boca = [0.0, 1.0]     # Apertura y ancho por el habla
        self._mirada = [0.0, 0.0]
        self._mirar_a = None
        self._t_mirar = 0.0
        self._vistazo = [0.0, 0.0]
        self._prox_vistazo = 2.0
        self._gesto = None
        self._t_gesto = 0.0
        self._prox_gesto = 5.0
        self._levanta = 0.0         # Sombrero levantado al saludar
        self._prox_ja = 0.0
        self._prox_gota = 0.0
        self._risas = []            # Los "¡JA!" que salen flotando
        self._cuadro = 0
        self._ultimo = None         # Última imagen dibujada (para el modo rápido)
        self._geo = dict(dy=0.0, cabeza=CABEZA, mano=(CX - 66, 372), mano_atras=(CX + 132, 398))

        self._lienzo = pygame.Surface((ANCHO * K, ALTO * K), pygame.SRCALPHA)
        self._piernas_img = self._crear_piernas()
        self._torso_img = self._crear_torso()
        self._cabeza_base = self._crear_cabeza()
        self._sombrero = self._crear_sombrero()
        self._mono = self._crear_mono()
        self._asombro = texto_borde(fuente(56, True), "!", c.ROJO, c.CREMA, 3)

    # -- Órdenes --
    def fijar(self, estado, duracion=None):
        """Cambia de estado; con duración, vuelve solo a reposo al terminar."""
        if estado == SORPRENDIDO:
            self._estira.v += 3.2           # Brinco: se estira hacia arriba
            cx, cy = self.cabeza_en_pantalla
            self._fx.emitir(cx, cy - 60, 5, ((150, 214, 255),), velocidad=(150, 300), vida=(0.4, 0.7),
                            tam=(6, 9), gravedad=700, forma="gota", angulo=(-2.6, -0.5))
        elif estado == DERROTADO and self.estado != DERROTADO:
            self._estira.v -= 1.5
        self._t_estado = 0.0
        self.estado = estado
        self._duracion = duracion
        self._gesto = None

    def mirar(self, punto, segundos=1.2):
        """Voltea los ojos hacia un punto de la pantalla por un momento."""
        self._mirar_a = punto
        self._t_mirar = segundos

    @property
    def boca_en_pantalla(self):
        """Punto al que apunta la cola del globo de diálogo."""
        return self.x + CX - 106, self.y + CABEZA[1] + 18

    @property
    def cabeza_en_pantalla(self):
        cx, cy = self._geo["cabeza"]
        return self.x + cx, self.y + cy

    # -- Lógica --
    def actualizar(self, dt):
        self._t += dt
        self._t_estado += dt
        if self._duracion is not None and self._t_estado >= self._duracion:
            self.fijar(REPOSO)
        self._actualizar_parpadeo(dt)

        nombre = HABLANDO if self.estado == REPOSO and self.hablando else self.estado
        objetivo = dict(POSES[nombre])
        self._levanta = acercar(self._levanta, 0.0, 9.0, dt)
        rizo = 0.0
        if nombre == DERROTADO and self._t_estado < SUBIR_MANO_SEG:
            # Primero lleva la mano al sombrero, luego lo baja al pecho
            objetivo.update(sombrero=0.0, mano_x=CX + 4, mano_y=66)
        elif nombre == HABLANDO:
            # Gesticula mientras habla
            objetivo["mano_x"] += math.sin(self._t * 3.1) * 28
            objetivo["mano_y"] += math.sin(self._t * 4.7) * 24
            objetivo["cabeza_rot"] += math.sin(self._t * 2.3) * 3
        elif nombre == APURANDO:
            objetivo["mano_y"] += math.sin(self._t * 10) * 5       # Sacude el reloj
        elif nombre == REPOSO:
            rizo = self._actualizar_gesto(objetivo, dt)
        if self.ofreciendo and nombre != DERROTADO:   # Derrotado: sombrero al pecho
            objetivo.update(mano_x=CX - 235, mano_y=330, senal=0.0, codo=-1.0, abierta=1.0)

        velocidad = 14.0 if nombre == SORPRENDIDO else 9.0
        for clave, valor in objetivo.items():
            if clave in self._resortes:
                self.pose[clave] = self._resortes[clave].actualizar(valor, dt)
            else:
                self.pose[clave] = acercar(self.pose[clave], valor, velocidad, dt)

        self._actualizar_boca(dt)
        self._actualizar_mirada(dt)

        # Las puntas del bigote siguen al ánimo con retraso y vibran al hablar o reír
        vibra = (self._boca[0] * math.sin(self._t * 19) * 9 + self.pose["risa"] * math.sin(self._t * 26) * 5)
        base = 24 - self.pose["bigote"] * 46
        self._puntas[0].actualizar(base + vibra + rizo, dt)
        self._puntas[1].actualizar(base - vibra * 0.8, dt)

        respira = math.sin(self._t * 2.0)
        self._estira.actualizar(1.0 + respira * 0.006 - self.pose["tristeza"] * 0.03, dt)
        self._calcular_geometria(dt, respira * 3)
        self._emitir(dt)

    def _actualizar_parpadeo(self, dt):
        self._prox_parpadeo -= dt
        if self._prox_parpadeo <= 0:
            self._parpadeo = 0.13
            # A veces parpadea dos veces seguidas
            self._prox_parpadeo = 0.3 if random.random() < 0.2 else random.uniform(2.0, 5.0)
        self._parpadeo = max(0.0, self._parpadeo - dt)

    def _actualizar_gesto(self, objetivo, dt):
        """Gestos espontáneos de reposo. Devuelve cuánto se riza la punta del bigote."""
        if self._gesto is None:
            self._prox_gesto -= dt
            if self._prox_gesto <= 0 and self.gestos and not self.ofreciendo:
                self._gesto = random.choice(list(GESTOS))
                self._t_gesto = 0.0
            return 0.0
        self._t_gesto += dt
        t = self._t_gesto
        if t >= GESTOS[self._gesto]:
            self._gesto = None
            self._prox_gesto = random.uniform(3.5, 7.0)
            return 0.0
        if self._gesto == "bigote":
            # Se atusa la punta del bigote, muy satisfecho
            a = t * 10
            objetivo.update(mano_x=CX - 104 + math.cos(a) * 7, mano_y=CABEZA[1] + 44 + math.sin(a) * 7,
                            codo=-1.0, abierta=0.0, parpado=1.0, ceja=0.6, sonrisa=1.0, cabeza_rot=7.0)
            return math.sin(a) * 9
        if self._gesto == "sombrero":
            # Saluda levantando el sombrero
            objetivo.update(mano_x=CX - 84, mano_y=74, codo=-1.0, abierta=0.0, sonrisa=1.0)
            if 0.4 < t < 1.1:
                self._levanta = acercar(self._levanta, 1.0, 40.0, dt)
                objetivo.update(mano_x=CX - 96, mano_y=44, cabeza_dy=7.0, cabeza_rot=-6.0, parpado=1.0)
            return 0.0
        # Mira su reloj de bolsillo y bosteza: no llega nadie a jugar
        objetivo.update(mano_x=CX - 128, mano_y=268, codo=-1.0, abierta=0.0, reloj=1.0, ceja=0.5,
                        cabeza_rot=-7.0, sonrisa=0.0)
        self.mirar((self.x + CX - 128, self.y + 330), 0.1)
        if 1.5 < t < 2.6:
            objetivo.update(boca=1.0, parpado=1.0, ceja=0.9, inclina=-0.6, cabeza_rot=6.0, cabeza_dy=-6.0, sonrisa=0.0)
        return 0.0

    def _actualizar_boca(self, dt):
        apertura, ancho = _visema(self.letra) if self.hablando else (0.0, 1.0)
        self._boca[0] = acercar(self._boca[0], apertura, 26.0, dt)
        self._boca[1] = acercar(self._boca[1], ancho, 26.0, dt)

    def _actualizar_mirada(self, dt):
        self._t_mirar -= dt
        self._prox_vistazo -= dt
        if self._prox_vistazo <= 0:
            # De vez en cuando echa un vistazo a las dianas o al jugador
            self._prox_vistazo = random.uniform(1.2, 3.2)
            self._vistazo = random.choice(([-0.9, 0.2], [0.0, 0.1], [0.0, 0.1], [-0.5, -0.3], [0.6, 0.0]))
        if self._t_mirar > 0 and self._mirar_a:
            cx, cy = self.cabeza_en_pantalla
            dx, dy = self._mirar_a[0] - cx, self._mirar_a[1] - cy
            largo = math.hypot(dx, dy) or 1
            meta = (dx / largo, dy / largo)
        elif self.hablando:
            meta = (0.0, 0.15)          # Al hablar mira al jugador
        else:
            meta = self._vistazo
        self._mirada[0] = acercar(self._mirada[0], meta[0] * 6.5, 16.0, dt)
        self._mirada[1] = acercar(self._mirada[1], meta[1] * 5.0, 16.0, dt)

    def _calcular_geometria(self, dt, respira):
        p = self.pose
        rebote = abs(math.sin(self._t * 13)) * -9 * p["risa"]
        temblor = (math.sin(self._t * 30) * 2.5 * max(0.0, p["tam_ojo"] - 1.05)
                   + math.sin(self._t * 9) * 1.6 * p["tristeza"])       # Susto y sollozo
        dy = respira * 0.5 + rebote + p["tristeza"] * 10
        cabeza = (CABEZA[0] + temblor, CABEZA[1] + p["cabeza_dy"] + dy)
        mano = (p["mano_x"], p["mano_y"] + dy)
        vaiven = math.sin(self._t * 1.3) * 5 + (math.sin(self._t * 6) * 8 if self.hablando else 0)
        mano_atras = (CX + 132 + vaiven, 406 + respira * 0.4 - p["tam_ojo"] * 8 + rebote * 0.6)
        self._geo = dict(dy=dy, cabeza=cabeza, mano=mano, mano_atras=mano_atras)

        # El sombrero persigue su lugar con un resorte: se retrasa y se bambolea
        rad = math.radians(p["cabeza_rot"])
        sx = cabeza[0] - math.sin(rad) * 88
        sy = cabeza[1] - math.cos(rad) * 88 - max(0.0, p["tam_ojo"] - 1.0) * 70 - self._levanta * 34
        quitado = limitar(p["sombrero"])
        sx += (mano[0] - sx) * quitado
        sy += (mano[1] - 34 - sy) * quitado
        giro = p["cabeza_rot"] + quitado * 24 + self._levanta * 16
        self._sombrero_pos[0].actualizar(sx, dt)
        self._sombrero_pos[1].actualizar(sy, dt)
        self._sombrero_pos[2].actualizar(giro, dt)
        self._mono_rot.actualizar(p["cabeza_rot"] * 0.5 + rebote * 0.8, dt)

    def _emitir(self, dt):
        """Risas flotantes y lágrimas."""
        cx, cy = self.cabeza_en_pantalla
        if self.pose["risa"] > 0.6:
            self._prox_ja -= dt
            if self._prox_ja <= 0:
                self._prox_ja = 0.24
                imagen = texto_borde(fuente(random.choice((26, 32, 38)), True), "¡JA!", c.MOSTAZA).copy()
                self._risas.append([cx - 20 + random.uniform(-70, 60), cy - 110, random.uniform(-70, 30),
                                    random.uniform(-150, -90), 0.0, imagen])
        for risa in self._risas:
            risa[0] += risa[2] * dt
            risa[1] += risa[3] * dt
            risa[4] += dt
        self._risas = [r for r in self._risas if r[4] < 0.9]

        if self.estado == DERROTADO and self._t_estado > 1.0:
            self._prox_gota -= dt
            if self._prox_gota <= 0:
                self._prox_gota = 0.2
                lado = random.choice(OJOS_X)
                self._fx.emitir(cx + lado, cy - 6, 1, ((130, 200, 255),), velocidad=(20, 70), vida=(0.7, 1.0),
                                tam=(6, 9), gravedad=620, forma="gota", angulo=(0.9, 2.2))

    # -- Piezas fijas (se dibujan una sola vez) --
    @staticmethod
    def _crear_piernas():
        s = pygame.Surface((ANCHO * K, 140 * K), pygame.SRCALPHA)
        for x in (CX - 88, CX + 6):
            rect_redondo(s, PANTALON, (x * K, 4 * K, 82 * K, 170 * K), 6 * K, 4 * K)
            for franja in range(x + 12, x + 76, 14):
                pygame.draw.line(s, (88, 82, 104), (franja * K, 6 * K), (franja * K, 140 * K), K)
            pygame.draw.line(s, (40, 34, 50), ((x + 41) * K, 30 * K), ((x + 41) * K, 140 * K), 2 * K)   # Raya del pantalón
            s.blit(degradado(28 * K, 132 * K, (0, 0, 20, 0), (0, 0, 20, 110), True), ((x + 54) * K, 6 * K))
            s.blit(degradado(82 * K, 30 * K, (0, 0, 20, 130), (0, 0, 20, 0)), (x * K, 22 * K))
        return s

    @staticmethod
    def _crear_torso():
        """Camisa, chaleco a rayas, cadena y cinturón. Origen: (CX - 110, 230)."""
        s = pygame.Surface((220 * K, 240 * K), pygame.SRCALPHA)

        def P(x, y):
            return (x + 110) * K, (y - 230) * K

        # Camisa con hombros redondos
        for signo in (-1, 1):
            circulo(s, CAMISA, P(signo * 76, 274), 20 * K, 4 * K)
        poligono(s, CAMISA, [P(-92, 258), P(92, 258), P(86, 452), P(-86, 452)], 4 * K)
        # Chaleco a rayas
        for i in range(12):
            tono = (200, 40, 48) if i % 2 == 0 else (250, 214, 110)
            pygame.draw.polygon(s, tono, [P(-90 + 15 * i, 262), P(-75 + 15 * i, 262), P(-75 + 15 * i, 448), P(-90 + 15 * i, 448)])
        # Sombras: el costado, bajo la barbilla y la panza
        capa = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(capa, (50, 0, 40, 84), [P(30, 262), P(90, 262), P(90, 448), P(54, 448), P(40, 360)])
        pygame.draw.ellipse(capa, (50, 0, 40, 96), (*P(-66, 238), 132 * K, 52 * K))
        pygame.draw.ellipse(capa, (255, 255, 255, 44), (*P(-82, 300), 54 * K, 120 * K))
        s.blit(capa, (0, 0))
        # Abertura en V con la pechera, y cuello de la camisa
        poligono(s, CAMISA, [P(-40, 256), P(40, 256), P(0, 372)], 4 * K)
        pygame.draw.polygon(s, CAMISA_SOMBRA, [P(8, 262), P(34, 262), P(2, 344)])
        for y in (306, 332):
            pygame.draw.circle(s, (150, 144, 150), P(0, y), 3 * K)
        pygame.draw.line(s, c.TINTA, P(0, 372), P(0, 448), 4 * K)
        pygame.draw.lines(s, c.TINTA, False, [P(-90, 258), P(-90, 450), P(90, 450), P(90, 258)], 5 * K)
        for signo in (-1, 1):
            poligono(s, CAMISA, [P(signo * 6, 262), P(signo * 40, 244), P(signo * 44, 276)], 3 * K)
        # Bolsillo, cadena del reloj y botones dorados
        pygame.draw.line(s, c.TINTA, P(36, 388), P(74, 384), 3 * K)
        cadena = bezier(P(-10, 398), P(6, 430), P(36, 428), P(54, 388), 12)
        linea_redonda(s, c.TINTA, cadena, 6 * K)
        linea_redonda(s, c.ORO, cadena, 3 * K)
        for y in (394, 424):
            circulo(s, oscurecer(c.ORO), P(-12, y), 6 * K, 2 * K)
            pygame.draw.circle(s, (255, 240, 160), P(-13, y - 1), 3 * K)
        # Cinturón con hebilla
        rect_redondo(s, (70, 40, 30), (*P(-88, 446), 176 * K, 16 * K), 2 * K, 3 * K)
        rect_redondo(s, c.ORO, (*P(-13, 443), 26 * K, 22 * K), 3 * K, 3 * K)
        pygame.draw.rect(s, (70, 40, 30), (*P(-6, 449), 12 * K, 10 * K))
        return s

    @staticmethod
    def _crear_mono():
        """Moño de lunares; se bambolea con un resorte."""
        s = pygame.Surface((116 * K, 70 * K), pygame.SRCALPHA)
        cx, cy = 58 * K, 35 * K
        for signo in (-1, 1):
            ala = [(cx, cy), (cx + signo * 48 * K, cy - 24 * K), (cx + signo * 50 * K, cy + 24 * K)]
            poligono(s, c.ROJO, ala, 4 * K)
            pygame.draw.polygon(s, c.ROJO_OSCURO, [(cx, cy), (cx + signo * 46 * K, cy + 6 * K), (cx + signo * 48 * K, cy + 21 * K)])
            for dx, dy in ((30, -8), (38, 6), (22, 4)):
                pygame.draw.circle(s, c.CREMA, (cx + signo * dx * K, cy + dy * K), 3 * K)
        circulo(s, c.ROJO_OSCURO, (cx, cy), 11 * K, 3 * K)
        pygame.draw.circle(s, c.ROJO, (cx - 2 * K, cy - 2 * K), 7 * K)
        return s

    @staticmethod
    def _crear_cabeza():
        """Orejas, cráneo calvo con sus mechones y chapas."""
        s = pygame.Surface((LIENZO_CABEZA[0] * K, LIENZO_CABEZA[1] * K), pygame.SRCALPHA)
        cx, cy = LIENZO_CABEZA[0] // 2, LIENZO_CABEZA[1] // 2

        def P(x, y):
            return (cx + x) * K, (cy + y) * K

        def R(x, y, w, h):
            return (cx + x) * K, (cy + y) * K, w * K, h * K

        for x in (-100, 66):
            elipse(s, PIEL, R(x, -14, 34, 52), 4 * K)
            pygame.draw.ellipse(s, PIEL_SOMBRA, R(x + 9, -3, 16, 30))
        elipse(s, PIEL_SOMBRA, R(-84, -94, 168, 192), 5 * K)
        pygame.draw.ellipse(s, PIEL, R(-84, -94, 154, 184))
        # Mechones a los lados y tres pelos peinados sobre la calva
        for signo in (-1, 1):
            poligono(s, PELO, [P(signo * 85, -38), P(signo * 100, -54), P(signo * 92, -34), P(signo * 106, -30),
                               P(signo * 90, -18), P(signo * 80, 26), P(signo * 62, 18), P(signo * 60, -44)], 3 * K)
        for i in range(3):
            pelo = bezier(P(-40 + i * 16, -92), P(-20 + i * 16, -112), P(20 + i * 14, -108), P(34 + i * 12, -84 + i * 3), 10)
            linea_redonda(s, PELO, pelo, 3 * K)
        # Brillo de la calva y chapas difuminadas
        capa = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(capa, (255, 255, 255, 120), R(-56, -84, 62, 24))
        pygame.draw.ellipse(capa, (240, 96, 96, 130), R(-72, 10, 44, 28))
        pygame.draw.ellipse(capa, (240, 96, 96, 130), R(26, 10, 44, 28))
        s.blit(desenfocar(capa, 8), (0, 0))
        return s

    @staticmethod
    def _crear_sombrero():
        """Canotier de paja con su listón."""
        s = pygame.Surface((230 * K, 110 * K), pygame.SRCALPHA)

        def R(x, y, w, h):
            return x * K, y * K, w * K, h * K

        # Ala
        elipse(s, PAJA_SOMBRA, R(8, 62, 214, 40), 4 * K)
        pygame.draw.ellipse(s, PAJA, R(12, 60, 206, 34))
        for r in range(1, 4):
            pygame.draw.ellipse(s, PAJA_SOMBRA, R(12 + r * 12, 62 + r * 3, 206 - r * 24, 32 - r * 7), 2 * K)
        # Copa con tejido de paja
        pygame.draw.rect(s, c.TINTA, R(46, 22, 138, 58))
        pygame.draw.rect(s, PAJA, R(50, 24, 130, 54))
        for x in range(56, 180, 9):
            pygame.draw.line(s, PAJA_SOMBRA, (x * K, 26 * K), ((x - 5) * K, 50 * K), K)
        s.blit(degradado(40 * K, 54 * K, (120, 70, 0, 0), (120, 70, 0, 96), True), (140 * K, 24 * K))
        # Listón rojo con franja azul
        pygame.draw.rect(s, c.ROJO_OSCURO, R(50, 50, 130, 26))
        pygame.draw.rect(s, c.ROJO, R(50, 50, 130, 8))
        pygame.draw.rect(s, (36, 56, 110), R(50, 60, 130, 6))
        pygame.draw.rect(s, c.TINTA, R(50, 48, 130, 3))
        pygame.draw.rect(s, c.TINTA, R(50, 75, 130, 3))
        elipse(s, PAJA, R(46, 8, 138, 30), 4 * K)
        pygame.draw.ellipse(s, (252, 228, 156), R(64, 12, 96, 17))
        pygame.draw.ellipse(s, PAJA, R(78, 15, 66, 10))
        return s

    # -- Dibujo --
    def dibujar(self, s):
        # En modo rápido el personaje se redibuja un cuadro sí y uno no
        self._cuadro += 1
        if c.MODO_RAPIDO and self._cuadro % 2 and self._ultimo:
            s.blit(*self._ultimo)
            self._dibujar_rotulos(s)
            return
        p = self.pose
        geo = self._geo
        dy = geo["dy"]
        lienzo = self._lienzo
        lienzo.fill((0, 0, 0, 0))

        lienzo.blit(self._piernas_img, (0, 436 * K))
        self._baston(lienzo, geo["mano_atras"])
        self._brazo(lienzo, HOMBRO_ATRAS, geo["mano_atras"], dy, -1.0)
        # El cuello va antes que el torso: así queda detrás de la camisa, el chaleco y el moño
        cabeza = geo["cabeza"]
        capsula(lienzo, PIEL_SOMBRA, _E((cabeza[0], cabeza[1] + 60)), _E((CX, 276 + dy)), 56 * K, 4 * K)
        lienzo.blit(self._torso_img, ((CX - 110) * K, (230 + dy) * K))
        self._dibujar_cabeza(lienzo, geo["cabeza"])
        mono = pygame.transform.rotate(self._mono, self._mono_rot.x)
        lienzo.blit(mono, mono.get_rect(center=(CX * K, (257 + dy) * K)))
        sombrero = pygame.transform.rotate(self._sombrero, self._sombrero_pos[2].x)
        lienzo.blit(sombrero, sombrero.get_rect(center=(self._sombrero_pos[0].x * K, self._sombrero_pos[1].x * K)))
        mano = geo["mano"]
        izq, arriba = CX - 128, 20.0
        codo = self._brazo(lienzo, HOMBRO_FRENTE, mano, dy, p["codo"], p["senal"], p["abierta"])
        if p["reloj"] > 0.05:
            self._dibujar_reloj(lienzo, mano, p["reloj"])
            izq = mano[0] - 80

        # Solo se reduce la parte del lienzo que se usó: es el paso más caro del cuadro
        izq = int(max(0, min(izq, mano[0] - 64, codo[0] - 30, self._sombrero_pos[0].x - 124)))
        arriba = int(max(0, min(arriba, mano[1] - 64, codo[1] - 30, self._sombrero_pos[1].x - 78)))
        usado = lienzo.subsurface((izq * K, arriba * K, (ANCHO - izq) * K, (ALTO - arriba) * K))
        # Estirar y encoger: al reducir el lienzo se deforma todo el cuerpo desde los pies
        alto = limitar(self._estira.x, 0.85, 1.2)
        ancho = 1 / math.sqrt(alto)
        imagen = pygame.transform.smoothscale(usado, (int((ANCHO - izq) * ancho), int((ALTO - arriba) * alto)))
        self._ultimo = (imagen, (self.x + CX * (1 - ancho) + izq * ancho, self.y + ALTO - imagen.get_height()))
        s.blit(*self._ultimo)
        self._dibujar_rotulos(s)

    def _dibujar_rotulos(self, s):
        for x, y, _, _, t, imagen in self._risas:
            imagen.set_alpha(int(255 * limitar((0.9 - t) * 3)))
            s.blit(imagen, imagen.get_rect(center=(x, y)))
        if self.estado == SORPRENDIDO and self._t_estado < 0.9:
            escala = 0.4 + 0.6 * limitar(self._t_estado * 9) + math.sin(self._t * 30) * 0.05
            imagen = pygame.transform.rotozoom(self._asombro, -12, escala)
            cx, cy = self.cabeza_en_pantalla
            s.blit(imagen, imagen.get_rect(center=(cx + 118, cy - 110)))

    @staticmethod
    def _baston(s, mano):
        x, y = mano
        inclinacion = (x - (CX + 132)) * 1.2
        punta = ((x - inclinacion) * K, (ALTO + 40) * K)
        tope = ((x + inclinacion * 0.3) * K, (y - 88) * K)
        capsula(s, (92, 28, 30), tope, punta, 8 * K, 3 * K)
        capsula(s, (150, 56, 50), (tope[0] - 2 * K, tope[1]), (punta[0] - 2 * K, punta[1]), 3 * K, 0)
        circulo(s, oscurecer(c.ORO), tope, 12 * K, 3 * K)
        pygame.draw.circle(s, c.ORO, (tope[0] - 2 * K, tope[1] - 2 * K), 9 * K)
        pygame.draw.circle(s, (255, 244, 180), (tope[0] - 4 * K, tope[1] - 5 * K), 3 * K)

    def _brazo(self, s, hombro, mano, dy, lado, senal=0.0, abierta=0.0):
        hombro = (hombro[0], hombro[1] + dy)
        codo = _resolver_codo(hombro, mano, 96, 96, lado)
        # Manga: base en sombra y encima la luz, corrida hacia arriba
        capsula(s, CAMISA_SOMBRA, _E(hombro), _E(codo), 40 * K, 4 * K)
        capsula(s, CAMISA_SOMBRA, _E(codo), _E(mano), 34 * K, 4 * K)
        capsula(s, CAMISA, _E((hombro[0] - 3, hombro[1] - 4)), _E((codo[0] - 3, codo[1] - 4)), 29 * K, 0)
        capsula(s, CAMISA, _E((codo[0] - 3, codo[1] - 4)), _E((mano[0] - 2, mano[1] - 3)), 24 * K, 0)
        # Liga de la manga con su broche
        dx, dy_b = codo[0] - hombro[0], codo[1] - hombro[1]
        largo = math.hypot(dx, dy_b) or 1
        liga = (hombro[0] + dx * 0.55, hombro[1] + dy_b * 0.55)
        nx, ny = -dy_b / largo * 21, dx / largo * 21
        capsula(s, c.ROJO, _E((liga[0] - nx, liga[1] - ny)), _E((liga[0] + nx, liga[1] + ny)), 7 * K, 3 * K)
        circulo(s, c.ORO, _E(liga), 4 * K, 2 * K)

        # Mano: los dedos se estiran según el gesto (puño, palma abierta o señalando)
        ux, uy = mano[0] - codo[0], mano[1] - codo[1]
        largo = math.hypot(ux, uy) or 1
        ux, uy = ux / largo, uy / largo
        vx, vy = -uy, ux
        dedos = []
        for i, lateral in enumerate((10, 3.5, -3.5, -10)):
            largo_dedo = 5 + 36 * max(senal, abierta * 0.7) if i == 0 else (5 + 24 * abierta) * (1 - 0.08 * i)
            giro = lateral / 10 * 0.3 * abierta
            dxn = ux * math.cos(giro) - uy * math.sin(giro)
            dyn = ux * math.sin(giro) + uy * math.cos(giro)
            base = (mano[0] + vx * lateral + ux * 9, mano[1] + vy * lateral + uy * 9)
            dedos.append((base, (base[0] + dxn * largo_dedo, base[1] + dyn * largo_dedo), 9.5))
        pulgar = (mano[0] + ux * (7 + 7 * abierta) + vx * (17 + 8 * abierta),
                  mano[1] + uy * (7 + 7 * abierta) + vy * (17 + 8 * abierta))
        dedos.append(((mano[0] + vx * 8, mano[1] + vy * 8), pulgar, 10.5))
        for borde in (3 * K, 0):        # Primero todos los contornos, luego los rellenos
            for base, punta, grosor in dedos:
                capsula(s, PIEL, _E(base), _E(punta), grosor * K, borde)
            circulo(s, PIEL, _E(mano), 18 * K, borde + (K if borde else 0))
        pygame.draw.circle(s, PIEL_SOMBRA, _E((mano[0] + 3, mano[1] + 4)), 9 * K)
        pygame.draw.circle(s, PIEL, _E((mano[0] + 1, mano[1] + 1)), 9 * K)
        # Puño de la camisa con mancuernilla
        puno_a = (mano[0] - ux * 22 - vx * 15, mano[1] - uy * 22 - vy * 15)
        puno_b = (mano[0] - ux * 22 + vx * 15, mano[1] - uy * 22 + vy * 15)
        capsula(s, CAMISA, _E(puno_a), _E(puno_b), 10 * K, 3 * K)
        pygame.draw.circle(s, c.ORO, _E((mano[0] - ux * 22, mano[1] - uy * 22)), 3 * K)
        return codo

    def _dibujar_reloj(self, s, mano, visible):
        """Reloj de bolsillo colgando de la mano, con su tic-tac."""
        angulo = math.sin(self._t * 5.5) * 0.45
        largo = 50 * visible
        centro = (mano[0] + math.sin(angulo) * largo, mano[1] + 8 + math.cos(angulo) * largo)
        linea_redonda(s, c.TINTA, [_E((mano[0], mano[1] + 8)), _E(centro)], 5 * K)
        linea_redonda(s, c.ORO, [_E((mano[0], mano[1] + 8)), _E(centro)], 2 * K)
        radio = 21 * visible
        circulo(s, oscurecer(c.ORO), _E((centro[0], centro[1] - radio)), 5 * K, 2 * K)
        circulo(s, oscurecer(c.ORO), _E(centro), radio * K, 3 * K)
        pygame.draw.circle(s, c.ORO, _E((centro[0] - 1, centro[1] - 1)), (radio - 2) * K)
        pygame.draw.circle(s, c.CREMA, _E(centro), (radio - 5) * K)
        for a, alcance, grosor in ((self._t * 7, 0.62, 3), (self._t * 0.9, 0.42, 4)):
            pygame.draw.line(s, c.TINTA, _E(centro), _E((centro[0] + math.sin(a) * radio * alcance,
                                                         centro[1] - math.cos(a) * radio * alcance)), grosor * K // 2 + 1)
        pygame.draw.circle(s, c.ROJO, _E(centro), 2 * K)

    def _dibujar_cabeza(self, s, centro):
        cabeza = self._cabeza_base.copy()
        cx, cy = LIENZO_CABEZA[0] // 2, LIENZO_CABEZA[1] // 2

        def P(x, y):
            return (cx + x) * K, (cy + y) * K

        self._dibujar_boca(cabeza, P)
        self._dibujar_ojos(cabeza, P)
        self._dibujar_cejas(cabeza, P)
        # Nariz
        elipse(cabeza, (226, 140, 116), (*P(-30, -8), 44 * K, 44 * K), 4 * K)
        pygame.draw.ellipse(cabeza, (244, 166, 136), (*P(-30, -8), 39 * K, 39 * K))
        pygame.draw.ellipse(cabeza, (255, 220, 200), (*P(-23, -2), 14 * K, 10 * K))
        self._dibujar_bigote(cabeza, P)
        rotada = pygame.transform.rotate(cabeza, self.pose["cabeza_rot"])
        s.blit(rotada, rotada.get_rect(center=(centro[0] * K, centro[1] * K)))

    def _dibujar_boca(self, s, P):
        p = self.pose
        abierta = limitar(max(p["boca"], self._boca[0]))
        cx, cy = -8, 54
        if abierta <= 0.06:
            curva = p["sonrisa"] * 12
            linea_redonda(s, c.TINTA, bezier(P(cx - 26, 60), P(cx - 12, 60 + curva), P(cx + 12, 60 + curva),
                                             P(cx + 26, 60), 10), 4 * K)
            return
        ancho = (46 + p["risa"] * 28) * (self._boca[1] if p["boca"] < 0.3 else 1.0)
        alto = 8 + abierta * 42
        esquina = cy + 4 - p["sonrisa"] * 6        # Las comisuras suben con la sonrisa
        izq, der = (cx - ancho / 2, esquina), (cx + ancho / 2, esquina)
        arriba = bezier(P(*izq), P(cx - ancho * 0.25, cy - 2), P(cx + ancho * 0.25, cy - 2), P(*der), 10)
        abajo = bezier(P(*der), P(cx + ancho * 0.42, cy + alto * 1.25), P(cx - ancho * 0.42, cy + alto * 1.25), P(*izq), 12)
        contorno = arriba + abajo[1:-1]
        pygame.draw.polygon(s, (104, 18, 36), contorno)
        pygame.draw.ellipse(s, (232, 96, 110), (*P(cx - ancho * 0.25, cy + alto * 0.5), ancho * 0.5 * K, alto * 0.42 * K))
        if alto > 20:
            dientes = arriba[2:-2] + [(x, y + 7 * K) for x, y in reversed(arriba[2:-2])]
            pygame.draw.polygon(s, (255, 255, 248), dientes)
        contorno_cerrado(s, contorno, 4 * K)

    def _dibujar_ojos(self, s, P):
        p = self.pose
        parpadea = self._parpadeo > 0
        cierre = 1.0 if parpadea else limitar(p["parpado"])
        for x in OJOS_X:
            if cierre > 0.93 and not parpadea and p["sonrisa"] > 0.2:
                # Ojos cerrados de gusto o de risa
                linea_redonda(s, c.TINTA, bezier(P(x - 15, -20), P(x - 7, -37), P(x + 7, -37), P(x + 15, -20), 8), 5 * K)
                continue
            ancho = int(28 * p["tam_ojo"] * K)
            alto = int(38 * p["tam_ojo"] * K)
            ojo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            ojo.fill((255, 255, 255))
            pygame.draw.ellipse(ojo, (212, 222, 238), (-ancho * 0.1, -alto * 0.62, ancho * 1.2, alto * 0.9))
            # Iris y pupila siguen la mirada; con el susto se encogen
            radio = 9.5 * K * (0.72 if p["tam_ojo"] > 1.2 else 1.0)
            px = ancho / 2 + (self._mirada[0] - 2) * K
            py = alto / 2 + (self._mirada[1] + 1) * K
            pygame.draw.circle(ojo, (96, 60, 36), (px, py), radio)
            pygame.draw.circle(ojo, c.TINTA, (px, py), radio * 0.6)
            pygame.draw.circle(ojo, (255, 255, 255), (px - radio * 0.35, py - radio * 0.42), radio * 0.32)
            if cierre > 0.02:
                parpado = pygame.Rect(-ancho * 0.15, alto * cierre - alto * 1.25, ancho * 1.3, alto * 1.25)
                pygame.draw.ellipse(ojo, c.TINTA, parpado.move(0, 2 * K))
                pygame.draw.ellipse(ojo, PARPADO, parpado.move(0, -K))
            mascara = pygame.Surface((ancho, alto), pygame.SRCALPHA)
            pygame.draw.ellipse(mascara, (255, 255, 255, 255), (0, 0, ancho, alto))
            ojo.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            centro = P(x, -24)
            pygame.draw.ellipse(s, c.TINTA, (centro[0] - ancho / 2 - 4 * K, centro[1] - alto / 2 - 4 * K,
                                             ancho + 8 * K, alto + 8 * K))
            s.blit(ojo, (centro[0] - ancho / 2, centro[1] - alto / 2))

    def _dibujar_cejas(self, s, P):
        p = self.pose
        y = -58 - p["ceja"] * 14 - max(0.0, p["tam_ojo"] - 1) * 22
        for x, hacia_centro in zip(OJOS_X, (1, -1)):
            interior = (x + hacia_centro * 19, y + p["inclina"] * 9)
            exterior = (x - hacia_centro * 23, y - p["inclina"] * 5 + 4)
            medio = ((interior[0] + exterior[0]) / 2, y - 6)
            curva = bezier(P(*interior), P(*medio), P(*medio), P(*exterior), 8)
            poligono(s, PELO, trazo_conico(curva, 11 * K, 5 * K), 2 * K)

    def _dibujar_bigote(self, s, P):
        """Bigote en manubrio: cada punta tiene su propio resorte."""
        vibra = self._boca[0] * math.sin(self._t * 19) * 5
        base_x = -8
        for signo, resorte in zip((-1, 1), self._puntas):
            punta = resorte.x
            curva = bezier(
                P(base_x + signo * 2, 38),
                P(base_x + signo * 40, 26 + vibra * 0.4),
                P(base_x + signo * 62, 56 + vibra * 0.5),
                P(base_x + signo * 88, punta + 30),
            ) + bezier(
                P(base_x + signo * 88, punta + 30),
                P(base_x + signo * 106, punta + 14),
                P(base_x + signo * 104, punta - 8),
                P(base_x + signo * 86, punta - 2), 8,
            )[1:]
            poligono(s, BIGOTE, trazo_conico(curva, 27 * K, 3 * K), 3 * K)
            # Brillo del bigote encerado
            luz = bezier(P(base_x + signo * 10, 33), P(base_x + signo * 36, 26 + vibra * 0.4),
                         P(base_x + signo * 54, 42 + vibra * 0.5), P(base_x + signo * 70, punta * 0.5 + 34), 8)
            pygame.draw.polygon(s, aclarar(BIGOTE, 0.28), trazo_conico(luz, 2 * K, 7 * K)[:9] + trazo_conico(luz, 2 * K, 1)[9:])
        pygame.draw.circle(s, BIGOTE, P(base_x, 40), 9 * K)
