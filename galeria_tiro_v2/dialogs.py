"""Frases del feriante. Se eligen al azar sin repetir la anterior de cada situación."""

import random

ESPERA = "espera"
INICIO = "inicio"
BURLA = "burla"
ACIERTO = "acierto"
PRESION = "presion"
FIN_CONSOLACION = "fin_consolacion"
FIN_BUEN_PREMIO = "fin_buen_premio"
NUEVO_RECORD = "nuevo_record"

FRASES = {
    ESPERA: [
        "¡Pásele, pásele! Nadie le atina, pero el intento es gratis.",
        "¿Quién sigue?, este es bien malo",
        "¡Acérquese! Mi abuela tiraba mejor, y eso que tiraba la toalla.",
        "¡Vengan a ver! El oso gigante lleva años aquí. Ya hasta paga renta.",
        "¿Puntería? Aquí la gente llega con ella y se va sin ella.",
        "¡Pase, joven! Prometo reírme solo un poquito. Bueno, bastante.",
        "Ese trofeo dorado nunca ha salido del estante. ¡Y hoy tampoco saldrá!",
        "¡La feria más honesta del condado! Aquí se pierde sin trampas.",
    ],
    INICIO: [
        "¡Muy bien! ¿Ya encontró de qué lado sale el láser?",
        "Tranquilo, las dianas no muerden. Tampoco se dejan pegar.",
        "A ver esa puntería... si es que la trajo de casa.",
        "Corre el tiempo. Yo mientras voy preparando el premio más chiquito.",
        "¡Adelante! He visto a palomas apuntar con más seguridad.",
        "Respire hondo. No le va a ayudar, pero se ve profesional.",
        "¡Comienza el espectáculo! Y yo con asiento en primera fila.",
    ],
    BURLA: [
        "¿Le apuntaba a la diana o a la pared de atrás?",
        "Esa diana ni se enteró de que están jugando.",
        "¡Uy! Casi. Bueno, no tan casi.",
        "¿Quiere que le acerque las dianas? Cobro aparte.",
        "El láser va en línea recta. Lo digo por si ayuda.",
        "Tira mejor mi abuela jajajaj.",
        "Es tirarle a las dianas no a la pared!!!",
    ],
    ACIERTO: [
        "¡Pura suerte!",
        "¡Hasta un reloj parado acierta dos veces al día!",
        "¿Qué? ¡Esa diana estaba floja!",
        "Fue el viento. Seguro fue el viento.",
        "¡Bah! Esa era la fácil.",
        "omg",
        "¡Se me resbaló la diana, no vale!",
        "No se emocione, que no se repite.",
    ],
    PRESION: [
        "Una tortuga es más rápida jajaja",
        "¡Se acaba el tiempo! ¿Le tiemblan las manos o que rollo?",
        "¡Últimos segundos!",
        "¡Apúrele, apúrele!",
        "¡Diez segundos no alcanzan ni para disculparse!",
        "¡Corre el reloj!",
        "¡Ya casi! Ya casi se termina su sufrimiento.",
    ],
    FIN_CONSOLACION: [
        "¡Ja, ja, ja! Tenga un premio de consolación.",
        "Gracias por participar jajajaja.",
        "jajajaja sin llorar...",
        "¡Buen intento! Bueno, intento. Tome, para que no se vaya vacío.",
        "¡Ja, ja! Tenga este detallito. Lo elegí pensando en su puntería.",
        "¡Otro que cae! Le regalo esto por haberme hecho reír tanto.",
    ],
    FIN_BUEN_PREMIO: [
        "¡Ja! El récord sigue en pie, pero tenga: se ganó esto... de chiripa.",
        "Nada mal... para un principiante. Llévese esto antes de que me arrepienta.",
        "Mmm, se lo ganó, lo admito. Pero el récord ni lo despeinó. ¡Ja!",
        "¡Tenga, tenga! No presuma mucho, que el récord sigue intacto.",
        "Bonito premio, ¿eh? Disfrútelo, porque el récord no se movió.",
        "¡Ja, ja! Se lleva esto, pero yo me quedo con mi récord.",
    ],
    NUEVO_RECORD: [
        "¡No... no puede ser! ¡Mi oso! ¡Mi trofeo! Tómelos, campeón...",
        "¡Me quito el sombrero! Treinta años en la feria y nunca vi algo igual..."
    ],
}


class Selector:
    """Elige frases al azar sin repetir dos veces seguidas la misma."""

    def __init__(self):
        self._ultima = {}

    def elegir(self, situacion):
        opciones = [f for f in FRASES[situacion] if f != self._ultima.get(situacion)]
        frase = random.choice(opciones)
        self._ultima[situacion] = frase
        return frase
