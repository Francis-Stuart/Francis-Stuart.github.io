import asyncio
import random
import pygame
import sys

# Define colors directly (remove dependency on colors.py for web)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 100)
DARK_GRAY = (64, 64, 64)

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Waste Sorting Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
smallFont = pygame.font.Font(None, 24)


class DraggableItem:
    def __init__(self, text, category, x, y, photo):
        self.text = text
        self.category = category
        try:
            self.photo = pygame.image.load(photo)
            self.photo = pygame.transform.scale(self.photo, (SCREEN_WIDTH // 6, SCREEN_HEIGHT // 6))
        except:
            # Create a colored surface if image fails to load
            self.photo = pygame.Surface((SCREEN_WIDTH // 6, SCREEN_HEIGHT // 6))
            self.photo.fill(GREEN)
        self.rect = pygame.Rect(x, y, SCREEN_WIDTH // 6, SCREEN_HEIGHT // 6)
        self.dragging = False
        self.original_pos = (x, y)

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        surface.blit(self.photo, self.rect)
        text_surface = smallFont.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.bottom + 10))
        surface.blit(text_surface, text_rect)

    def update(self):
        if self.dragging:
            self.rect.center = pygame.mouse.get_pos()

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

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 3)
        text_surface = font.render(self.category.upper(), True, BLACK)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery - 15))
        screen.blit(text_surface, text_rect)

    def check_collision(self, item_rect):
        return self.rect.colliderect(item_rect)


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
            ("Plastic Bag", "Trash", "images/platic-bag.jpg"),
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
        self.spawn_next_item()

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
            y = 10
            boxes.append(CategoryBox(category, x, y, box_width, box_height))
        return boxes

    def spawn_next_item(self):
        if self.current_item_index < self.total_items:
            text, category, photo_path = self.all_items[self.current_item_index]
            x = SCREEN_WIDTH // 2 - (SCREEN_WIDTH // 20)
            y = SCREEN_HEIGHT // 2 - (SCREEN_HEIGHT // 20)
            self.current_item = DraggableItem(text, category, x, y, photo_path)
            return True
        else:
            self.game_over = True
            return False

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
            box.items_sorted.append(self.current_item)
            self.score += 1
            self.message = f"Correct! {self.current_item.text} goes to {box.category}!"
            self.message_timer = 90
            self.current_item_index += 1
            self.spawn_next_item()
        elif result is False:
            self.message = f"Wrong! {self.current_item.text} doesn't go in {box.category}!"
            self.message_timer = 90
            self.current_item.reset_position()
        else:
            self.current_item.reset_position()
        self.current_item.end_drag()

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
        if self.current_item and self.current_item.dragging:
            self.current_item.update()

    def draw(self):
        screen.fill(DARK_GRAY)
        for box in self.boxes:
            box.draw()
        if self.current_item and not self.game_over:
            self.current_item.draw(screen)

        score_text = font.render(f"Score: {self.score}/{self.total_items}", True, WHITE)
        screen.blit(score_text, (10, 100))

        if self.message_timer > 0:
            msg_color = GREEN if "Correct" in self.message else RED
            msg_surface = font.render(self.message, True, msg_color)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
            screen.blit(msg_surface, msg_rect)

        inst_text = smallFont.render("Drag item to correct waste bin!", True, WHITE)
        screen.blit(inst_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 30))

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