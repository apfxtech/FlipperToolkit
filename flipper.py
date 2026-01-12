#!/usr/bin/env python3
import pygame
from flipperzero_protobuf.cli_helpers import print_hex, dict2datetime
from flipperzero_protobuf.flipper_proto import FlipperProto

def main():
    proto = FlipperProto()
    proto.rpc_gui_start_screen_stream()

    # Initialize Pygame
    pygame.init()
    SCALE_FACTOR = 4
    WIDTH, HEIGHT = 128, 64
    WINDOW_WIDTH, WINDOW_HEIGHT = WIDTH * SCALE_FACTOR, HEIGHT * SCALE_FACTOR
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Flipper Zero Screen Stream")
    clock = pygame.time.Clock()

    # Create a surface for the original 128x64 image
    frame_surface = pygame.Surface((WIDTH, HEIGHT))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            data = proto._rpc_read_answer(0)
            frame_data = data.gui_screen_frame.data

            # Unpack the frame data (1024 bytes, each byte represents 8 vertical pixels)
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    byte_index = (y // 8) * WIDTH + x
                    bit_index = y % 8
                    pixel_value = (frame_data[byte_index] >> bit_index) & 1
                    color = (255, 255, 255) if pixel_value else (0, 0, 0)
                    frame_surface.set_at((x, y), color)

            # Scale the surface to 512x256
            scaled_surface = pygame.transform.scale(frame_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))

            # Blit to screen and update
            screen.blit(scaled_surface, (0, 0))
            pygame.display.flip()

            clock.tick(30)  # Limit to 30 FPS

        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(f"Error: {e}")
            running = False

    proto.rpc_gui_stop_screen_stream()
    pygame.quit()

if __name__ == '__main__':
    main()