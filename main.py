import asyncio
import random
import pygame
import sys
import math

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 80, 80)
GREEN = (80, 200, 80)
BLUE = (80, 150, 255)
YELLOW = (255, 220, 80)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (120, 120, 120)
BROWN = (101, 67, 33)
GOLD = (218, 167, 27)
LIGHT_GOLD = (245, 197, 66)
DARK_BROWN = (57, 43, 1)

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Waste Sorting Game")
clock = pygame.time.Clock()

# Fonts
title_font = pygame.font.Font(None, 48)
font = pygame.font.Font(None, 32)
smallFont = pygame.font.Font(None, 24)


class DraggableItem:
    def __init__(self, text, category, x, y, photo):
        self.text = text
        self.category = category
        self.dragging = False
        self.original_pos = (x, y)
        self.float_offset = 0
        self.float_direction = 1

        # Load and scale image
        try:
            self.photo = pygame.image.load(photo)
            self.photo = pygame.transform.scale(self.photo, (SCREEN_WIDTH // 6, SCREEN_HEIGHT // 6))
        except:
            self.photo = pygame.Surface((SCREEN_WIDTH // 6, SCREEN_HEIGHT // 6))
            self.photo.fill(GOLD)

        self.rect = pygame.Rect(x, y, SCREEN_WIDTH // 6, SCREEN_HEIGHT // 6)
        self.shadow_rect = self.rect.copy()

    def draw(self, surface):
        # Draw shadow when dragging
        if self.dragging:
            shadow_offset = 8
            shadow_rect = self.rect.copy()
            shadow_rect.x += shadow_offset
            shadow_rect.y += shadow_offset
            pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=12)

        # Draw main item with rounded corners
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=12)
        pygame.draw.rect(surface, GOLD, self.rect, 3, border_radius=12)

        # Draw image
        surface.blit(self.photo, self.rect)

        # Draw text label with background
        text_surface = smallFont.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.bottom + 12))

        # Text background
        text_bg = text_rect.inflate(10, 4)
        pygame.draw.rect(surface, WHITE, text_bg, border_radius=6)
        pygame.draw.rect(surface, GOLD, text_bg, 1, border_radius=6)
        surface.blit(text_surface, text_rect)

    def update(self):
        if self.dragging:
            self.rect.center = pygame.mouse.get_pos()
        else:
            # Gentle floating animation when not dragging
            self.float_offset += 0.1 * self.float_direction
            if abs(self.float_offset) > 3:
                self.float_direction *= -1
            self.rect.y = self.original_pos[1] + self.float_offset

    def start_drag(self):
        self.dragging = True

    def end_drag(self):
        self.dragging = False

    def reset_position(self):
        self.rect.x, self.rect.y = self.original_pos


class CategoryBox:
    def __init__(self, category, x, y, width, height):
        self.category = category
        self.rect = pygame.Rect(x, y, width, height)
        self.items_sorted = []
        self.hover = False
        self.animation_offset = 0

        # Category colors
        self.colors = {
            "Food Waste": (80, 200, 80),
            "Trash": (120, 120, 120),
            "Recycle": (80, 150, 255)
        }

    def draw(self):
        color = self.colors.get(self.category, GREEN)

        # Hover effect
        if self.hover:
            color = tuple(min(255, c + 30) for c in color)
            self.animation_offset = 5
        else:
            self.animation_offset = max(0, self.animation_offset - 0.5)

        # Draw box with rounded corners
        box_rect = self.rect.inflate(self.animation_offset, self.animation_offset)
        pygame.draw.rect(screen, color, box_rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, box_rect, 3, border_radius=15)

        # Draw category icon/text
        text_surface = font.render(self.category.upper(), True, WHITE)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
        screen.blit(text_surface, text_rect)

        # Draw counter badge
        count = len(self.items_sorted)
        if count > 0:
            badge_radius = 20
            badge_x = self.rect.right - 30
            badge_y = self.rect.top + 30
            pygame.draw.circle(screen, GOLD, (badge_x, badge_y), badge_radius)
            pygame.draw.circle(screen, DARK_BROWN, (badge_x, badge_y), badge_radius, 2)
            count_text = smallFont.render(str(count), True, DARK_BROWN)
            count_rect = count_text.get_rect(center=(badge_x, badge_y))
            screen.blit(count_text, count_rect)

    def check_collision(self, item_rect):
        return self.rect.colliderect(item_rect)

    def set_hover(self, is_hover):
        self.hover = is_hover


class Game:
    def __init__(self):
        self.all_items = [
            ("Banana Peel", "Food Waste", "images/banana-peel.png"),
            ("Fries", "Food Waste", "images/fries.jpg"),
            ("Apple Core", "Food Waste", "images/apple-core.png"),
            ("Cardboard", "Recycle", "images/cardboard.jpg"),
            ("Paper", "Recycle", "images/paper.jpg"),
            ("Tin Can", "Recycle", "images/tin-can.jpg"),
            ("Plastic Fork", "Trash", "images/plastic-fork.jpg"),
            ("Empty Chip Bag", "Trash", "images/chipbag.jpg"),
            ("Plastic Bag", "Trash", "images/plastic-bag.jpg"),
        ]
        random.shuffle(self.all_items)

        self.boxes = self.create_category_boxes()
        self.current_item_index = 0
        self.current_item = None
        self.score = 0
        self.total_items = len(self.all_items)
        self.game_over = False
        self.message = ""
        self.message_timer = 0
        self.drag_offset = (0, 0)
        self.particle_effects = []
        self.spawn_next_item()

        # Background pattern
        self.bg_offset = 0

    def create_category_boxes(self):
        box_width = SCREEN_WIDTH // 4
        box_height = SCREEN_HEIGHT // 10
        total_boxes_width = box_width * 3
        total_spacing = SCREEN_WIDTH - total_boxes_width
        gap = total_spacing // 4
        categories = ["Food Waste", "Trash", "Recycle"]
        boxes = []
        for i, category in enumerate(categories):
            x = gap + i * (box_width + gap)
            y = 20
            boxes.append(CategoryBox(category, x, y, box_width, box_height))
        return boxes

    def spawn_next_item(self):
        if self.current_item_index < self.total_items:
            text, category, photo_path = self.all_items[self.current_item_index]
            x = SCREEN_WIDTH // 2 - (SCREEN_WIDTH // 12)
            y = SCREEN_HEIGHT // 2 - (SCREEN_HEIGHT // 12)
            self.current_item = DraggableItem(text, category, x, y, photo_path)
            return True
        else:
            self.game_over = True
            return False

    def add_particle_effect(self, x, y, is_correct):
        color = GREEN if is_correct else RED
        for _ in range(10):
            self.particle_effects.append({
                'x': x, 'y': y, 'vx': random.uniform(-5, 5),
                'vy': random.uniform(-10, -2), 'life': 30,
                'color': color, 'size': random.randint(3, 6)
            })

    def check_sorting(self):
        if not self.current_item:
            return None, None
        for box in self.boxes:
            if box.check_collision(self.current_item.rect):
                if box.category == self.current_item.category:
                    return True, box
                else:
                    return False, box
        return None, None

    def handle_drop(self):
        if not self.current_item:
            return
        result, box = self.check_sorting()
        if result is True:
            self.add_particle_effect(self.current_item.rect.centerx, self.current_item.rect.centery, True)
            box.items_sorted.append(self.current_item)
            self.score += 1
            self.message = f"✓ Correct! +1 point"
            self.message_timer = 60
            self.current_item_index += 1
            self.spawn_next_item()
        elif result is False:
            self.add_particle_effect(self.current_item.rect.centerx, self.current_item.rect.centery, False)
            self.message = f"✗ Wrong! {self.current_item.text} doesn't go in {box.category}!"
            self.message_timer = 60
            self.current_item.reset_position()
        else:
            self.current_item.reset_position()
        self.current_item.end_drag()

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1

        if self.current_item and self.current_item.dragging:
            self.current_item.update()

        # Update hover effects
        mouse_pos = pygame.mouse.get_pos()
        for box in self.boxes:
            box.set_hover(box.rect.collidepoint(mouse_pos))

        # Update particles
        for particle in self.particle_effects[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.5  # gravity
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particle_effects.remove(particle)

    def draw_background(self):
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            color_value = 40 + (y * 15 // SCREEN_HEIGHT)
            color = (color_value, color_value // 2, color_value // 4)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

    def draw(self):
        self.draw_background()

        # Draw boxes
        for box in self.boxes:
            box.draw()

        # Draw current item
        if self.current_item and not self.game_over:
            self.current_item.draw(screen)

        # Draw particles
        for particle in self.particle_effects:
            pygame.draw.circle(screen, particle['color'],
                               (int(particle['x']), int(particle['y'])), particle['size'])

        # Score panel - positioned on the right side, below the first bin
        # First bin is at x = gap (around 62), width is 250, so right edge is around 312
        # Placing score panel at x = SCREEN_WIDTH - 200 (right side)
        score_panel = pygame.Rect(SCREEN_WIDTH - 200, 150, 180, 70)
        pygame.draw.rect(screen, DARK_BROWN, score_panel, border_radius=10)
        pygame.draw.rect(screen, GOLD, score_panel, 2, border_radius=10)

        score_text = font.render(f"Score: {self.score}/{self.total_items}", True, WHITE)
        screen.blit(score_text, (SCREEN_WIDTH - 190, 160))

        remaining_text = smallFont.render(f"Remaining: {self.total_items - self.current_item_index}", True, LIGHT_GRAY)
        screen.blit(remaining_text, (SCREEN_WIDTH - 190, 195))

        # Message popup
        if self.message_timer > 0:
            alpha = min(255, self.message_timer * 4)
            msg_color = GREEN if "Correct" in self.message else RED
            msg_surface = font.render(self.message, True, msg_color)

            # Message background
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
            bg_rect = msg_rect.inflate(30, 15)
            pygame.draw.rect(screen, DARK_BROWN, bg_rect, border_radius=10)
            pygame.draw.rect(screen, GOLD, bg_rect, 2, border_radius=10)
            screen.blit(msg_surface, msg_rect)

        # Instructions
        inst_text = smallFont.render("Drag item to matching colored bin!", True, WHITE)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        inst_bg = inst_rect.inflate(20, 10)
        pygame.draw.rect(screen, DARK_BROWN, inst_bg, border_radius=8)
        screen.blit(inst_text, inst_rect)

        # Game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(DARK_BROWN)
            screen.blit(overlay, (0, 0))

            if self.score == self.total_items:
                win_text = title_font.render("PERFECT! YOU WIN!", True, GOLD)
                win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                screen.blit(win_text, win_rect)

                perfect_text = font.render(f"Final Score: {self.score}/{self.total_items}", True, WHITE)
                perfect_rect = perfect_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(perfect_text, perfect_rect)
            else:
                game_over_text = title_font.render("GAME OVER", True, RED)
                game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
                screen.blit(game_over_text, game_over_rect)

            restart_text = font.render("Press 'R' to play again", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            screen.blit(restart_text, restart_rect)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_game()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.current_item:
                if self.current_item.rect.collidepoint(event.pos):
                    self.current_item.start_drag()
                    self.drag_offset = (self.current_item.rect.x - event.pos[0],
                                        self.current_item.rect.y - event.pos[1])
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.current_item and self.current_item.dragging:
                self.handle_drop()
        elif event.type == pygame.MOUSEMOTION:
            if self.current_item and self.current_item.dragging:
                self.current_item.rect.center = (event.pos[0] + self.drag_offset[0],
                                                 event.pos[1] + self.drag_offset[1])
        return True

    def reset_game(self):
        for box in self.boxes:
            box.items_sorted = []
        random.shuffle(self.all_items)
        self.current_item_index = 0
        self.score = 0
        self.game_over = False
        self.message = ""
        self.message_timer = 0
        self.particle_effects = []
        self.spawn_next_item()


async def main():
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            running = game.handle_event(event)
        game.update()
        game.draw()
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())