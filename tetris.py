from scene import *
import sound
import random
import math
A = Action


class Color:
    def __init__(self, r, g, b):
        self.buffer = (r << 16) + (g << 8) + b
        
    def __int__(self):
        return self.buffer

        
class Block:
    Pattern = (
        0x4444,
        0x0e20,
        0x0e80,
        0x06c0,
        0x0660,
        0x0c60,
        0x0e40,
    )
    
    SIZE = 29
    LENGTH = 25
    
    def __init__(self):
        pattern = Block.Pattern[random.randint(0, len(Block.Pattern) - 1)]
        
        color = Color(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        
        self.buffer = self.merge(pattern, color)
                    
    def merge(self, pattern, color):
        new_buffer = 0
        
        for x in range(4):
            for y in range(4):
                if pattern & 0x8000 >> x + y * 4:
                    new_buffer |= int(color) << self.offset(x, y) + Block.LENGTH - 24
                    new_buffer |= 1 << self.offset(x, y)
                    
        return new_buffer
        
    def offset(self, x, y):
        return (3 - y) * (Block.LENGTH * 4) + (3 - x) * Block.LENGTH
           
    def get(self, x, y):
        return self.buffer >> self.offset(x, y) & (1 << Block.LENGTH) - 1
        
    def rotate(self):
        new_buffer = 0
             
        for x in range(4):
            for y in range(4):
                block = self.get(x, y)          
                if block:
                    new_buffer |= block << Block.LENGTH * 15 >> (3 - y) * Block.LENGTH + x * Block.LENGTH * 4
                         
        self.buffer = new_buffer
         
    def map(self, x, y, w, h):
        mod = self.buffer     
        new = 0
        
        base = w * h * Block.LENGTH - (Block.LENGTH * 4 + x * Block.LENGTH + y * w * Block.LENGTH)
            
        for i in range(4):
            offset = base - (3 - i) * w * Block.LENGTH
        
            slice = mod & (1 << Block.LENGTH * 4) - 1
            
            if offset > 0:
                new |= slice << offset
            else:
                new |= slice >> -offset
            
            mod >>= Block.LENGTH * 4
        
        return new
        
        
    def draw(self, sx, sy, a = 1):
        for x in range(4):
            for y in range(4):
                block = self.get(x, y)
                if block:
                    color = block >> Block.LENGTH - 24
                    fill((color >> 16) / 255, (color >> 8 & 0xff) / 255, (color & 0xff) / 255, a)
                    rect(sx + x * Block.SIZE, sy - y * Block.SIZE, Block.SIZE, Block.SIZE)
        
        
class Board:
    WIDTH = 13
    HEIGHT = 20
    SIZE = WIDTH * HEIGHT
    LINE_MASK = (1 << WIDTH * Block.LENGTH) - 1
    FILL_MASK = 0
    for i in range(WIDTH):
        FILL_MASK |= 1 << Block.LENGTH * i
    
    def __init__(self):
        self.buffer = 0
        
    def is_valid(self, x, y, block):
        for row in range(4):
            for col in range(4):
                if block.get(col, row) and  not (0 <= x + col < Board.WIDTH):
                    return False
        return True
        
    def is_collision(self, x, y, block):
        map = block.map(x, y, Board.WIDTH, Board.HEIGHT)
        
        map2 = block.map(x, y - 1, Board.WIDTH, Board.HEIGHT)
     
        if map & self.buffer:
            return True
        
        if map2 & Board.LINE_MASK:
            return True
            
        return False
    
    def put(self, x, y, block):
        self.buffer |= block.map(x, y, Board.WIDTH, Board.HEIGHT)
        
    def is_fill(self, y):
        mask = Board.FILL_MASK << (Board.HEIGHT - y - 1) * Board.WIDTH * Block.LENGTH
        
        return self.buffer & mask == mask
        
    def erase(self, y):
        self.buffer &= ~(Board.LINE_MASK << (Board.HEIGHT - y - 1) * Block.LENGTH * Board.WIDTH)
        
    def down(self, y):
        dump = self.buffer & (~0 << (Board.HEIGHT - y) * Block.LENGTH * Board.WIDTH)
        self.buffer ^= dump
        dump >>= (Board.WIDTH * Block.LENGTH)
        self.buffer |= dump
        
    def update(self):
        y = Board.HEIGHT - 1
            
        while y > 0:
            if self.is_fill(y):
                self.erase(y)
                self.down(y)
            else:
                y -= 1
                
    def get(self, x, y):
        return self.buffer >> (Board.WIDTH - x - 1) * Block.LENGTH + (Board.HEIGHT - y - 1) * Board.WIDTH * Block.LENGTH & (1 << Block.LENGTH) - 1
        
    def draw(self, sx, sy):
        for x in range(Board.WIDTH):
            for y in range(Board.HEIGHT):
                block = self.get(x, y)
                if block:
                    fill('#' + hex(block >> Block.LENGTH - 24))
                else:
                    fill('#' + ('0c1524', '0b1730')[x % 2])
                rect(sx + x * Block.SIZE, sy - y * Block.SIZE, Block.SIZE, Block.SIZE)
        
        
class Tetris (object):
    DELAY = 30
    
    def __init__(self, size):
        self.board = Board()
        self.block = Block()
        self.next_block = Block()
        
        x, y = size
        
        self.offset = ((x - Board.WIDTH * Block.SIZE) // 2, y - Block.SIZE)
        
        self.setup()
        
    def block_left(self):
        if self.check_left():
            self.x -= 1
            
    def block_right(self):
        if self.check_right():
            self.x += 1
            
    def block_down(self):
        if self.check_down():
            self.y += 1
            
        self.delay = Tetris.DELAY
        
    def block_put(self):
        while self.check(self.x, self.y + 1):
            self.y += 1
            
        self.delay = 0
        
    def block_rotate(self):
        for i in range(4):
            self.block.rotate()
            
            if self.check(self.x, self.y):
                return
        
    def check(self, x, y):
        return self.board.is_valid(x, y, self.block) and not self.board.is_collision(x, y, self.block)
        
    def check_left(self):
        return self.check(self.x - 1, self.y)
        
    def check_right(self):
        return self.check(self.x + 1, self.y)
        
    def check_down(self):
        return self.check(self.x, self.y + 1)
        
    def put_block(self):
        self.board.put(self.x, self.y, self.block)
        self.board.update()
        
    def put_draw(self, x, y):
        put_y = self.y
        
        while self.check(self.x, put_y + 1):
            put_y += 1
        
        self.block.draw(x + self.x * Block.SIZE, y - put_y * Block.SIZE, 0.3)
        
    def next(self):
        self.block = self.next_block
        self.next_block = Block()
     
    def setup(self):
        self.delay = Tetris.DELAY
        self.x = Board.WIDTH // 2 - 1
        self.y = -2
        
    def is_over(self):
        return self.board.buffer & Board.LINE_MASK << (Board.HEIGHT * Block.LENGTH * Board.WIDTH)
    
    def update(self):
        self.delay -= 1
        
        if self.is_over():
            self.board = Board()
            self.setup()
        elif not self.check_down():
            if self.delay < 0:
                self.put_block()
                self.next()
                self.setup()
        elif self.delay < 0:
            self.y += 1
            self.delay = Tetris.DELAY
            if self.check_down():
                self.delay *= 3
            
    def draw(self):
        x, y = self.offset
        
        self.board.draw(x, y)
        
        self.block.draw(x + self.x * Block.SIZE, y - self.y * Block.SIZE)
        
        self.put_draw(x, y)
        
        
class Button (object):
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.onclicks = []
        
    def add_click(self, f):
        self.onclicks.append(f)
        
    def contains(self, x, y):
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h
        
    def click(self):
        for onclick in self.onclicks:
            onclick()
        
    def draw(self):
        fill('#fff')
        rect(self.x, self.y, self.w, self.h)
        tint(1,0,0)
        text(self.text, font_size=24, x=self.x + self.w // 2, y=self.y + self.h // 2)
        
        
class MyScene (Scene):
    def setup(self):
        self.tetris = Tetris(get_screen_size())
        
        self.left_btn = Button('⬅️', 2, 0, 71, 87)
        self.left_btn.add_click(self.tetris.block_left)
        
        self.rotate_btn = Button('🔄', 77, 0, 71, 87)
        self.rotate_btn.add_click(self.tetris.block_rotate)
        
        self.right_btn = Button('➡️', 152, 0, 71, 87)
        self.right_btn.add_click(self.tetris.block_right)
        
        self.down_btn = Button('⬇️', 227, 0, 71, 87)
        self.down_btn.add_click(self.tetris.block_down)
        self.put_btn = Button('⏬', 302, 0, 71, 87)
        self.put_btn.add_click(self.tetris.block_put)
        
        self.btns = [self.left_btn, self.rotate_btn, self.right_btn, self.down_btn, self.put_btn]
    
    def did_change_size(self):
        pass
    
    def update(self):
        self.tetris.update()
        pass
    
    def draw(self):
        self.tetris.draw()
        
        for btn in self.btns:
            btn.draw()
        
    def touch_began(self, touch):
        for btn in self.btns:
            if btn.contains(*touch.location):
                btn.click()
    
    def touch_moved(self, touch):
        pass
    
    def touch_ended(self, touch):
        pass

if __name__ == '__main__':
    run(MyScene(), show_fps=False)
