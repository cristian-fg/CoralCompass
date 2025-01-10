import pygame
import sys
import math
import os
from networktables import NetworkTables

# --- Set Window Position (before pygame.init) ---
os.environ['SDL_VIDEO_WINDOW_POS'] = '0,30'  # Top-left corner

# Screen dimensions
screen_width = 600
screen_height = 600

# --- Colors (Dark Theme) ---
dark_gray = (40, 40, 40)  # Background
white = (255, 255, 255)
light_gray = (60, 60, 60)  # UI elements, non-highlighted
medium_gray = (80, 80, 80)  # Lines in hexagon
blue = (66, 133, 244)  # Highlighted UI elements
highlight_color = (238, 108, 77)  # Highlighted segments on hexagon (coral color)

# --- Joystick setup and helper functions ---
joystick = None
joystick_count = 0
controller_was_detected = False
joystick_initialized = False  # Flag to indicate if joystick is intentionally initialized

def init_joystick():
    """Initializes the joystick and clears the event queue."""
    global joystick, joystick_count, controller_was_detected, joystick_initialized
    pygame.joystick.quit()
    pygame.joystick.init()
    joystick_count = pygame.joystick.get_count()
    if joystick_count > 0:
        try:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            controller_was_detected = True
            joystick_initialized = False  # Reset flag on new detection
        except pygame.error:
            print("Error initializing joystick")
            joystick = None
            controller_was_detected = False
    else:
        joystick = None
        controller_was_detected = False
    # Clear the event queue after reinitializing
    pygame.event.clear()

def check_joystick_init_buttons():
    """Checks if the required buttons are pressed to initialize the joystick."""
    global joystick_initialized
    if joystick and not joystick_initialized:
        # Check for button combination: Pause (button 7) and A (button 0)
        if joystick.get_button(7) and joystick.get_button(0):
            joystick_initialized = True
            print("Joystick initialized by user.")

# Initialize Pygame
pygame.init()

# Create the screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Coral Compass")

# Shapes positions and sizes
hexagon_center = (screen_width // 2, screen_height // 2)
hexagon_radius = 100  # Increased hexagon radius
line_thickness = 5  # Changed Line thickness

# --- UI Element Positions (Updated for 600x600) ---
bottom_rects = [pygame.Rect(150 + i * 90, 500, 80, 40) for i in range(3)]  # Adjusted positions
right_rects = [pygame.Rect(500, 150 + i * 90, 40, 80) for i in range(4)]  # Adjusted positions
position_text_topleft = (20, 450)  # Updated position for text

# Selected rectangle indices
selected_bottom = 0
selected_right = 0

# Initialize joystick after Pygame is fully set up
init_joystick()

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

# Font for text
font = pygame.font.Font(None, 36)

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
                        start_point[0]
                        + (end_point[0] - start_point[0]) * 2
                        / 3,
                        start_point[1]
                        + (end_point[1] - start_point[1]) * 2
                        / 3,
                    ]
                    segment_end = end_point
                elif position_within_side == 1:
                    segment_start = [
                        start_point[0]
                        + (end_point[0] - start_point[0]) / 3,
                        start_point[1]
                        + (end_point[1] - start_point[1]) / 3,
                    ]
                    segment_end = [
                        start_point[0]
                        + (end_point[0] - start_point[0]) * 2
                        / 3,
                        start_point[1]
                        + (end_point[1] - start_point[1]) * 2
                        / 3,
                    ]
                else:  # position_within_side == 2
                    segment_start = start_point
                    segment_end = [
                        start_point[0]
                        + (end_point[0] - start_point[0]) / 3,
                        start_point[1]
                        + (end_point[1] - start_point[1]) / 3,
                    ]

                pygame.draw.line(
                    surface, highlight_color, segment_start, segment_end, line_thickness + 3
                )  # Highlight segment

                # Draw the rest of the side in gray
                if position_within_side != 2:
                    pygame.draw.line(
                        surface, medium_gray, start_point, segment_start, line_thickness
                    )  # Draw start of side
                if position_within_side != 0:
                    pygame.draw.line(
                        surface, medium_gray, segment_end, end_point, line_thickness
                    )  # Draw end of side

            else:
                pygame.draw.line(
                    surface, highlight_color, start_point, end_point, line_thickness
                )  # Highlight entire side

        else:
            line_color = medium_gray  # Normal side
            pygame.draw.line(surface, line_color, start_point, end_point, line_thickness)

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
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.JOYDEVICEADDED:
                # A new joystick was detected
                init_joystick()
            elif event.type == pygame.JOYDEVICEREMOVED:
                # A joystick was removed
                init_joystick()

        # Check for joystick initialization
        check_joystick_init_buttons()

        # Get joystick input only if a joystick is connected and initialized
        if joystick and joystick_initialized:
            hat = joystick.get_hat(0)  # DPAD state
            current_time = pygame.time.get_ticks()

            # DPAD right or left
            if hat[0] == 1 and current_time - last_dpad_press["right"] > debounce_delay:
                selected_bottom = (selected_bottom + 1) % len(bottom_rects)
                last_dpad_press["right"] = current_time
                current_position_number = calculate_position_number(
                    current_highlighted_side, selected_bottom, selected_right
                )
            elif hat[0] == -1 and current_time - last_dpad_press["left"] > debounce_delay:
                selected_bottom = (selected_bottom - 1) % len(bottom_rects)
                last_dpad_press["left"] = current_time
                current_position_number = calculate_position_number(
                    current_highlighted_side, selected_bottom, selected_right
                )

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
                current_position_number = calculate_position_number(
                    current_highlighted_side, selected_bottom, selected_right
                )

            # Send data to NetworkTables
            sd.putNumber("Slot", selected_bottom)
            sd.putNumber("Level", selected_right)
            sd.putNumber("Position", current_position_number)

        # Draw everything
        screen.fill(dark_gray)  # Set the background color

        # Display "No controller detected" message based on controller_was_detected
        if not controller_was_detected:
            text_surface = font.render("No controller detected", True, white)
            text_rect = text_surface.get_rect(center=(screen_width // 2, 20))
            screen.blit(text_surface, text_rect)

        # Draw hexagon (using the stored highlighted side and position number)
        draw_hexagon(
            screen,
            hexagon_center,
            hexagon_radius,
            current_highlighted_side,
            current_position_number,
        )

        # Draw bottom rectangles
        for i, rect in enumerate(bottom_rects):
            color = blue if i == selected_bottom else light_gray  # Use the new colors
            pygame.draw.rect(screen, color, rect)

        # Draw right rectangles
        for i, rect in enumerate(right_rects):
            color = blue if i == selected_right else light_gray  # Use the new colors
            pygame.draw.rect(screen, color, rect)

        # Display "Position: " and the position number
        position_text = font.render(f"Position: {current_position_number}", True, white)
        position_rect = position_text.get_rect(topleft=position_text_topleft)  # Use updated position
        screen.blit(position_text, position_rect)

        # Update the display
        pygame.display.flip()

    except pygame.error as e:
        print(f"Pygame error: {e}")
        # Handle specific Pygame errors if possible
        if "joystick" in str(e).lower():  # Check if error is related to joystick
            print("Joystick error detected. Reinitializing...")
            init_joystick()
        else:
            running = False  # For unknown errors, exit gracefully
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        running = False  # Exit gracefully on unexpected errors

pygame.quit()
NetworkTables.shutdown()