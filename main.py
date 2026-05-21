# ==============================================================================
# LIBRERÍAS
# ==============================================================================
from djitellopy import Tello
import cv2, time, os, sys, signal, platform
from datetime import datetime
import numpy as np
from pupil_apriltags import Detector
from ultralytics import YOLO

# ==============================================================================
# CONFIGURACIÓN DE TECLADO POR SISTEMA OPERATIVO
# En macOS, cv2.waitKey() no detecta teclas correctamente,
# por lo que se usa pynput como alternativa.
# ==============================================================================
OS = platform.system()
USE_PYNPUT = (OS == "Darwin")
print(f"USE PYNPUT: {USE_PYNPUT}")

if USE_PYNPUT:
    from pynput import keyboard
    keys = set()

    def on_press(key):
        try:
            keys.add(key.char)
        except:
            if key == keyboard.Key.esc:
                keys.add('esc')

    def on_release(key):
        try:
            keys.discard(key.char)
        except:
            if key == keyboard.Key.esc:
                keys.discard('esc')

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()


# ==============================================================================
# INICIALIZACIÓN DEL DRON
# Conecta al Tello, muestra la batería y activa el stream de video.
# ==============================================================================
def inicializar_dron():
    tello = Tello()
    tello.connect()
    print("Battery:", tello.get_battery())

    tello.streamoff()
    tello.streamon()
    frame_read = tello.get_frame_read()
    time.sleep(2)

    return tello, frame_read


# ==============================================================================
# DIRECTORIOS DE GUARDADO
# Crea dos carpetas con timestamp: una para frames originales
# y otra para frames con las detecciones ya dibujadas.
# ==============================================================================
def crear_directorios_guardado():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join("images", timestamp)
    save_dir2 = os.path.join("images", timestamp, "processed")
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(save_dir2, exist_ok=True)
    return save_dir, save_dir2


# ==============================================================================
# ATERRIZAJE SEGURO
# Detiene el movimiento del dron, luego intenta aterrizar hasta 3 veces.
# Si todos los intentos fallan, activa el modo de emergencia.
# ==============================================================================
def safe_land(tello):
    print("LANDING...")

    for _ in range(5):
        tello.send_rc_control(0, 0, 0, 0)
        time.sleep(0.05)

    time.sleep(0.3)

    for _ in range(3):
        try:
            tello.land()
            print("LANDED OK")
            return
        except:
            time.sleep(0.5)

    print("FORCED EMERGENCY")
    tello.emergency()


# ==============================================================================
# MANEJADOR DE INTERRUPCIÓN (Ctrl+C)
# Si el usuario interrumpe el programa, aterriza el dron de forma segura
# antes de cerrar.
# ==============================================================================
def crear_handler(tello):
    def handler(sig, frame):
        safe_land(tello)
        tello.streamoff()
        tello.end()
        sys.exit(0)
    return handler


# ==============================================================================
# CARGA DE MODELOS DE IA
# Carga el modelo YOLO para detección de personas y el detector de AprilTags.
# ==============================================================================
def cargar_modelos():
    modelo_yolo = YOLO("./yolo26m.pt")
    at_detector = Detector(
        families="tag36h11",  # Familia estándar de AprilTags
        nthreads=1,
        quad_decimate=1.0     # Sin reducción de resolución
    )
    return modelo_yolo, at_detector


# ==============================================================================
# DETECCIÓN DE APRILTAGS
# Convierte el frame a escala de grises y detecta los marcadores visuales.
# Dibuja un punto y el ID de cada tag encontrado sobre el frame.
# Retorna los centros de los tags y los resultados completos.
# ==============================================================================
def detectar_apriltags(frame, at_detector):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resultados_tags = at_detector.detect(gray)
    puntos_area = []

    for r in resultados_tags:
        cx, cy = int(r.center[0]), int(r.center[1])
        puntos_area.append((cx, cy))
        cv2.circle(frame, (cx, cy), 5, (255, 0, 255), -1)
        cv2.putText(frame, f"ID:{r.tag_id}", (cx + 10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

    return puntos_area, resultados_tags


# ==============================================================================
# CONSTRUCCIÓN DE ZONA Y CÁLCULO DE ÁREA
# Con los centros de los tags detectados, construye un polígono convexo
# que define el área de monitoreo.
#
# CALIBRACIÓN DINÁMICA:
# Usa la distancia real conocida entre los tags 2 y 4 (borde superior del área)
# para calcular cuántos metros equivale cada píxel en ese instante.
# Esto permite que el área en m² sea precisa aunque el dron cambie de altura.
# ==============================================================================
def construir_zona_y_calcular_area(frame, puntos_area, resultados_tags):
    poligono_valido = None
    area_m2 = 0.0

    if len(puntos_area) >= 3:
        puntos_np = np.array(puntos_area, dtype=np.int32)
        poligono_valido = cv2.convexHull(puntos_np)

        # Dibuja el contorno del área
        cv2.polylines(frame, [poligono_valido], isClosed=True,
                      color=(255, 255, 0), thickness=2)

        # Rellena el área con amarillo semitransparente
        overlay = frame.copy()
        cv2.fillPoly(overlay, [poligono_valido], (255, 255, 0))
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

        # Distancia real medida entre los dos tags de referencia superiores
        DISTANCIA_REAL_METROS = 1.50

        tag_referencia_1 = None  # Tag 2: esquina superior izquierda
        tag_referencia_2 = None  # Tag 4: esquina superior derecha

        for r in resultados_tags:
            if r.tag_id == 2:
                tag_referencia_1 = r.center
            elif r.tag_id == 4:
                tag_referencia_2 = r.center

        if tag_referencia_1 is not None and tag_referencia_2 is not None:
            x1, y1 = tag_referencia_1
            x2, y2 = tag_referencia_2

            # Calcula la distancia en píxeles entre los dos tags de referencia
            distancia_pixeles = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

            # Dibuja la línea de referencia sobre el frame
            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)),
                     (0, 255, 255), 2)
            medio_x = int((x1 + x2) / 2)
            medio_y = int((y1 + y2) / 2)
            cv2.putText(frame,
                        f"{int(distancia_pixeles)} px = {DISTANCIA_REAL_METROS}m",
                        (medio_x - 50, medio_y - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            if distancia_pixeles > 0:
                # Factor de conversión: metros por píxel al cuadrado (para área 2D)
                metros_por_pixel = DISTANCIA_REAL_METROS / distancia_pixeles
                FACTOR_CONVERSION_DINAMICO = metros_por_pixel ** 2

                area_pixeles = cv2.contourArea(poligono_valido)
                area_m2 = area_pixeles * FACTOR_CONVERSION_DINAMICO
        else:
            cv2.putText(frame, "Waiting for reference line (Tags 2 and 4)...",
                        (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return poligono_valido, area_m2


# ==============================================================================
# DETECCIÓN DE PERSONAS
# Ejecuta el modelo YOLO sobre el frame para detectar personas (clase 0).
# Determina cuáles están dentro del polígono del área monitoreada.
# Dibuja cajas verdes para los que están dentro y rojas para los que están fuera.
# ==============================================================================
def detectar_personas(frame, modelo_yolo, poligono_valido):
    resultados_yolo = modelo_yolo.predict(frame, classes=[0], verbose=False)
    personas_en_area = 0

    for r in resultados_yolo:
        for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            x1, y1, x2, y2 = map(int, box)

            # Punto central de la caja, usado como posición de la persona
            px_pies = (x1 + x2) // 2
            py_pies = (y1 + y2) // 2

            esta_dentro = False
            if poligono_valido is not None:
                dist = cv2.pointPolygonTest(
                    poligono_valido, (px_pies, py_pies), measureDist=False
                )
                if dist >= 0:
                    esta_dentro = True

            color = (0, 255, 0) if esta_dentro else (0, 0, 255)

            if esta_dentro:
                personas_en_area += 1

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (px_pies, py_pies), 5, color, -1)

    return personas_en_area


# ==============================================================================
# PANEL DE TELEMETRÍA
# Dibuja un panel con los datos clave del vuelo sobre el frame:
# personas detectadas, área estimada, densidad, altura, batería y tiempo.
# ==============================================================================
def dibujar_panel_telemetria(frame, personas_en_area, area_m2,
                              densidad, tello, tiempo_inicial):
    cv2.rectangle(frame, (10, 10), (380, 200), (0, 0, 0), -1)

    cv2.putText(frame, f"People in area: {personas_en_area}",
                (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"Estimated area: {area_m2:.2f} m2",
                (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.putText(frame, f"Density: {densidad:.2f} people/m2",
                (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    altura_dron_m = tello.get_distance_tof() / 100.0
    cv2.putText(frame, f"Drone height: {altura_dron_m:.2f} m",
                (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 255), 2)

    bateria_dron = tello.get_battery()
    cv2.putText(frame, f"Battery: {bateria_dron} %",
                (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 255), 2)

    tiempo_actual = time.time()
    cv2.putText(frame, f"Flight time: {int(tiempo_actual - tiempo_inicial)} s",
                (20, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 255), 2)


# ==============================================================================
# LECTURA DE TECLADO
# Abstrae la lectura de teclas según el sistema operativo.
# Retorna un set con los caracteres actualmente presionados.
# ==============================================================================
def leer_teclas():
    if USE_PYNPUT:
        cv2.pollKey()
        return keys.copy()
    else:
        key = cv2.waitKey(1) & 0xFF
        pressed = set()
        if key != 255:
            pressed.add(chr(key))
        return pressed


# ==============================================================================
# LOOP PRINCIPAL
# Ejecuta el ciclo de monitoreo en tiempo real:
#   1. Lee el frame del dron
#   2. Guarda el frame original
#   3. Detecta AprilTags y construye el área
#   4. Detecta personas dentro del área
#   5. Calcula densidad y muestra telemetría
#   6. Guarda el frame procesado y lo muestra en pantalla
#   7. Aterriza si se presiona 'l' o Escape
# ==============================================================================
def loop_principal(tello, frame_read, save_dir, save_dir2,
                   modelo_yolo, at_detector):
    fps = 5
    interval = 1.0 / fps
    last_frame_time = time.time()
    frame_id = 0
    tiempo_inicial = time.time()

    while True:
        frame = frame_read.frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if frame is None:
            continue

        # Guardar frame original a la tasa de FPS configurada
        now = time.time()
        if now - last_frame_time >= interval:
            cv2.imwrite(os.path.join(save_dir, f"{frame_id:06d}.png"), frame)
            frame_id += 1
            last_frame_time = now

        # Paso 1: detectar AprilTags
        puntos_area, resultados_tags = detectar_apriltags(frame, at_detector)

        # Paso 2: construir zona y calcular área en m²
        poligono_valido, area_m2 = construir_zona_y_calcular_area(
            frame, puntos_area, resultados_tags
        )

        # Paso 3: detectar personas y contar las que están dentro del área
        personas_en_area = detectar_personas(frame, modelo_yolo, poligono_valido)

        # Paso 4: calcular densidad (evita división por cero)
        densidad = 0.0
        if area_m2 > 0.01:
            densidad = personas_en_area / area_m2

        # Paso 5: dibujar panel de telemetría sobre el frame
        dibujar_panel_telemetria(frame, personas_en_area, area_m2,
                                  densidad, tello, tiempo_inicial)

        # Paso 6: guardar frame procesado y mostrarlo en pantalla
        cv2.imwrite(os.path.join(save_dir2, f"{frame_id:06d}.png"), frame)
        cv2.imshow("Crowd Density Monitor - UOH", frame)

        # Paso 7: leer teclas y verificar si se debe aterrizar
        pressed = leer_teclas()
        if 'l' in pressed or 'esc' in pressed:
            safe_land(tello)
            break


# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    tello, frame_read = inicializar_dron()
    signal.signal(signal.SIGINT, crear_handler(tello))
    save_dir, save_dir2 = crear_directorios_guardado()
    modelo_yolo, at_detector = cargar_modelos()

    # Descomentar para vuelo real:
    # tello.takeoff()
    # time.sleep(2)

    loop_principal(tello, frame_read, save_dir, save_dir2,
                   modelo_yolo, at_detector)

    # Limpieza final
    tello.streamoff()
    tello.end()
    cv2.destroyAllWindows()
