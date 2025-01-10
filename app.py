import pygame
import sys
import math
from networktables import NetworkTables

# Initialize pygame
pygame.init()

# Screen dimensions
screen_width = 800
screen_height = 600

# Colors
black = (0, 0, 0)
white = (255, 255, 255)
gray = (200, 200, 200)
blue = (0, 0, 255)
highlight_color = (255, 0, 0)  # Red for highlighting

# Create the screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Coral Compass")

# Shapes positions and sizes
hexagon_center = (screen_width // 2, screen_height // 2)
hexagon_radius = 50

bottom_rects = [pygame.Rect(250 + i * 100, 500, 80, 40) for i in range(3)]
right_rects = [pygame.Rect(700, 150 + i * 100, 40, 80) for i in range(4)]

# Selected rectangle indices
selected_bottom = 0
selected_right = 0

# Xbox controller setup
pygame.joystick.init()
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
else:
    print("No controller detected!")
    sys.exit()

# Debounce variables
debounce_delay = 150  # milliseconds
last_dpad_press = {
    "left": 0,
    "right": 0,
    "up": 0,
    "down": 0
}

# NetworkTables setup
NetworkTables.initialize(server='10.6647.2')  # Replace with your team number
sd = NetworkTables.getTable("Coral")

# Variable to store the currently highlighted side and position
current_highlighted_side = 3  # Initialize to the bottom side (side 3)
current_position_number = 1  # Initialize to position 1

def draw_hexagon(surface, center, radius, highlighted_side=None, position_number=-1):
    """Draw a hexagon, optionally highlighting a side and a specific position."""
    points = []
    for i in range(6):
        angle = i * math.pi / 3
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

    # Draw the hexagon sides
    for i in range(6):
        start_point = points[i]
        end_point = points[(i + 1) % 6]

        # Determine line color
        if i == highlighted_side:
            # Highlight specific position within the side
            if 1 <= position_number <= 18:
                position_within_side = (position_number - 1) % 3  # 0, 1, or 2

                # Calculate segment start and end based on position_within_side (REVERSED ORDER)
                if position_within_side == 0:
                    segment_start = [
                        start_point[0] + (end_point[0] - start_point[0]) * 2 / 3,
                        start_point[1] + (end_point[1] - start_point[1]) * 2 / 3
                    ]
                    segment_end = end_point
                elif position_within_side == 1:
                    segment_start = [
                        start_point[0] + (end_point[0] - start_point[0]) / 3,
                        start_point[1] + (end_point[1] - start_point[1]) / 3
                    ]
                    segment_end = [
                        start_point[0] + (end_point[0] - start_point[0]) * 2 / 3,
                        start_point[1] + (end_point[1] - start_point[1]) * 2 / 3
                    ]
                else:  # position_within_side == 2
                    segment_start = start_point
                    segment_end = [
                        start_point[0] + (end_point[0] - start_point[0]) / 3,
                        start_point[1] + (end_point[1] - start_point[1]) / 3
                    ]
                

                pygame.draw.line(surface, highlight_color, segment_start, segment_end, 6)  # Highlight segment

                # Draw the rest of the side in gray
                if position_within_side != 2:
                    pygame.draw.line(surface, gray, start_point, segment_start, 3)  # Draw start of side
                if position_within_side != 0:
                    pygame.draw.line(surface, gray, segment_end, end_point, 3)  # Draw end of side

            else:
                pygame.draw.line(surface, highlight_color, start_point, end_point, 3)  # Highlight entire side

        else:
            line_color = gray  # Normal side
            pygame.draw.line(surface, line_color, start_point, end_point, 3)

def calculate_position_number(hexagon_side, selected_bottom, selected_right):
    """
    Calculates the position number (1-18) based on the highlighted hexagon side and selected rectangle.
    Numbers start from the bottom side (1, 2, 3) and go COUNTERCLOCKWISE around the hexagon.
    """

    if hexagon_side is None:
        hexagon_side = 3  # Default to the bottom side

    # Adjust hexagon_side for counterclockwise numbering, starting from the bottom
    adjusted_hexagon_side = (3 - hexagon_side) % 6

    # Rotate the numbers by four sides counterclockwise to align 1, 2, 3 with the bottom
    rotated_hexagon_side = (adjusted_hexagon_side + 4) % 6

    # Calculate position number
    position_number = rotated_hexagon_side * 3 + selected_bottom + 1

    return position_number

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get joystick input
    if joystick:
        hat = joystick.get_hat(0)  # DPAD state
        current_time = pygame.time.get_ticks()

        # DPAD right or left
        if hat[0] == 1 and current_time - last_dpad_press["right"] > debounce_delay:
            selected_bottom = (selected_bottom + 1) % len(bottom_rects)
            last_dpad_press["right"] = current_time
            current_position_number = calculate_position_number(current_highlighted_side, selected_bottom, selected_right)
        elif hat[0] == -1 and current_time - last_dpad_press["left"] > debounce_delay:
            selected_bottom = (selected_bottom - 1) % len(bottom_rects)
            last_dpad_press["left"] = current_time
            current_position_number = calculate_position_number(current_highlighted_side, selected_bottom, selected_right)

        # DPAD up or down
        if hat[1] == 1 and current_time - last_dpad_press["up"] > debounce_delay:
            selected_right = (selected_right - 1) % len(right_rects)
            last_dpad_press["up"] = current_time
        elif hat[1] == -1 and current_time - last_dpad_press["down"] > debounce_delay:
            selected_right = (selected_right + 1) % len(right_rects)
            last_dpad_press["down"] = current_time

        # Left Joystick
        joystick_x = joystick.get_axis(0)
        joystick_y = joystick.get_axis(1)

        # Calculate angle based on joystick position
        angle = math.atan2(joystick_y, joystick_x)
        if angle < 0:
            angle += 2 * math.pi

        # Determine highlighted hexagon side only if joystick is moved
        if abs(joystick_x) > 0.2 or abs(joystick_y) > 0.2:
            current_highlighted_side = int((angle / (math.pi / 3)) % 6)
            current_position_number = calculate_position_number(current_highlighted_side, selected_bottom, selected_right)

        # Send data to NetworkTables
        sd.putNumber('Slot', selected_bottom)
        sd.putNumber('Level', selected_right)
        sd.putNumber('Position', current_position_number)

    # Draw everything
    screen.fill(white)

    # Draw hexagon (using the stored highlighted side and position number)
    draw_hexagon(screen, hexagon_center, hexagon_radius, current_highlighted_side, current_position_number)

    # Draw bottom rectangles
    for i, rect in enumerate(bottom_rects):
        color = blue if i == selected_bottom else gray
        pygame.draw.rect(screen, color, rect)

    # Draw right rectangles
    for i, rect in enumerate(right_rects):
        color = blue if i == selected_right else gray
        pygame.draw.rect(screen, color, rect)

    # Update the display
    pygame.display.flip()

pygame.quit()
NetworkTables.shutdown()