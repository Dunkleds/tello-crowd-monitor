# Monitor de Densidad de Personas con Dron Tello

Sistema de monitoreo de densidad de personas en tiempo real usando un **dron DJI Tello**, **YOLOv8** para detección de personas y marcadores **AprilTag** para calibración dinámica del área.

Desarrollado como proyecto de visión computacional y robótica en la **Universidad de O'Higgins (UOH)**.

---

## Demo

> *Video / GIF de vuelo próximamente*

---

## ¿Cómo funciona?

El dron sobrevuela un área delimitada por marcadores **AprilTag** colocados en el suelo. El sistema:

1. Detecta los AprilTags para definir el polígono del área monitoreada
2. Usa la distancia real conocida entre dos tags de referencia para calibrar dinámicamente la conversión de píxeles a metros, a cualquier altura de vuelo
3. Ejecuta **YOLOv8** para detectar personas en cada frame
4. Cuenta cuántas personas están dentro del polígono
5. Calcula la densidad de personas (personas/m²) en tiempo real
6. Superpone toda la telemetría sobre el video en vivo y guarda cada frame

---

## Características

- Detección de personas en tiempo real con YOLOv8
- Calibración dinámica del área (funciona a cualquier altura)
- Cálculo de densidad de personas (personas/m²)
- Telemetría en pantalla: área, densidad, altura del dron, batería y tiempo de vuelo
- Guardado automático de frames (originales y procesados)
- Aterrizaje seguro con tecla o Ctrl+C
- Compatible con macOS y Linux/Windows

---

## Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Dron | DJI Tello (djitellopy) |
| Detección de personas | YOLOv8 (Ultralytics) |
| Marcadores de área | AprilTags - tag36h11 (pupil-apriltags) |
| Procesamiento de imagen | OpenCV, NumPy |
| Entrada de teclado | pynput (macOS) / OpenCV (Linux/Windows) |

---

## Estructura del proyecto

```
tello-crowd-monitor/
├── main.py               # Aplicación principal
├── requirements.txt      # Dependencias de Python
├── README.md
└── images/               # Generada automáticamente al ejecutar
    └── YYYYMMDD_HHMMSS/
        ├── 000001.png    # Frames originales
        └── processed/
            └── 000001.png  # Frames con detecciones
```

---

## Instalación y uso

### Requisitos previos

- Python 3.9+
- Dron DJI Tello
- Archivo del modelo YOLOv8 (`yolo26m.pt`) en la raíz del proyecto
- Marcadores AprilTag (familia tag36h11) — mínimo 3, idealmente 4

### Instalación

```bash
git clone https://github.com/TU_USUARIO/tello-crowd-monitor.git
cd tello-crowd-monitor
pip install -r requirements.txt
```

### Ejecución

1. Conecta tu computador a la red WiFi del Tello
2. Coloca los marcadores AprilTag en el suelo para delimitar el área
3. Asegúrate de que los tags **ID 2** e **ID 4** estén en el borde superior del área, separados exactamente **1.50 m**
4. Ejecuta:

```bash
python main.py
```

5. Presiona `l` o `Escape` para aterrizar de forma segura

> Para activar el despegue real, descomenta las líneas `tello.takeoff()` en `main.py`

---

## Configuración

| Parámetro | Ubicación | Valor por defecto | Descripción |
|---|---|---|---|
| `DISTANCIA_REAL_METROS` | `construir_zona_y_calcular_area()` | `1.50` | Distancia real entre los tags de referencia (metros) |
| `fps` | `loop_principal()` | `5` | Tasa de guardado de frames |
| IDs de tags de referencia | `construir_zona_y_calcular_area()` | `2` y `4` | IDs de los tags del borde superior |

---

## Controles

| Tecla | Acción |
|---|---|
| `l` | Aterrizaje seguro |
| `Escape` | Aterrizaje seguro |
| `Ctrl+C` | Aterrizaje de emergencia seguro |

---

## Licencia

MIT License — libre de usar y modificar con atribución.

---

## Autor

Desarrollado en la Universidad de O'Higgins (UOH)  
Visión Computacional · Robótica · Python
