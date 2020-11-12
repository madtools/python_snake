import curses
from typing import List
import  random

MIN_WIDTH = 20
MIN_HEIGHT = 6
HEADER_HEIGHT = 3

DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3

HEADS = [">", "<", "^", "v"]
BODY = "O"
FOOD = "$"
EMPTY = " "
SPEED_HORIZONTAL = 100
SPEED_VERTICAL = 150


class Snake:
    def __init__(self, size, start_y, start_x):
        self.size = size
        self.body = [[start_y, x] for x in range(start_x, start_x-size, -1)]
        self.direction = DIR_RIGHT
        self.dead_part = None

    def draw(self, window):
        for i, part in enumerate(self.body):
            if not i:
                window.addch(part[0], part[1], HEADS[self.direction])
            else:
                window.addch(part[0], part[1], BODY)
        if self.dead_part:
            window.addch(self.dead_part[0], self.dead_part[1], ' ')
            self.dead_part = None

    def move(self):
        head = self.body[0]
        new_head = None
        if self.direction == DIR_RIGHT:
            new_head = [head[0], head[1]+1]
        elif self.direction == DIR_LEFT:
            new_head = [head[0], head[1]-1]
        elif self.direction == DIR_UP:
            new_head = [head[0]-1, head[1]]
        elif self.direction == DIR_DOWN:
            new_head = [head[0]+1, head[1]]
        if new_head:
            self.body.insert(0, new_head)
            self.dead_part = self.body.pop(-1)

    def grow(self):
        self.body.append(self.dead_part)
        self.dead_part = None

    def get_head(self):
        return self.body[0]


def generate_foods(window: curses.window, snake: Snake, current_foods:List[List[int]], food_count=1):
    min_x = min_y = 1
    max_y, max_x = window.getmaxyx()
    max_x -= 2
    max_y -= 2
    foods = current_foods
    for i in range(food_count):
        while True:
            y = random.randint(min_y, max_y)
            x = random.randint(min_x, max_x)
            food = [y, x]
            if food not in snake.body and food not in current_foods:
                foods.append(food)
                break
    return foods


def draw_foods(window: curses.window, foods):
    for f in foods:
        window.addch(f[0], f[1], FOOD)


def print_center(window: curses.window, str, line_y):
    height, width = window.getmaxyx()
    x = int(width / 2 - len(str) / 2)
    window.addstr(line_y, x, str)


def main(scr: curses.window, *args):
    score = 0
    curses.curs_set(0)
    height, width = scr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        print(f"Window must be at least {MIN_WIDTH}x{MIN_HEIGHT}")

    game_window_height = height-HEADER_HEIGHT
    game_window = curses.newwin(height-HEADER_HEIGHT, width, HEADER_HEIGHT, 0)
    game_window.border(0)
    game_window.keypad(True)
    game_window.timeout(SPEED_HORIZONTAL)

    print_center(scr, "I'm bored Snake Game", 0)
    print_center(scr, f"Score: {score}", 1)
    s = Snake(5, 3, 10)
    s.draw(game_window)
    foods = []
    foods = generate_foods(game_window, s, foods, 50)
    draw_foods(game_window, foods)
    scr.refresh()

    while True:
        ch = game_window.getch()
        if ch == ord('q'):
            break

        if ch == curses.KEY_LEFT and s.direction in [DIR_UP, DIR_DOWN]:
            s.direction = DIR_LEFT
            game_window.timeout(SPEED_HORIZONTAL)
        elif ch == curses.KEY_RIGHT and s.direction in [DIR_UP, DIR_DOWN]:
            s.direction = DIR_RIGHT
            game_window.timeout(SPEED_HORIZONTAL)
        elif ch == curses.KEY_UP and s.direction in [DIR_LEFT, DIR_RIGHT]:
            s.direction = DIR_UP
            game_window.timeout(SPEED_VERTICAL)
        elif ch == curses.KEY_DOWN and s.direction in [DIR_LEFT, DIR_RIGHT]:
            s.direction = DIR_DOWN
            game_window.timeout(SPEED_VERTICAL)

        s.move()
        head = s.get_head()
        if head[0] <= 0 or head[0] >= game_window_height-1 or head[1] <= 0 or head[1] >= width-1 or head in s.body[1:]:
            print_center(scr, 'GAME OVER', 0)
            scr.getch()
            break
        if head in foods:
            score += 1
            s.grow()
            foods.remove(head)
            foods = generate_foods(game_window, s, foods, 1)
            draw_foods(game_window, foods)

            print_center(scr, f" Score: {score} ", 1)
            scr.refresh()

        s.draw(game_window)


if __name__ == '__main__':
    curses.wrapper(main)
