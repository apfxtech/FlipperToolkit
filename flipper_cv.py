#!/usr/bin/env python3
import cv2
import numpy as np
import sys
import time
from flipperzero_protobuf.flipper_proto import FlipperProto

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def main(video_path=None):
    proto = FlipperProto()
    device = {}
    data = proto.rpc_device_info()
    for i in data:
        key = i[0]
        val = i[1]
        device[key] = val

    proto.rpc_gui_start_screen_stream()

    SCALE_FACTOR = 4
    WIDTH, HEIGHT = 128, 64
    WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH * SCALE_FACTOR, HEIGHT * SCALE_FACTOR

    window_title = f"Device: {device.get('hardware_name', 'Flipper zero')}, {device.get('firmware_version')}"

    frame_img = np.zeros((HEIGHT, WIDTH, 3), np.uint8)

    writer = None
    if video_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_path, fourcc, 30, (WINDOW_WIDTH, WINDOW_HEIGHT))

    running = True
    while running:
        start_time = time.time()
        try:
            data = proto._rpc_read_answer(0)
            frame_data = data.gui_screen_frame.data
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    byte_index = (y // 8) * WIDTH + x
                    bit_index = y % 8
                    pixel_value = (frame_data[byte_index] >> bit_index) & 1
                    color = BLACK if pixel_value else WHITE
                    frame_img[y, x] = color

            scaled_img = cv2.resize(frame_img, (WINDOW_WIDTH, WINDOW_HEIGHT), interpolation=cv2.INTER_NEAREST)

            cv2.imshow(window_title, scaled_img)

            if writer:
                writer.write(scaled_img)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):  # ESC or 'q' to quit
                running = False

            # Throttle to approximately 30 FPS
            elapsed = time.time() - start_time
            if elapsed < 1/30:
                time.sleep(1/30 - elapsed)

        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(f"Error: {e}")
            running = False

    proto.rpc_gui_stop_screen_stream()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(video_path)