import chess
import os
import tkinter as tk
import socket, select
import sys
import threading

### TODO:

# change bottom left square to be black

###


class Main():
	def __init__(self, gui):
		self.gui = gui

	def initMain(self):
		self.board = chess.Board()
		self.mycolour = "white"
		self.myturn = True
		self.hasConn = False
		self.square_origin = None
		self.square_dest = None
		self.move_evt = threading.Event()

		client = threading.Thread(target=self.handleConnection)
		client.daemon = True
		client.start()

		while True:
			if self.hasConn:
				self.gui.initialise()
				break

	def handleConnection(self):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect(('192.168.0.1', 2488))
			self.conn = s
			self.hasConn = True
			data = s.recv(1024)
			print('recieved',str(data))
			if data.decode("utf-8") == "white":
				self.mycolour = "white"
				self.myturn = True
			else:
				self.mycolour = "black"
				self.myturn = False

			

			while True:
				if self.myturn:
					if self.move_evt.isSet():
						self.conn.sendall(b'MOVE='+bytes(self.square_origin+self.square_dest, 'utf-8'))
						self.move_evt.clear()

						self.square_origin = None
						self.square_dest = None
						self.myturn = False
				else:
					data = s.recv(1024)
					data = data.decode('utf-8')
					print('received', repr(data))
					if data == '':
						sys.exit()
					elif data.startswith("BOARD_MOVE"):
						## WE ARE GOING TO UPDATE BOARD NOW
						data = data.split('=')[1]

						#FEN STRINGS FORMAT: rnbqkbnr/pppppppp/8/8/8/P7/1PPPPPPP/RNBQKBNR b KQkq - 0 1
						#                              ^                                  ^   ^    
						#                              actual board                     turn castling 

						# SO WE SPLIT ON THE SPACES, THIS GIVES THE BOARD AND THE MOVE, EP SQUARE AND CASTLING

						fen = data
						data = data.split()
						board = data[0]
						turn = data[1]

						self.board.set_fen(fen)
						self.updateBoard()

						if turn == 'w':
							if self.mycolour == "white":
								self.myturn = True
							else:
								self.myturn = False
						elif turn == 'b':
							if self.mycolour == 'black':
								self.myturn = True
							else:
								self.myturn = False

	def move(self, square_origin, square_dest):
		if self.myturn:
			self.square_origin = square_origin
			self.square_dest = square_dest
			self.move_evt.set()

	def updateBoard(self):
		self.gui.canvas.delete("pieces")
		for square in chess.SQUARES:
			piece = self.board.piece_at(square)
			if piece == None:
				#tmp = f'self.gui.square_piece_{chess.square_name(square)}.configure(width=16,height=8)'
				#exec(tmp)
				pass
			else:
				tmp_image = None
				if piece.color == chess.WHITE:
					ptype = piece.symbol()
					if ptype == "P":
						ptype = "pawn"
					elif ptype == "N":
						ptype = "knight"
					elif ptype == "B":
						ptype = "bishop"
					elif ptype == "R":
						ptype = "rook"
					elif ptype == "K":
						ptype = "king"
					elif ptype == "Q":
						ptype = "queen"
					tmp_image = self.gui.piece_images["white"+ptype]
				elif piece.color == chess.BLACK:
					ptype = piece.symbol()
					if ptype == "p":
						ptype = "pawn"
					elif ptype == "n":
						ptype = "knight"
					elif ptype == "b":
						ptype = "bishop"
					elif ptype == "r":
						ptype = "rook"
					elif ptype == "k":
						ptype = "king"
					elif ptype == "q":
						ptype = "queen"
					tmp_image = self.gui.piece_images["black"+ptype]

				
				x, y = self.gui.getCanvasCoords(chess.square_name(square)[0]+chess.square_name(square)[1], middle=True)
				tmp = self.gui.canvas.create_image(x, y, image=tmp_image, tag=chess.square_name(square)+" pieces")
				self.gui.canvas.tag_bind(tmp, "<ButtonPress-1>", self.gui.select_piece)
				self.gui.canvas.tag_bind(tmp, "<B1-Motion>", self.gui.drag_piece)
				self.gui.canvas.tag_bind(tmp, "<ButtonRelease-1>", self.gui.select_piece)

class GUI(tk.Frame):
	def __init__(self, master=None):
		super().__init__(master)
		self.master = master

	def setMain(self, main):
		self.main = main

	def initialise(self):
		self.ROOT_PATH = "C:/Users/cam/Desktop/code/python/chess/photos/"
		self.piece_image_names = ['whiteking.png', 'whiteknight.png', 'whiterook.png', 'whitebishop.png', 'whitepawn.png', 'whitequeen.png', 'blackking.png', 'blackknight.png', 'blackrook.png', 'blackbishop.png', 'blackpawn.png', 'blackqueen.png']
		self.piece_images = {}
		self.master.geometry("1000x1080")
		self.prev_square = ""
		self.canvas = tk.Canvas(self, width=950, height=1080)
		self.canvas.pack()
		self.pack()
		self.create_piece_images()
		self.create_widgets()
 	
	def create_piece_images(self):
		tmp_piece_photo = self.ROOT_PATH + 'square_move.png'
		self.piece_images['square_move'] = tk.PhotoImage(file = tmp_piece_photo)
		for piece in range(0, 12):
			tmp_piece_photo = self.ROOT_PATH + self.piece_image_names[piece]
			self.piece_images[self.piece_image_names[piece].replace('.png', '')] = tk.PhotoImage(file = tmp_piece_photo)
			
	def create_widgets(self):
		ranks = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e', '6': 'f', '7': 'g', '8': 'h'}
		for square in range(1, 9):
			for rank in range(1, 9):
				if square % 2 != 0: # we are odd
					if rank % 2 == 0: # we are even
						background_cl = '#769656' # set to black
						curr_file = self.ROOT_PATH + "blacksquare.png"

					else:
						background_cl = '#eeeed2' # set to white
						curr_file = self.ROOT_PATH + "whitesquare.png"

				else: # we are even
					if rank % 2 == 0: # we are even
						background_cl = '#eeeed2' # set to white
						curr_file = self.ROOT_PATH + "whitesquare.png"
					else:
						background_cl = '#769656' # set to black
						curr_file = self.ROOT_PATH + "blacksquare.png"

				#print(f"HERE: --- Rank:{rank}, Square: {square}, background_cl: {background_cl}")
				if self.main.mycolour == "white":
					#print("COORDS:",rank*100, (9-square)*100, (rank+1)*100, (10-square)*100,"rank: " + ranks[str(rank)], str(square))
					tmp=self.canvas.create_rectangle(rank*100, (9-square)*100, (rank+1)*100, (10-square)*100, fill=background_cl, width=0, tag=ranks[str(rank)]+str(square))
				elif self.main.mycolour == "black":
					#print("COORDS:",(9-rank)*100, square*100, (10-rank)*100, square*100,"rank: " + ranks[str(rank)], str(square))
					tmp=self.canvas.create_rectangle((9-rank)*100, square*100, (10-rank)*100, (square+1)*100, fill=background_cl, width=0, tag=ranks[str(rank)]+str(square))
				#self.canvas.tag_bind(tmp, "<Button-1>", lambda _: self.canvas.itemconfigure(tmp, fill='red'))
				self.canvas.tag_bind(tmp, "<ButtonPress-1>", self.select_piece)
				#tmp_piece = f'self.square_piece_{ranks[str(rank)]}{str(square)}.bind("<Button-1>", lambda e: self.select_piece("{ranks[str(rank)]}{str(square)}", e))'
				#exec(tmp_piece, locals())

	def select_piece(self, event):
		tmp = event.widget.find_withtag('current')[0]

		
		id = self.canvas.itemcget(tmp, "tag").split()[0]
		# piece is [1], current is [2]
		if self.prev_square == "":
			self.prev_square = id
			self.highlightHintSquares(id)
		else:
			print(self.canvas.find_overlapping(event.x, event.y, event.x, event.y))
			print('aaaaaaaaa',self.canvas.itemcget(self.canvas.find_overlapping(event.x, event.y, event.x, event.y)[0], "tag"))
			id = self.canvas.itemcget(self.canvas.find_overlapping(event.x, event.y, event.x, event.y)[0], "tag")
			print('id',id, 'prev_square',self.prev_square)
			self.canvas.delete('hint')
			self.main.move(self.prev_square, id)
			self.prev_square = ""

	def drag_piece(self, event):
		self.canvas.coords('current', event.x, event.y)

	def getCanvasCoords(self, uci_pos, middle=False):
		x = uci_pos[0]
		y = uci_pos[1]

		x = ord(x) - ord('a')+1
		
		if self.main.mycolour == 'white':
			if middle:
				x = x * 100 + 50
				y = (9-int(y)) * 100 + 50
			else:
				x = x * 100
				y = (9-int(y)) * 100
		elif self.main.mycolour == 'black':
			if middle:
				x = (9-x) * 100 + 50
				y = int(y) * 100 + 50
			else:
				x = (9-x) * 100
				y = int(y) * 100
		return x,y

	def highlightHintSquares(self, piece):
		for move in self.main.board.legal_moves:
			move = move.uci()
			origin_square = move[0:2]
			dest_square = move[2:4]

			if origin_square == piece:
				x,y = self.getCanvasCoords(dest_square, middle=True)
				tmp = self.canvas.create_image(x, y, image=self.piece_images['square_move'], tag=dest_square+' hint')
				self.canvas.tag_bind(tmp, "<ButtonPress-1>", self.select_piece)


if __name__ == "__main__":
	root = tk.Tk()
	app = GUI(master=root)
	main = Main(app)
	app.setMain(main)
	main.initMain()
	main.updateBoard()

	app.mainloop()