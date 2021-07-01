import socket
import chess
import sys
import threading
import select
import random

class Lobby():
	def __init__(self):
		self.board = chess.Board()
		self.turn = self.board.turn
		self.white_board_evt = threading.Event()
		self.black_board_evt = threading.Event()

		self.backranks = ['a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1', 'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8']


	def move(self, square_origin, square_dest):
		if square_dest in self.backranks and self.board.piece_at(chess.SQUARES[chess.parse_square(square_origin)]).piece_type == chess.PAWN:
			try:
				move = chess.Move.from_uci(square_origin+square_dest+'q')
			except ValueError:
				print('invalid move')
				return
		else:
			try:
				move = chess.Move.from_uci(square_origin+square_dest)
			except ValueError:
				print('invalid move')
				return
				
		if move in self.board.legal_moves:
			if self.board.is_game_over():
				print('GAME OVER :D')
				self.board.reset()
			else:
				self.board.push(move)
		else:
			pass

class SocketServer():
	def __init__(self):
		self.HOST = '192.168.0.1'
		self.PORT = 2488

		self.colours = ["white", "black"]
		self.players_sent = 0
		self.current_state = ""
		self.lobby = Lobby()

	def startServer(self):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind((self.HOST, self.PORT))
			self.threads = []

			while True:
				s.listen(4)
				print('listening')
				conn, addr = s.accept()
				print('got accept')
				server = threading.Thread(target=self.handleConnection, args=(conn,addr))
				server.daemon = True
				server.start()

	def handleConnection(self, conn, addr):
		with conn:
			print('Connected by:', addr)
			print('sending colour now')

#			conn.setblocking(0)
			colour = random.choice(self.colours)
			conn.sendall(colour.encode("utf-8"))
			self.colours.remove(colour)

			while True:
				if self.lobby.white_board_evt.isSet() and colour == 'white':
					board_fen = self.lobby.board.fen()
					board_fen = board_fen.encode('utf-8')
					print("sending board_fen to white player")
					conn.sendall(b'BOARD_MOVE='+board_fen)
					self.lobby.white_board_evt.clear()
				elif self.lobby.black_board_evt.isSet() and colour == 'black':
					board_fen = self.lobby.board.fen()
					board_fen = board_fen.encode('utf-8')
					print("sending board_fen to black player")
					conn.sendall(b'BOARD_MOVE='+board_fen)
					self.lobby.black_board_evt.clear()
				else:
					print('selecting')
					ready_read, _, _ = select.select([conn], [], [], 1)
					print('after select', ready_read)
					if len(ready_read) > 0:
						data = conn.recv(1024)
						print(data)
						if not data:
							break
						elif data == b'killconn':
							print('killing conn')
							conn.close()
							return "Client killed connection safely."
						elif data == b'killserver':
							print('killing server')
							conn.close()
							sys.exit()
						else:
							command = data.decode("utf-8")
							## CHECK WHAT CCP command is
							if command.startswith('MOVE'):
								# command is a move
								uci_move = command.split('=')[1]
								if len(uci_move) >= 4 and len(uci_move) <= 5:
									## move is legit
									self.lobby.move(uci_move[0:2], uci_move[2:4])
									# set send_board_evt, this will send the board fen to both players
									self.lobby.white_board_evt.set()
									self.lobby.black_board_evt.set()
								else:
									## move isn't legit
									conn.sendall('ERR=MOVE_INVALID')
							else:
								conn.sendall(b"UNKNOWN COMMAND")



if __name__ == "__main__":
	ss = SocketServer()
	ss.startServer()