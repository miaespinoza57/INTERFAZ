# Galería de Tiro Láser: interfaz gráfica (versión 2)

Interfaz animada para el proyecto final de Microcontroladores. Toda la lógica del juego
la hace el ATmega328P; este programa solo muestra lo que recibe por el puerto serie.

Esta carpeta es la versión mejorada. La original sigue intacta en `../galeria_tiro`
como repuesto; las dos usan el mismo protocolo y las mismas teclas.

## Qué cambió respecto a la versión 1

- **Feriante:** sombreado, manos con dedos, ojos que siguen la mirada (voltea a la diana
  que derribas), boca que se mueve según las letras del globo, y movimiento con inercia
  (bigote, sombrero y moño rebotan). Brinca y suda con cada acierto, llora al perder.
- **Gestos de espera:** se atusa el bigote, saluda con el sombrero, mira su reloj y bosteza.
- **Presión:** en los últimos segundos saca su reloj de bolsillo y lo sacude.
- **Impactos:** las dianas son físicas y no se dibujan; cada acierto marca su indicador con
  chispas, estrellas, el "+10", temblor de cámara y destello de los focos.
- **Escena:** telón de apertura, faldón del toldo que se mece, postes de caramelo,
  premios que hacen la ola, polvo en la luz y penumbra en las orillas.
- **Letrero:** marcador con cifras que ruedan y barra de tiempo.
- **Final:** cartel colgante con estrellas del premio, cuenta regresiva gigante, cañones
  de confeti y fuegos artificiales con el récord. El telón separa una partida de otra.

## Windows sin comandos

1. Instala Python 3 desde [python.org](https://www.python.org/downloads/) y marca
   **Add python.exe to PATH**.
2. Doble clic en `instalar.bat` (solo la primera vez; necesita internet).
3. Doble clic en `jugar.bat` para abrir la simulación.

Con el Arduino conectado, abre una terminal en la carpeta y ejecuta
`jugar.bat --serial --port COM6` (cambia `COM6` por el puerto del Administrador de dispositivos).

## Instalar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt          # Linux
.venv\Scripts\pip install -r requirements.txt      # Windows
```

## Ejecutar en VS Code

1. Abre esta carpeta (`galeria_tiro_v2`) en VS Code. Se necesita la extensión de Python.
2. Pulsa `F5` y elige **Galería: simulación (sin Arduino)**.

En Windows, elige el intérprete con `Ctrl+Shift+P` > *Python: Select Interpreter* >
`.venv\Scripts\python.exe`.

## Ejecutar en terminal

```bash
.venv/bin/python main.py                     # Por ahora arranca en simulación
.venv/bin/python main.py --sim               # Simulación, sin Arduino
.venv/bin/python main.py --serial            # Arduino en COM6 a 9600
.venv/bin/python main.py --serial --port /dev/ttyACM0 --baud 9600
```

Los valores por defecto están en `config.py`. Cuando el Arduino esté listo, pon
`MODO_SIMULACION = False` para que arranque con el puerto serie sin argumentos.

## Teclas

| Tecla | Acción |
|---|---|
| `S` | Inicia partida (`START,60`) y el simulador manda `T` cada segundo |
| `1` `2` `3` | Impacto en esa diana (`HIT`); se levanta sola a los 3 s (`UP`) |
| `E` | Fin con valores de prueba; cada vez entrega otro nivel (0, 1, 2) |
| `R` | Fin con nuevo récord y premio 3 |
| `F11` | Pantalla completa |
| `F3` | Muestra los cuadros por segundo |
| `Esc` | Salir |

`S`, `1`, `2`, `3`, `E` y `R` solo funcionan en simulación. Los impactos solo cuentan
durante una partida.

## Si va lenta

Pulsa `F3`. Si marca menos de 50 FPS, pon `MODO_RAPIDO = True` en `config.py`.

## Protocolo serie

Texto ASCII, un mensaje por línea terminado en `\n` (`Serial.println` también sirve).

```
READY                                    REC,<record>
START,<segundos>                         T,<segundos_restantes>
HIT,<diana 1-3>,<puntaje>                UP,<diana 1-3>
END,<puntaje>,<record>,<nuevo 0/1>,<premio 0-3>
```

Las líneas mal formadas o desconocidas se ignoran.

## Archivos

| Archivo | Contenido |
|---|---|
| `main.py` | Bucle a 60 FPS y reacción a cada mensaje |
| `serial_link.py` | Parseo, lectura serie en un hilo y simulador |
| `scene.py` | Puesto de feria, estantes, premios, foquitos y dianas |
| `barker.py` | El feriante: poses, resortes, gestos y dibujo |
| `dialogs.py` | Frases |
| `hud.py` | Letrero, indicadores, globo, cartel de resultados y confeti |
| `efectos.py` | Partículas, láser, temblor, telón, fuegos y rótulos |
| `dibujo.py` | Utilidades de dibujo compartidas |
| `config.py` | Puerto, tiempos y colores |
