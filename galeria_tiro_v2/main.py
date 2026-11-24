"""Interfaz de la galería de tiro láser.

Solo muestra lo que manda el microcontrolador: aquí no se calcula tiempo, puntaje,
récord ni premio. Ejecuta `python main.py --help` para ver las opciones.
"""

import argparse
import random

import pygame

import barker
import config as c
import dialogs
from efectos import Fuegos, Motas, Particulas, Rotulo, Sacudida, Telon, crear_luz
from hud import Hud
from iniciales import Iniciales
from scene import Escena
from serial_link import EnlaceSerie, SimuladorMicro

ESPERA = "espera"
JUGANDO = "jugando"
RESULTADOS = "resultados"

ENTREGA_SEG = 1.3            # Momento del fin de partida en que entrega el premio
CENTRO_JUEGO = (490, 300)    # Donde salen los rótulos grandes


class App:
    def __init__(self, enlace, simulacion, puerto=""):
        self.enlace = enlace
        self.simulacion = simulacion
        self.puerto = puerto
        self.pantalla = pygame.display.set_mode((c.ANCHO, c.ALTO), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(c.TITULO)
        self.reloj = pygame.time.Clock()
        self.mundo = pygame.Surface((c.ANCHO, c.ALTO))   # La escena se dibuja aquí para poder sacudirla

        self.fx = Particulas()
        self.escena = Escena(self.fx)
        self.hud = Hud()
        self.iniciales = Iniciales()    # Recuadro de las 3 letras del jugador
        self.feriante = barker.Feriante(820, 150, self.fx)
        self.frases = dialogs.Selector()
        self.telon = Telon(("GALERÍA DE", "TIRO LÁSER"))
        self.sacudida = Sacudida()
        self.motas = Motas()
        self.fuegos = Fuegos(self.fx)
        self.luz = crear_luz()
        self.rotulos = []

        self.estado = ESPERA
        self.corriendo = True
        self.prox_frase = 2.2        # Segundos para la siguiente frase espontánea
        self.pausa_acierto = 0.0
        self.en_presion = False
        self.t_resultado = 0.0
        self.duracion_resultado = c.RESULTADOS_SEG
        self.entrega_pendiente = None    # Situación de la frase de entrega
        self.saliendo = False            # El telón ya se está cerrando sobre los resultados
        self.ver_fps = False             # F3 muestra los cuadros por segundo

        self.manejadores = {
            "READY": self.al_ready, "START": self.al_start, "T": self.al_tiempo,
            "HIT": self.al_impacto, "UP": self.al_levantar, "END": self.al_fin,
            "REC": self.al_record, "TOP": self.al_top, "ASK": self.al_pedir,
            "NOM": self.al_nombres,
        }

    # -- Mensajes del micro --
    def procesar(self, mensaje):
        self.manejadores[mensaje.tipo](*mensaje.valores)

    def al_ready(self):
        """El micro se encendió o se presionó REINICIAR: a la pantalla de espera, sin importar dónde."""
        self.iniciales.cerrar()
        self.ir_a_espera()

    def al_pedir(self):
        """Se presionó INICIAR: pide las 3 letras; la partida empieza al aceptarlas."""
        if self.estado != ESPERA:
            self.ir_a_espera()
        self.hud.globo.ocultar()
        self.iniciales.abrir()

    def aceptar_iniciales(self, letras):
        self.enlace.enviar(f"N,{letras}\n")    # El micro responde con START

    def al_start(self, segundos):
        self.iniciales.cerrar()
        self.limpiar_partida()
        self.estado = JUGANDO
        self.hud.reiniciar(segundos)
        self.escena.foquitos.destello()
        self.rotulos.append(Rotulo("¡A TIRAR!", c.ORO, CENTRO_JUEGO, 110, 1.1))
        self.decir(dialogs.INICIO, barker.REPOSO)
        self.prox_frase = random.uniform(*c.BURLA_FRASE_SEG)

    def al_tiempo(self, segundos):
        if self.estado == RESULTADOS:
            return
        self.entrar_a_partida_en_curso()
        if segundos != self.hud.tiempo and 0 < segundos <= 5:
            self.rotulos.append(Rotulo(str(segundos), (255, 96, 70), CENTRO_JUEGO, 190, 0.8))
        self.hud.tiempo = segundos
        self.hud.tiempo_total = max(self.hud.tiempo_total, segundos)
        if 0 < segundos <= c.ULTIMOS_SEGUNDOS and not self.en_presion:
            self.en_presion = True
            self.prox_frase = 0.0

    def al_impacto(self, diana, puntaje):
        if self.estado == RESULTADOS:
            return
        self.entrar_a_partida_en_curso()
        punto = self.escena.punto_impacto(diana)
        self.escena.impacto(diana)
        self.sacudida.golpe(7)
        self.hud.impacto(diana, puntaje, punto)
        self.hud.foquitos.destello()
        self.feriante.fijar(barker.SORPRENDIDO, 1.4)
        self.feriante.mirar(punto, 1.4)
        if self.pausa_acierto <= 0:
            self.hud.globo.mostrar(self.frases.elegir(dialogs.ACIERTO), 2.0)
            self.pausa_acierto = c.PAUSA_ENTRE_ACIERTOS
        self.prox_frase = c.PRESION_FRASE_SEG if self.en_presion else random.uniform(*c.BURLA_FRASE_SEG)

    def al_levantar(self, diana):
        self.hud.levantar(diana)

    def al_fin(self, puntaje, record, nuevo, premio):
        self.limpiar_partida()
        self.estado = RESULTADOS
        self.t_resultado = 0.0
        es_record = nuevo == 1
        nivel = 3 if es_record else premio      # Con récord siempre se entrega el gran premio
        self.duracion_resultado = c.RESULTADOS_RECORD_SEG if es_record else c.RESULTADOS_SEG
        self.hud.globo.ocultar()
        self.hud.mostrar_resultado(puntaje, record, es_record, nivel)
        self.escena.iniciar_premio(nivel)
        self.escena.ola(nivel)
        if es_record:
            self.velocidad_foquitos(14.0)
            self.fuegos.lanzar(self.duracion_resultado - 3)
            self.sacudida.golpe(10)
            self.rotulos.append(Rotulo("¡RÉCORD!", c.ORO, (600, 330), 130, 1.3))
            self.feriante.fijar(barker.DERROTADO)
            self.entrega_pendiente = dialogs.NUEVO_RECORD
        else:
            self.rotulos.append(Rotulo("¡TIEMPO!", c.CREMA, (600, 330), 130, 1.0))
            self.feriante.fijar(barker.BURLANDOSE, ENTREGA_SEG + 1.2)
            self.entrega_pendiente = dialogs.FIN_CONSOLACION if premio < 2 else dialogs.FIN_BUEN_PREMIO

    def al_record(self, record):
        self.hud.record = record

    def al_top(self, *puntajes):
        self.hud.fijar_top(puntajes=puntajes)

    def al_nombres(self, *nombres):
        self.hud.fijar_top(nombres=nombres)

    # -- Cambios de pantalla --
    def entrar_a_partida_en_curso(self):
        """La interfaz se abrió con la partida ya empezada, o se perdió el START."""
        if self.estado == ESPERA:
            self.estado = JUGANDO
            self.escena.en_espera = False
            self.feriante.gestos = False
            self.prox_frase = random.uniform(*c.BURLA_FRASE_SEG)

    def limpiar_partida(self):
        """Deja la escena lista para lo que sigue: sin premio y sin fuegos."""
        self.en_presion = False
        self.saliendo = False
        self.entrega_pendiente = None
        self.escena.retirar_premio()
        self.escena.en_espera = False
        self.velocidad_foquitos(3.0)
        self.fuegos.detener()
        self.feriante.ofreciendo = False
        self.feriante.gestos = False

    def ir_a_espera(self):
        self.limpiar_partida()
        self.estado = ESPERA
        self.escena.en_espera = True
        self.hud.reiniciar()
        self.hud.globo.ocultar()
        self.feriante.gestos = True
        self.feriante.fijar(barker.REPOSO)
        self.prox_frase = 1.5

    def cerrar_resultados(self):
        """Lo llama el telón cuando ya tapó la escena."""
        if self.estado == RESULTADOS:
            self.ir_a_espera()

    def velocidad_foquitos(self, velocidad):
        self.escena.foquitos.velocidad = velocidad
        self.hud.foquitos.velocidad = velocidad

    def decir(self, situacion, estado, duracion=2.5, permanencia=None):
        self.hud.globo.mostrar(self.frases.elegir(situacion), permanencia)
        self.feriante.fijar(estado, duracion)

    # -- Bucle principal --
    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.iniciales.abierto:
                letras = self.iniciales.clic(evento.pos)
                if letras:
                    self.aceptar_iniciales(letras)
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.corriendo = False
                elif evento.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif evento.key == pygame.K_F3:
                    self.ver_fps = not self.ver_fps
                elif evento.key == pygame.K_TAB:
                    self.enlace.tecla("\t")             # Solo en simulación: botón REINICIAR
                elif self.iniciales.abierto:
                    letras = self.iniciales.tecla(evento)
                    if letras:
                        self.aceptar_iniciales(letras)
                elif evento.unicode:
                    self.enlace.tecla(evento.unicode)

    def actualizar(self, dt):
        self.enlace.actualizar(dt)
        for mensaje in self.enlace.leer():
            self.procesar(mensaje)

        self.pausa_acierto = max(0.0, self.pausa_acierto - dt)
        if self.estado == RESULTADOS:
            self.actualizar_resultados(dt)
        elif not self.telon.ocupado:
            self.actualizar_frases(dt)

        globo = self.hud.globo
        self.feriante.hablando = globo.escribiendo
        self.feriante.letra = globo.letra_actual
        self.feriante.actualizar(dt)
        self.escena.actualizar(dt)
        self.hud.actualizar(dt, self.estado == ESPERA)
        self.iniciales.actualizar(dt)
        self.motas.actualizar(dt)
        self.fuegos.actualizar(dt)
        self.fx.actualizar(dt)
        self.sacudida.actualizar(dt)
        self.telon.actualizar(dt)
        for rotulo in self.rotulos:
            rotulo.actualizar(dt)
        self.rotulos = [r for r in self.rotulos if r.vivo]

    def actualizar_frases(self, dt):
        """Frases espontáneas del feriante en espera y durante la partida."""
        self.prox_frase -= dt
        if self.prox_frase > 0 or self.hud.globo.escribiendo or self.iniciales.abierto:
            return
        if self.estado == ESPERA:
            estado = random.choice((barker.REPOSO, barker.REPOSO, barker.BURLANDOSE))
            self.decir(dialogs.ESPERA, estado)
            self.prox_frase = random.uniform(*c.ESPERA_FRASE_SEG)
        elif self.en_presion:
            self.decir(dialogs.PRESION, barker.APURANDO, 3.0, permanencia=1.0)
            self.prox_frase = c.PRESION_FRASE_SEG
        else:
            self.decir(dialogs.BURLA, barker.BURLANDOSE, 2.0)
            self.prox_frase = random.uniform(*c.BURLA_FRASE_SEG)

    def actualizar_resultados(self, dt):
        self.t_resultado += dt
        if self.entrega_pendiente and self.t_resultado >= ENTREGA_SEG:
            self.feriante.ofreciendo = True
            self.hud.globo.mostrar(self.frases.elegir(self.entrega_pendiente), self.duracion_resultado)
            self.entrega_pendiente = None
        if self.t_resultado >= self.duracion_resultado and not self.saliendo:
            self.saliendo = True
            self.telon.cerrar_y_abrir(self.cerrar_resultados)

    def dibujar(self):
        # 1) El mundo: escena, premio, feriante, luz y efectos
        m = self.mundo
        self.escena.dibujar(m)
        self.motas.dibujar(m)
        self.hud.dibujar_tablero(m)      # Antes del feriante: su brazo puede pasar por encima
        self.escena.dibujar_premio(m)
        self.feriante.dibujar(m)
        if not c.MODO_RAPIDO:
            m.blit(self.luz, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        self.hud.dibujar_efectos(m)
        self.fx.dibujar(m)
        for rotulo in self.rotulos:
            rotulo.dibujar(m)

        # 2) A la pantalla, con el temblor de los impactos
        s = self.pantalla
        s.blit(m, self.sacudida.desplazamiento)

        # 3) Encima, lo que no tiembla: letrero, globo, confeti y telón
        self.hud.dibujar(s, self.estado == ESPERA)
        self.hud.globo.dibujar(s, self.feriante.boca_en_pantalla)
        self.hud.confeti.dibujar(s)
        self.iniciales.dibujar(s)
        self.telon.dibujar(s)
        aviso = None if self.enlace.conectado else f"Sin conexión con {self.puerto}: reintentando..."
        if self.ver_fps:
            aviso = f"{self.reloj.get_fps():.0f} FPS" + (f"  ·  {aviso}" if aviso else "")
        self.hud.dibujar_avisos(s, aviso, None)    # Sin barra de teclas: solo el aviso de conexión

    def ejecutar(self):
        while self.corriendo:
            # Si la ventana se atora (al moverla, por ejemplo) no se salta la animación
            dt = min(self.reloj.tick(c.FPS) / 1000, 0.05)
            self.manejar_eventos()
            self.actualizar(dt)
            self.dibujar()
            pygame.display.flip()


def leer_argumentos():
    parser = argparse.ArgumentParser(description=c.TITULO)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--sim", action="store_true", help="simula el Arduino con el teclado")
    modo.add_argument("--serial", action="store_true", help="usa el puerto serie real")
    parser.add_argument("--port", "--puerto", dest="puerto", default=c.PUERTO,
                        help=f"puerto serie (por defecto {c.PUERTO})")
    parser.add_argument("--baud", "--baudios", dest="baudios", type=int, default=c.BAUDIOS,
                        help=f"velocidad (por defecto {c.BAUDIOS})")
    return parser.parse_args()


def main():
    args = leer_argumentos()
    simulacion = args.sim or (c.MODO_SIMULACION and not args.serial)
    pygame.init()
    enlace = SimuladorMicro() if simulacion else EnlaceSerie(args.puerto, args.baudios)
    try:
        App(enlace, simulacion, args.puerto).ejecutar()
    finally:
        enlace.cerrar()
        pygame.quit()


if __name__ == "__main__":
    main()