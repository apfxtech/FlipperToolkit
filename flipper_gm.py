#!/usr/bin/env python3
import pygame
from flipperzero_protobuf.flipper_proto import FlipperProto

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def main():
    proto = FlipperProto()
    device = {}
    data = proto.rpc_device_info()
    for i in data:
        key = i[0]
        val = i[1]
        device[key] = val
    
    proto.rpc_gui_start_screen_stream()

    pygame.init()
    SCALE_FACTOR = 4
    WIDTH, HEIGHT = 128, 64
    WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH * SCALE_FACTOR, HEIGHT * SCALE_FACTOR
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Device: {device.get('hardware_name', 'Flipper zero')}, {device.get('firmware_version')}")
    clock = pygame.time.Clock()

    frame_surface = pygame.Surface((WIDTH, HEIGHT))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            data = proto._rpc_read_answer(0)
            frame_data = data.gui_screen_frame.data

            for y in range(HEIGHT):
                for x in range(WIDTH):
                    byte_index = (y // 8) * WIDTH + x
                    bit_index = y % 8
                    pixel_value = (frame_data[byte_index] >> bit_index) & 1
                    color = BLACK if pixel_value else WHITE
                    frame_surface.set_at((x, y), color)

            scaled_surface = pygame.transform.scale(frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
            screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()

            clock.tick(30)

        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(f"Error: {e}")
            running = False

    proto.rpc_gui_stop_screen_stream()
    pygame.quit()

if __name__ == '__main__':
    main()