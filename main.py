from tkinter import Tk, Label, Button, Canvas
import random


def random_color():
    base = random.randint(0, 0x1000000)
    return '#'+str(hex(base)[2:]).rjust(6, '0')


def parse_pieces(file_name):
    with open(file_name, 'r') as f:
        s = f.read()
        pieces = {}
        for spec in s.split('---\n')[1:]:
            color = spec.split(':')[1]
            shape = [list(map(int, i)) for i in spec.split(':')[2].split('\n')[1:-1]]
            pieces[spec.split(':')[0]] = {'color':color, 'shape':shape, 'location_list':shape_to_location_list(shape)}
        return pieces

def shape_to_location_list(shape):
    loc_list = []
    for x in range(len(shape)):
        for y in range(len(shape[0])):
            if(shape[x][y] == 1):
                loc_list.append((x, y))
    return loc_list


def check_collision(places, board):
    for (x, y) in places:
        if x >= len(board) or x < 0 or y >= len(board[0]) or y < 0:
            return True
        if(board[x][y] != ''):
            return True
    return False


class Tetramino():

    def __init__(self, x0, y0, piece_dict):
        self.piece_dict = piece_dict
        self.piece_choice = list(piece_dict.keys())
        self.x, self.y = x0, y0
        self.x0, self.y0 = x0, y0

    def relative_to_absolute_location(self, place_list):
        return [(self.x+x, self.y+y) for (x, y) in place_list]

    def rotate_piece(self, direction, board):
        # clock wise
        if(direction == 1):
            rotated = list(map(list, zip(*self.shape[::-1])))
        # counter clock wise
        elif(direction == -1):
            rotated = list(map(list, zip(*self.shape)))[::-1]

        else:
            raise ValueError("direction should only be 1 or -1")

        location_list = shape_to_location_list(rotated)
        if(check_collision(self.relative_to_absolute_location(location_list), board)):
            return
        self.shape = rotated
        self.location_list = location_list

    def set_type(self, piece_type):
        self.piece_type = piece_type
        self.color = self.piece_dict[piece_type]['color']
        self.shape = self.piece_dict[piece_type]['shape']
        self.location_list = self.piece_dict[piece_type]['location_list']

    def reset(self, board, type):
        self.x = self.x0
        self.y = self.y0
        self.set_type(type)
        if(check_collision(self.absolute_location(), board)):
            return False
        return True

    def reset_random(self, board):
        return self.reset(board, random.choice(self.piece_choice))
    
    def drop(self, board):
        self.y -=1
        if(check_collision(self.absolute_location(), board)):
            self.y += 1
            return False
        return True

    def move(self, x_offset, board):
        self.x += x_offset
        if(check_collision(self.absolute_location(), board)):
            self.x -= x_offset

    def absolute_location(self):
        return self.relative_to_absolute_location(self.location_list)


class Tetris_View(Canvas):
    def __init__(self, root, x, y, piece_dict):
        self.bg_color = '#EEEEEE'
        self.grid_color = '#888888'
        self.border_width = 5
        self.cell_size = 10
        super().__init__(root, bd=5, relief='sunken', width=40, height=40)
        super().place(x=x, y=y)
        self.piece_dict = piece_dict
        self.piece = ''
        self.display_init()


    def display_init(self):
        self.board_cells = [[0 for _ in range(4)] for _ in range(4)]
        for x in range(4):
            for y in range(4):
                x0 = x*self.cell_size+3+self.border_width
                y0 = (3-y)*self.cell_size+3+self.border_width
                x1 = x0+self.cell_size-2
                y1 = y0+self.cell_size-2
                self.board_cells[x][y] = super().create_rectangle(x0, y0, x1, y1, fill=self.bg_color, width=1, outline=self.grid_color)

    def draw_cell(self, x, y, color):
        if(x<0 or x>4 or y<0 or y>4): return
        super().itemconfig(self.board_cells[x][y], fill=color)

    def update_piece(self, piece):
        if self.piece != '':
            for (x, y) in self.piece_dict[self.piece]['location_list']:
                self.draw_cell(x, y, self.bg_color)
        if piece not in self.piece_dict:
            return
        for (x, y) in self.piece_dict[piece]['location_list']:
                self.draw_cell(x, y, self.piece_dict[piece]['color'])
        self.piece = piece


class Tetris_Game():

    def __init__(self):
        self.root = Tk()
        self.board_cells = [[0 for _ in range(25)] for _ in range(15)]
        self.windows_config()
        self.game_config()
        self.game_board_setup()
        self.logic_counter = 10

    def game_config(self):
        self.score = 0
        self.level = 0
        self.cell_size = 20
        self.border_width = 5
        self.bg_color = '#EEEEEE'
        self.grid_color = '#888888'
        self.pieces = parse_pieces('./pieces.txt')

        self.current_piece = Tetramino(4, 18, self.pieces)

    def windows_config(self):
        self.root.title("Simple Tetris")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        self.root.attributes("-alpha", 0.8)
        self.root.attributes("-topmost", True)
        self.root.config(background="lightblue")
        self.root.bind("<KeyPress>", self.input_handler)
        self.root.protocol("WM_DELETE_WINDOW", self.stop)

    def game_board_setup(self):
        board_width = self.cell_size*10
        board_height = self.cell_size*20
        self.game_canvas = Canvas(self.root, width=board_width, height=board_height, bd=self.border_width, relief='sunken')
        self.game_canvas.place(x=60, y=60)

        self.hold_view = Tetris_View(self.root, x=5, y=60, piece_dict=self.pieces)
        self.hold_piece = ''
        self.hold_valid = True

        self.preview_view = [Tetris_View(self.root, x=275, y=(60+50*i), piece_dict=self.pieces) for i in range(4)]
        self.previews = [random.choice(list(self.pieces.keys())) for i in range(4)]
        self.update_previews()

        self.last_board = [['init' for i in range(40)] for i in range(10)]
        self.board = [['' for i in range(40)] for i in range(10)]
        self.current_piece.reset_random(self.board)
        for x in range(10):
            for y in range(20):
                x0 = x*self.cell_size+3+self.border_width
                y0 = (19-y)*self.cell_size+3+self.border_width
                x1 = x0+self.cell_size-2
                y1 = y0+self.cell_size-2
                self.board_cells[x][y] = self.game_canvas.create_rectangle(x0, y0, x1, y1, fill=self.bg_color, width=1, outline=self.grid_color)
        
        self.draw_board()

        self.score_text = Label(self.root, width=20, borderwidth=3, justify='left', anchor='w', bg='#8080FF')
        self.score_text.place(x=20, y=10)
#        self.score_text.place(x=350, y=80)
        self.score_text.configure(text=f"Your Score:\t{self.score}")

    def update_previews(self):
        for view, piece in zip(self.preview_view, self.previews):
            view.update_piece(piece)

    def draw_board(self):
        piece_location = self.current_piece.absolute_location()
        for x in range(10):
            for y in range(20):
                if(self.board[x][y] != self.last_board[x][y]):
                    if (x, y) in piece_location:
                        continue
                    if self.board[x][y] == '':
                        self.draw_cell(x, y, self.bg_color)
                    else:
                        self.draw_cell(x, y, self.board[x][y])
                    self.last_board[x][y] = self.board[x][y]
        for (x, y) in piece_location:
            self.draw_cell(x, y, self.current_piece.color)
            self.last_board[x][y] = self.current_piece.color

    def input_handler(self, event):
        if event.keycode == 27:
            self.stop()
        if not self.alive:
            if event.keycode in [13]:
                self.reset()
            return 
        if event.keycode in [37]:               # left
            self.current_piece.move(-1, self.board)
            self.game_logic("modify")
        elif event.keycode in [39]:             # right
            self.current_piece.move(1, self.board)
            self.game_logic("modify")
        elif event.keycode in [40]:             # down
            self.game_logic("drop")
        elif event.keycode in [17, 88]:         # rotate cw
            self.current_piece.rotate_piece(-1, self.board)
            self.game_logic("modify")
        elif event.keycode in [38, 90]:         # rotate ccw
            self.current_piece.rotate_piece(1, self.board)
            self.game_logic("modify")
        elif event.keycode in [16, 67]:         # hold piece
            if self.hold_valid:
                self.hold_valid = False
                current_piece_tmp = self.current_piece.piece_type
                if self.hold_piece:
                    self.current_piece.reset(self.board, self.hold_piece)
                else:
                    self.current_piece.reset(self.board, self.previews[0])
                    self.previews = self.previews[1:]
                    self.previews.append(random.choice(list(self.pieces.keys())))
                    self.update_previews()
                self.hold_piece = current_piece_tmp
                self.hold_view.update_piece(self.hold_piece)
            self.game_logic("modify")
        elif event.keycode == 32:               # space - hard drop
            while(self.current_piece.drop(self.board)):
                pass
            self.game_logic("harddrop")
#        else:
#            print(event.keycode, event.char)

    def draw_cell(self, x, y, color):
        if(x<0 or x>10 or y<0 or y>20): return
        self.game_canvas.itemconfig(self.board_cells[x][y], fill=color)

    def game_logic(self, type="timer"):
        if type == "timer":
            self.root.after(100, self.game_logic)
        if not self.alive: return
        dropped = True
        if type == "timer":
            self.logic_counter -= 1
            if self.logic_counter < 0:
                self.logic_counter = 10
                dropped = self.current_piece.drop(self.board)
        elif type == "drop":
            dropped = self.current_piece.drop(self.board)
        elif type == "modify":
            dropped = True
        elif type == "harddrop":
            dropped = False
        if not dropped:
            for (x, y) in self.current_piece.relative_to_absolute_location(self.current_piece.location_list):
                self.board[x][y] = self.current_piece.color
            self.score += self.check_line()
            self.score_text.configure(text=f"Your Score:\t{self.score}")
            if(not self.current_piece.reset(self.board, self.previews[0])):
                self.game_over()
            self.previews = self.previews[1:]
            self.previews.append(random.choice(list(self.pieces.keys())))
            self.update_previews()
            self.hold_valid = True
            self.logic_counter = 0
        self.draw_board()

    def check_line(self):
        newboard = []
        score = 0
        for line in zip(*self.board):
            if '' not in line:
                score += 1
            else:
                newboard.append(line)
        self.board = [list(i)+['']*(40-len(i)) for i in zip(*newboard)]
        return [0, 40, 100, 300, 1200][score]

    def reset(self):
        self.score = 0
        self.level = 0
        self.score_text.configure(text=f"Your Score:\t{self.score}")
        self.last_board = [['init' for i in range(40)] for i in range(10)]
        self.board = [['' for i in range(40)] for i in range(10)]
        self.previews = [random.choice(list(self.pieces.keys())) for i in range(4)]
        self.update_previews()
        self.hold_piece = ''
        self.hold_valid = True
        self.draw_board()
        self.logic_counter = 10
        self.start()

    def run(self):
        self.alive = False
        self.score_text.configure(text=f"Press <Enter> to start")
        self.root.after(100, self.game_logic)
        self.root.mainloop()

    def start(self):
        self.alive = True

    def stop(self):
        self.root.quit()


    def game_over(self):
        self.alive = False
        self.score_text.configure(text=f"Game Over!!!\nYour Score:\t{self.score}")


if __name__ == '__main__':
    tetris = Tetris_Game()
    tetris.run()
