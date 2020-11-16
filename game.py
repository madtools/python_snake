import curses
import math
import random
from typing import List, Optional

DIR_RIGHT = 0
DIR_LEFT = 1
DIR_UP = 2
DIR_DOWN = 3
DIRECTIONS = [DIR_RIGHT, DIR_LEFT, DIR_UP, DIR_DOWN]



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
    HEADS = [">", "<", "^", "v"]
    BODY = "O"

    def __init__(self, size, start_y, start_x, direction=DIR_RIGHT, attr=0):
        self.size = size
        self.direction = direction
        if direction == DIR_RIGHT:
            self.body = [[start_y, x] for x in range(start_x, start_x-size, -1)]
        elif direction == DIR_LEFT:
            self.body = [[start_y, x] for x in range(start_x, start_x+size)]
        self.dead_part = None
        self.curses_attr = attr

    def draw(self, window):
        for i, part in enumerate(self.body):
            if not i:
                window.addch(part[0], part[1], self.HEADS[self.direction], self.curses_attr)
            else:
                window.addch(part[0], part[1], self.BODY, self.curses_attr)
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

    def remove_corpse(self, window):
        for part in self.body:
            window.addch(part[0], part[1], ' ')


class Bot(Snake):
    BAD_POSITION = 1000000

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
        possible_positions = {d: calculate_new_pos(head, d) for d in DIRECTIONS}
        for d, pos in possible_positions.items():
            positions_score[d] = calculate_distance(self.goal, pos)

        for d, pos in possible_positions.items():
            if pos[0] < self.limits[0] or pos[0] > self.limits[2] or pos[1] < self.limits[1] or pos[1] > self.limits[3]:
                positions_score[d] = self.BAD_POSITION
            else:
                for s in snakes:
                    if pos in s.body:
                        positions_score[d] = self.BAD_POSITION
                        break

        ideal_position = sorted(positions_score.items(), key=lambda item: item[1])
        return ideal_position[0][0]


class Game:
    MIN_WIDTH = 20
    MIN_HEIGHT = 6
    HEADER_HEIGHT = 3

    FOOD_COLOR_ID = 1
    WIN_COLOR_ID = 2
    GAME_OVER_COLOR_ID = 3
    PLAYER_COLOR_ID = 4
    CORPSE_COLOR_ID = 5

    DIR_RIGHT = 0
    DIR_LEFT = 1
    DIR_UP = 2
    DIR_DOWN = 3
    DIRECTIONS = [DIR_RIGHT, DIR_LEFT, DIR_UP, DIR_DOWN]

    FOOD = "$"
    SPEED_HORIZONTAL = 100
    SPEED_VERTICAL = 150

    def __init__(self, scr):
        self.score = 0
        self.player: Optional[Snake] = None
        self.bots: List[Bot] = []
        self.snakes: List[Snake] = []
        self.foods = []
        curses.curs_set(0)
        # curses.use_default_colors()
        curses.init_pair(self.FOOD_COLOR_ID, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(self.WIN_COLOR_ID, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(self.GAME_OVER_COLOR_ID, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(self.PLAYER_COLOR_ID, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(self.CORPSE_COLOR_ID, curses.COLOR_RED, curses.COLOR_BLACK)

        self.scr = scr
        self.scr.keypad(True)

        self.screen_height, self.screen_width = scr.getmaxyx()
        if self.screen_height < self.MIN_HEIGHT or self.screen_width < self.MIN_WIDTH:
            raise Exception(f"Window must be at least {self.MIN_WIDTH}x{self.MIN_HEIGHT}")

        self.board_min_x = 1
        self.board_min_y = 1
        self.board_max_x = self.screen_width - 2
        self.board_max_y = self.screen_height-self.HEADER_HEIGHT - 2

        self.board_window = curses.newwin(self.screen_height-self.HEADER_HEIGHT, self.screen_width,
                                          self.HEADER_HEIGHT, 0)
        self.board_window.border(0)
        self.board_window.keypad(True)
        self.board_window.timeout(self.SPEED_HORIZONTAL)

        self.print_center("I'm bored Snake Game", 0)
        self.print_score()

    def get_limits(self):
        return [self.board_min_y, self.board_min_x, self.board_max_y, self.board_max_x]

    def print_center(self, string, line_y, attr=0):
        x = int(self.screen_width / 2 - len(string) / 2)
        self.scr.addstr(line_y, x, string, attr)

    def print_end_screen(self, string, attr=0):
        margin_size = 3

        end_window = self.scr.derwin(5,
                                     len(string) + margin_size*2,
                                     int(self.screen_height / 2 - 5/2),
                                     int(self.screen_width / 2 - len(string) / 2 - margin_size))
        end_window.clear()
        end_window.border(0)
        end_window.addstr(2, margin_size, string, attr)
        end_window.refresh()

    def print_score(self):
        self.print_center(f"Score: {self.score}", 1)

    def generate_foods(self, count):
        for i in range(count):
            while True:
                y = random.randint(self.board_min_y, self.board_max_y)
                x = random.randint(self.board_min_x, self.board_max_x)
                food = [y, x]
                if not any([food in s.body for s in self.snakes]) and food not in self.foods:
                    self.foods.append(food)
                    break

    def draw_foods(self):
        for f in self.foods:
            self.board_window.addch(f[0], f[1], self.FOOD, curses.color_pair(self.FOOD_COLOR_ID))

    def draw_snakes(self):
        for s in self.snakes:
            s.draw(self.board_window)
        # self.player.draw(self.board_window)
        # for bot in self.bots:
        #     bot.draw(self.board_window)

    def add_player(self, size):
        # player is created in the center of the board
        bh, bw = self.board_window.getmaxyx()
        y = int(bh/2)
        x = int(bw/2-size)

        self.player = Snake(size, y, x, attr=curses.color_pair(self.PLAYER_COLOR_ID))
        self.snakes.append(self.player)

    def add_bot(self, size):

        while True:
            y = random.randint(self.board_min_y, self.board_max_y)
            x = random.randint(self.board_min_x + size, self.board_max_x - size)
            direction = random.randint(DIR_RIGHT, DIR_LEFT)
            bot = Bot(size, y, x, direction, self.get_limits())
            overlapped = False
            for part in bot.body:
                for s in self.snakes:
                    if part in s.body:
                        overlapped = True
            if not overlapped:
                break
        self.bots.append(bot)
        self.snakes.append(bot)

    def is_pos_valid(self, pos):
        return self.board_min_y <= pos[0] <= self.board_max_y and self.board_min_x <= pos[1] <= self.board_max_x

    def is_snake_hit_other_snake(self, snake):
        head_pos = snake.get_head()
        for s in self.snakes:
            # if current snake is THE snake, don't check the head.
            if s is snake:
                if head_pos in s.body[1:]:
                    return True
            else:
                if head_pos in s.body:
                    return True

        return False

    def run(self):
        self.draw_snakes()
        self.draw_foods()
        self.scr.refresh()

        while True:
            for bot in self.bots:
                bot_direction = bot.calculate_direction(self.foods, self.snakes)
                if bot_direction is not None:
                    bot.direction = bot_direction

            ch = self.board_window.getch()
            if ch == ord('q'):
                break

            if ch == curses.KEY_LEFT and self.player.direction in [DIR_UP, DIR_DOWN]:
                self.player.direction = DIR_LEFT
                self.board_window.timeout(self.SPEED_HORIZONTAL)
            elif ch == curses.KEY_RIGHT and self.player.direction in [DIR_UP, DIR_DOWN]:
                self.player.direction = DIR_RIGHT
                self.board_window.timeout(self.SPEED_HORIZONTAL)
            elif ch == curses.KEY_UP and self.player.direction in [DIR_LEFT, DIR_RIGHT]:
                self.player.direction = DIR_UP
                self.board_window.timeout(self.SPEED_VERTICAL)
            elif ch == curses.KEY_DOWN and self.player.direction in [DIR_LEFT, DIR_RIGHT]:
                self.player.direction = DIR_DOWN
                self.board_window.timeout(self.SPEED_VERTICAL)

            for bot in self.bots:
                bot.move()
                bot_head = bot.get_head()
                if not self.is_pos_valid(bot_head) or self.is_snake_hit_other_snake(bot):
                    # Bot snake is dead.
                    # bot.remove_corpse(self.board_window)
                    bot.curses_attr = curses.color_pair(self.CORPSE_COLOR_ID)
                    self.bots.remove(bot)
                    self.score += 100
                    self.print_score()
                    self.scr.refresh()

                if bot_head in self.foods:
                    bot.grow()
                    self.foods.remove(bot_head)
                    self.generate_foods(1)
                    self.draw_foods()

            if not len(self.bots):
                self.draw_snakes()
                self.print_end_screen('YOU WIN', curses.color_pair(self.WIN_COLOR_ID))
                while self.scr.getch() in [curses.KEY_LEFT, curses.KEY_RIGHT,
                                                    curses.KEY_UP, curses.KEY_DOWN]:
                    pass
                break

            self.player.move()
            head = self.player.get_head()
            if not self.is_pos_valid(head) or self.is_snake_hit_other_snake(self.player):
                self.draw_snakes()
                self.print_end_screen('GAME OVER', curses.color_pair(self.GAME_OVER_COLOR_ID))
                while self.scr.getch() in [curses.KEY_LEFT, curses.KEY_RIGHT,
                                                    curses.KEY_UP, curses.KEY_DOWN]:
                    pass
                break

            if head in self.foods:
                self.score += 1
                self.player.grow()
                self.foods.remove(head)
                self.generate_foods(1)
                self.draw_foods()
                self.print_score()
                self.scr.refresh()

            self.draw_snakes()


def main(scr: curses.window, *args):
    board = Game(scr)

    bh, bw = board.board_window.getmaxyx()
    area = bh * bw

    board.add_player(5)
    for i in range(int(bh/2)):
        board.add_bot(5)
    board.generate_foods(int(area / 50))

    board.run()


if __name__ == '__main__':
    curses.wrapper(main)
