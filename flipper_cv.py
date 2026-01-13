#!/usr/bin/env python3
import sys
import time
import threading

import cv2
import numpy as np
from flipperzero_protobuf.flipper_proto import FlipperProto

WHITE = (254, 128, 25)
BLACK = (8, 8, 8)

WIDTH, HEIGHT = 128, 64
SCALE_FACTOR = 4
WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH * SCALE_FACTOR, HEIGHT * SCALE_FACTOR

def decode_frame_to_bgr(
    frame_data: bytes,
    white=(25, 128, 254),
    black=(8, 8, 8),
) -> np.ndarray:
    """
    frame_data: 1024 bytes (128 * 64/8), формат Flipper:
      byte_index = (y//8)*WIDTH + x
      bit_index  = y%8
      bit=1 -> BLACK, bit=0 -> WHITE

    Возвращает BGR uint8 (64, 128, 3)
    """
    # (8, 128) страницы по 8 строк
    pages = np.frombuffer(frame_data, dtype=np.uint8).reshape(HEIGHT // 8, WIDTH)

    # Раскрываем биты: получаем (8, 8, 128)
    bits = np.unpackbits(pages, axis=0)          # b7..b0
    bits = bits.reshape(8, 8, WIDTH)[:, ::-1, :] # b0..b7

    mono = bits.reshape(HEIGHT, WIDTH)  # 1 = black, 0 = white

    # Подготовим выходной BGR
    bgr = np.empty((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # bit=1 -> BLACK, bit=0 -> WHITE
    bgr[mono == 1] = black
    bgr[mono == 0] = white

    return bgr

def main(video_path=None):
    proto = FlipperProto()
    device = dict(proto.rpc_device_info())

    proto.rpc_gui_start_screen_stream()

    window_title = f"Device: {device.get('hardware_name', 'Flipper zero')}, {device.get('firmware_version', 'unknown')}"
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_title, WINDOW_WIDTH, WINDOW_HEIGHT)

    # Опциональная запись видео
    writer = None
    if video_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(video_path, fourcc, 30, (WINDOW_WIDTH, WINDOW_HEIGHT))

    lock = threading.Lock()
    latest = {"data": None, "seq": 0}
    stop_event = threading.Event()

    def reader():
        """Блокирующее чтение RPC: сохраняем только самый свежий gui_screen_frame."""
        seq = 0
        try:
            while not stop_event.is_set():
                msg = proto._rpc_read_any()  # блокирует до сообщения

                if not hasattr(msg, "gui_screen_frame"):
                    continue

                frame = msg.gui_screen_frame.data
                if not frame:
                    continue

                # ожидаем ровно 1024 байта
                if len(frame) != WIDTH * (HEIGHT // 8):
                    continue

                seq += 1
                with lock:
                    latest["data"] = bytes(frame)  # зафиксировать
                    latest["seq"] = seq

        except Exception as e:
            stop_event.set()
            print(f"Reader stopped: {e}")

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    last_seq = 0
    running = True

    try:
        while running and not stop_event.is_set():
            # Берём последний кадр (не ждём)
            with lock:
                frame_data = latest["data"]
                seq = latest["seq"]

            if frame_data is not None and seq != last_seq:
                last_seq = seq

                frame_bgr = decode_frame_to_bgr(frame_data)
                scaled = cv2.resize(frame_bgr, (WINDOW_WIDTH, WINDOW_HEIGHT), interpolation=cv2.INTER_NEAREST)

                cv2.imshow(window_title, scaled)
                if writer:
                    writer.write(scaled)

            # 1 мс достаточно для обработки событий окна
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):  # ESC или q
                running = False

            # Небольшой сон, чтобы не жечь CPU (стрим всё равно приходит асинхронно)
            time.sleep(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        try:
            proto.rpc_gui_stop_screen_stream()
        except Exception:
            pass
        if writer:
            writer.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(video_path)
