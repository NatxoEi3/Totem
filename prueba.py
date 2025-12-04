# -*- coding: utf-8 -*-
"""
core.obsbot_patrol

Modo patrulla 100% automático (hecho por la OBSBOT / su app) + handoff a core.camera_agent.

- La OBSBOT se mueve sola (modo patrulla / tracking activado en su app).
- Este script SOLO:
    1) Lee el video de la cámara.
    2) Usa YOLO para detectar personas.
    3) Cuando alguien se acerca lo suficiente (bbox grande):
        - Libera la cámara.
        - Cierra la ventana.
        - Llama a core.camera_agent.iniciar_detector().

No se usan teclas, no se manda nada a la cámara. Todo el movimiento es del hardware.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

import cv2
from ultralytics import YOLO


# =========================
# CONFIGURACIÓN
# =========================

CAMERA_INDEX = 1         # si no toma video, prueba 1 o 2
YOLO_MODEL_PATH = "yolov8n.pt"

CONF_THRESHOLD = 0.5

# Cuando el alto del bbox es >= a este % de la altura del frame,
# consideramos que la persona "ya se acercó" = lanzar camera_agent
APPROACH_HEIGHT_RATIO = 0.35  # 35% de la altura del frame

# Para aligerar: no correr YOLO en TODOS los frames
YOLO_EVERY_N_FRAMES = 4

SHOW_FPS = True


# =========================
# INTEGRACIÓN CON camera_agent
# =========================

def lanzar_camera_agent() -> None:
    """
    Importa y lanza core.camera_agent.iniciar_detector().
    """
    try:
        from core import camera_agent
    except ImportError as e:
        print(f"[camera_agent] ERROR importando core.camera_agent: {e}")
        return

    if not hasattr(camera_agent, "iniciar_detector"):
        print("[camera_agent] No existe la función iniciar_detector() en core.camera_agent.")
        return

    print("[camera_agent] Lanzando camera_agent.iniciar_detector() ...")
    camera_agent.iniciar_detector()


# =========================
# YOLO: UTILIDADES
# =========================

def get_biggest_person_box(result, frame_shape) -> Optional[Tuple[int, int, int, int, float]]:
    """
    Devuelve el bounding box de la persona más grande (en pixeles) junto con la confianza.
    Si no hay personas, regresa None.
    """
    h, w, _ = frame_shape
    if result.boxes is None or len(result.boxes) == 0:
        return None

    best_box = None
    best_area = 0.0
    best_conf = 0.0

    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        if cls_id != 0:  # clase 0 = persona (COCO)
            continue
        if conf < CONF_THRESHOLD:
            continue

        x1, y1, x2, y2 = box.xyxy[0].tolist()
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        area = (x2 - x1) * (y2 - y1)

        if area > best_area:
            best_area = area
            best_box = (x1, y1, x2, y2)
            best_conf = conf

    if best_box is None:
        return None

    return (*best_box, best_conf)


# =========================
# LOOP PRINCIPAL
# =========================

def main() -> None:
    print(">>> Iniciando core.obsbot_patrol (patrulla hardware + handoff a camera_agent)")
    print(f">>> Cámara índice: {CAMERA_INDEX}")
    print(f">>> Modelo YOLO: {YOLO_MODEL_PATH}")

    model = YOLO(YOLO_MODEL_PATH)

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("ERROR: No se pudo abrir la cámara. Cambia CAMERA_INDEX o revisa la OBSBOT.")
        return

    last_time = time.time()
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: No se pudo leer frame de la cámara.")
                break

            frame_count += 1
            h, w, _ = frame.shape

            person_box = None
            if frame_count % YOLO_EVERY_N_FRAMES == 0:
                # YOLO más ligero con imgsz
                results = model.predict(frame, imgsz=480, verbose=False)
                result = results[0]
                person_box = get_biggest_person_box(result, frame.shape)

            if person_box is not None:
                x1, y1, x2, y2, conf = person_box
                bbox_height = y2 - y1
                ratio = bbox_height / float(h)

                # Dibujamos bbox y datos
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"Persona ({conf:.2f}, ratio={ratio:.2f})"
                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

                if ratio >= APPROACH_HEIGHT_RATIO:
                    print(f"[Handoff] Persona acercándose (ratio={ratio:.2f}) -> llamar camera_agent.")
                    cap.release()
                    cv2.destroyAllWindows()
                    lanzar_camera_agent()
                    return

            # Estado en pantalla (patrulla a nivel hardware)
            cv2.putText(
                frame,
                "Estado: PATRULLA (movimiento por hardware/camara)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # FPS
            if SHOW_FPS:
                ahora = time.time()
                elapsed = ahora - last_time
                if elapsed > 0:
                    fps = frame_count / elapsed
                    cv2.putText(
                        frame,
                        f"FPS: {fps:.1f}",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )

            cv2.imshow("OBSBOT Patrulla (hardware) + YOLO handoff", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                print(">>> Saliendo de core.obsbot_patrol (ESC/q)")
                break

    finally:
        try:
            cap.release()
        except Exception:
            pass
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()