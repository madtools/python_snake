import curses
import math
import random
from typing import List

MIN_WIDTH = 20
MIN_HEIGHT = 6
HEADER_HEIGHT = 3

DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3
DIRECTIONS = [DIR_RIGHT, DIR_LEFT, DIR_UP, DIR_DOWN]

HEADS = [">", "<", "^", "v"]
BODY = "O"
FOOD = "$"
EMPTY = " "
SPEED_HORIZONTAL = 100
SPEED_VERTICAL = 150

BAD_POSITION = 1000000

# TODO: We should have a board class ?


def calculate_distance(pt1, pt2):
    return math.hypot(pt2[1] - pt1[1], pt2[0] - pt1[0])


def left(pos):
    return [pos[0], pos[1]-1]


def right(pos):
    return [pos[0], pos[1]+1]


def up(pos):
    return [pos[0]-1, pos[1]]


def down(pos):
    return [pos[0]+1, pos[1]]


def calculate_new_pos(pos, direction):
    new_pos = None
    if direction == DIR_RIGHT:
        new_pos = right(pos)
    elif direction == DIR_LEFT:
        new_pos = left(pos)
    elif direction == DIR_UP:
        new_pos = up(pos)
    elif direction == DIR_DOWN:
        new_pos = down(pos)
    return new_pos


class Snake:
    def __init__(self, size, start_y, start_x, direction=DIR_RIGHT):
        self.size = size
        self.direction = direction
        if direction == DIR_RIGHT:
            self.body = [[start_y, x] for x in range(start_x, start_x-size, -1)]
        elif direction == DIR_LEFT:
            self.body = [[start_y, x] for x in range(start_x, start_x+size)]
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
        head = self.get_head()
        new_head = calculate_new_pos(head, self.direction)
        if new_head:
            self.body.insert(0, new_head)
            self.dead_part = self.body.pop(-1)

    def grow(self):
        self.body.append(self.dead_part)
        self.dead_part = None

    def get_head(self):
        return self.body[0]


class Bot(Snake):

    def __init__(self, size, start_y, start_x, direction, limits):
        super().__init__(size, start_y, start_x, direction)
        self.goal = None
        self.limits = limits

    def calculate_direction(self, foods, snakes):
        head = self.get_head()
        if not self.goal or self.goal not in foods:
            # find nearest food
            current_dist = None
            self.goal = None
            for food in foods:
                d = calculate_distance(head, food)
                if current_dist is None or d < current_dist:
                    self.goal = food
                    current_dist = d

        if self.goal is None:
            # We may have a problem
            return None

        positions_score = {}
        possible_positions = {d: calculate_new_pos(head, d) for d in DIRECTIONS }
        for d, pos in possible_positions.items():
            positions_score[d] = calculate_distance(self.goal, pos)

        for d, pos in possible_positions.items():
            if pos[0] < self.limits[0] or pos[0] > self.limits[2] or pos[1] < self.limits[1] or pos[1] > self.limits[3]:
                positions_score[d] = BAD_POSITION
            else:
                for s in snakes:
                    if pos in s.body:
                        positions_score[d] = BAD_POSITION
                        break

        ideal_position = sorted(positions_score.items(), key=lambda item: item[1])
        return ideal_position[0][0]


def generate_foods(window: curses.window, snakes: List[Snake], current_foods:List[List[int]], food_count=1):
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
            if not any([food in s.body for s in snakes]) and food not in current_foods:
                foods.append(food)
                break
    return foods


def draw_foods(window: curses.window, foods):
    for f in foods:
        window.addch(f[0], f[1], FOOD, curses.color_pair(1))


def print_center(window: curses.window, str, line_y, attr=0):
    height, width = window.getmaxyx()
    x = int(width / 2 - len(str) / 2)
    window.addstr(line_y, x, str, attr)


def print_end_screen(window: curses.window, str):
    height, width = window.getmaxyx()

    end_window = window.derwin(5, len(str)+6, int(height/2-3), int(width/2-len(str)/2-3))
    end_window.clear()
    end_window.border(0)
    print_center(end_window, str, 2, curses.color_pair(2))
    end_window.refresh()


def main(scr: curses.window, *args):
    score = 0
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    height, width = scr.getmaxyx()
    if height < MIN_HEIGHT or width < MIN_WIDTH:
        print(f"Window must be at least {MIN_WIDTH}x{MIN_HEIGHT}")

    game_window_height = height-HEADER_HEIGHT
    game_window = curses.newwin(height-HEADER_HEIGHT, width, HEADER_HEIGHT, 0)
    game_window.border(0)
    game_window.keypad(True)
    game_window.timeout(SPEED_HORIZONTAL)
    limits = [1, 1, game_window_height-2, width-2]

    print_center(scr, "I'm bored Snake Game", 0)
    print_center(scr, f"Score: {score}", 1)
    s = Snake(5, 3, 10)
    b = Bot(5, 4, width-10, DIR_LEFT, limits)
    snakes = [s, b]

    b.draw(game_window)
    s.draw(game_window)
    foods = []
    foods = generate_foods(game_window, snakes, foods, 50)
    draw_foods(game_window, foods)
    scr.refresh()

    while True:
        bot_direction = b.calculate_direction(foods, snakes)
        if bot_direction is not None:
            b.direction = bot_direction
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

        b.move()
        bot_head = b.get_head()
        if bot_head[0] < 1 or bot_head[0] > game_window_height-2 or bot_head[1] < 1 or bot_head[1] > width-2 or \
                bot_head in s.body or bot_head in b.body[1:]:
            print_end_screen(game_window, 'YOU WIN')

            while scr.getch() != 10:
                pass
            break

        if b.get_head() in foods:
            b.grow()
            foods.remove(b.get_head())
            foods = generate_foods(game_window, snakes, foods, 1)
            draw_foods(game_window, foods)

        s.move()
        head = s.get_head()
        if head[0] < 1 or head[0] > game_window_height-2 or head[1] < 1 or head[1] > width-2 or head in s.body[1:] or \
                head in b.body:
            print_end_screen(game_window, 'GAME OVER')

            while scr.getch() != 10:
                pass
            break
        if head in foods:
            score += 1
            s.grow()
            foods.remove(head)
            foods = generate_foods(game_window, snakes, foods, 1)
            draw_foods(game_window, foods)

            print_center(scr, f" Score: {score} ", 1)
            scr.refresh()

        b.draw(game_window)
        s.draw(game_window)


if __name__ == '__main__':
    curses.wrapper(main)
