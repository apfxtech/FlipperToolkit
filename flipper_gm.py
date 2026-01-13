#!/usr/bin/env python3
import threading
import pygame
from flipperzero_protobuf.flipper_proto import FlipperProto

WHITE = (254, 128, 25)
BLACK = (8, 8, 8)

WIDTH, HEIGHT = 128, 64
SCALE_FACTOR = 4
WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH * SCALE_FACTOR, HEIGHT * SCALE_FACTOR

def main():
    proto = FlipperProto()
    device = dict(proto.rpc_device_info())

    proto.rpc_gui_start_screen_stream()

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(
        f"Device: {device.get('hardware_name', 'Flipper zero')}, {device.get('firmware_version', 'unknown')}"
    )
    clock = pygame.time.Clock()

    frame_surface = pygame.Surface((WIDTH, HEIGHT))

    lock = threading.Lock()
    latest = {"data": None, "seq": 0}
    stop_event = threading.Event()

    def reader():
        seq = 0
        try:
            while not stop_event.is_set():
                msg = proto._rpc_read_any() 
                if not hasattr(msg, "gui_screen_frame"):
                    continue

                frame = msg.gui_screen_frame.data
                if not frame:
                    continue

                if len(frame) != WIDTH * (HEIGHT // 8):
                    continue

                seq += 1
                with lock:
                    latest["data"] = frame
                    latest["seq"] = seq

        except Exception as e:
            stop_event.set()
            print(f"Reader stopped: {e}")

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    black_map = frame_surface.map_rgb(BLACK)
    white_map = frame_surface.map_rgb(WHITE)

    last_seq = 0
    running = True
    try:
        while running and not stop_event.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            with lock:
                frame_data = latest["data"]
                seq = latest["seq"]

            if frame_data is not None and seq != last_seq:
                last_seq = seq

                px = pygame.PixelArray(frame_surface)

                for page in range(HEIGHT // 8): 
                    base = page * WIDTH
                    y0 = page * 8
                    for x in range(WIDTH):
                        b = frame_data[base + x]

                        px[x, y0 + 0] = black_map if (b & 0x01) else white_map
                        px[x, y0 + 1] = black_map if (b & 0x02) else white_map
                        px[x, y0 + 2] = black_map if (b & 0x04) else white_map
                        px[x, y0 + 3] = black_map if (b & 0x08) else white_map
                        px[x, y0 + 4] = black_map if (b & 0x10) else white_map
                        px[x, y0 + 5] = black_map if (b & 0x20) else white_map
                        px[x, y0 + 6] = black_map if (b & 0x40) else white_map
                        px[x, y0 + 7] = black_map if (b & 0x80) else white_map

                del px

                scaled = pygame.transform.scale(frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
                screen.blit(scaled, (0, 0))
                pygame.display.flip()

            clock.tick(60)

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        try:
            proto.rpc_gui_stop_screen_stream()
        except Exception:
            pass
        pygame.quit()


if __name__ == "__main__":
    main()
