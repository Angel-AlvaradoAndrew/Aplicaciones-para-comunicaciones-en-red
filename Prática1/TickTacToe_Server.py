#! /usr/bin/python3

# Importa el módulo de socket
import socket
# Importar módulo multihilo
import threading
# Importar el módulo de tiempo
import time
# Importar argumentos de línea de comando
from sys import argv
# Registro de importación
import logging


# Configurar el registro en el archivo
logging.basicConfig(level=logging.DEBUG,
	format='[%(asctime)s] %(levelname)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S',
	filename='ttt_server.log');
# Define un controlador que escribe mensajes INFO o superiores en sys.stderr
# Esto imprimirá todos los mensajes INFO o superiores al mismo tiempo
console = logging.StreamHandler();
console.setLevel(logging.INFO);
# Agrega el controlador al registrador raíz
logging.getLogger('').addHandler(console);

class TTTServer:
	"""TickTackToe_Server se ocupa de las redes y la comunicación con TickTackToe_Client."""

	def __init__(self):
		"""Inicializa el objeto del servidor con un socket de servidor."""
		# Crear un socket TCP/IP
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);

	def bind(self, port_number):
		"""Vincula el servidor con el puerto designado y comienza a escuchar
l          a dirección enlazada."""
		while True:
			try:
				# Enlace a una dirección con el puerto designado
				# La cadena vacía "" es un nombre simbólico
				# es decir, todas las interfaces disponibles
				self.server_socket.bind(("", int(port_number)));
				logging.info("Reserved port " + str(port_number));
				# Comienza a escuchar la dirección enlazada
				self.server_socket.listen(1);
				logging.info("Listening to port " + str(port_number));
				# Rompe el ciclo while si no se detecta ningún error
				break;
			except:
				# Atrapa un error
				logging.warning("There is an error when trying to bind " +
					str(port_number));
				# Pregunta al usuario qué hacer con el error.
				choice = input("[A]bortar, [C]ambiar puerto, o [R]eintentar?");
				if(choice.lower() == "a"):
					exit();
				elif(choice.lower() == "c"):
					port_number = input("Por favor, ingrese el puerto:");

	def close(self):
		# Cierra el Socket
		self.server_socket.close();

class TTTServerGame(TTTServer):
	"""TickTackToe_Server trata con la lógica del juego en el lado del servidor."""

	def __init__(self):
		"""Inicializa el objeto del juego del servidor."""
		TTTServer.__init__(self);

	def start(self):
		"""Inicia el servidor y deja que acepte clientes."""
		# Crea un objeto de matriz para almacenar jugadores conectados
		self.waiting_players = [];
		# Use un candado simple para sincronizar el acceso cuando los jugadores coincidan
		self.lock_matching = threading.Lock();
		# Inicia el bucle principal
		self.__main_loop();

	def __main_loop(self):
		"""(Privado) El bucle principal."""
		# Bucle para aceptar infinitamente nuevas clientes
		while True:
			# Aceptar una conexión de una cliente
			connection, client_address = self.server_socket.accept();
			logging.info("Received connection from " + str(client_address));

			# Inicialice un nuevo objeto Player para almacenar toda la información del cliente
			new_player = Player(connection);
			# Empuja este nuevo objeto jugador en la matriz de jugadores
			self.waiting_players.append(new_player);

			try:
				# Iniciar un nuevo hilo para tratar con este cliente.
				threading.Thread(target=self.__client_thread,
					args=(new_player,)).start();
			except:
				logging.error("Error al crear hilo.");

	def __client_thread(self, player):
		"""(Privado) Este es el hilo del cliente."""
		# Envuelve todo el hilo del cliente con un intento y captura para que
		#  el servidor no se vea afectado incluso si un cliente se equivoca
		try:
			# Envía la identificación del jugador al cliente
			player.send("A", str(player.id));
			# Enviar al cliente no confirmó el mensaje
			if(player.recv(2, "c") != "1"):
				# Un error ha ocurrido
				logging.warning("Client " + str(player.id) +
					" no confirmó el mensaje inicial.");
				# Termina
				return;

			while player.is_waiting:
				# Si el jugador todavía está esperando que otro jugador se una
				# Intenta unir a este jugador con otros jugadores en espera.
				match_result = self.matching_player(player);

				if(match_result is None):
					# Si no coincide, espere un segundo (para mantener bajo el uso de la CPU)
					time.sleep(1);
					# Compruebe si el reproductor todavía está conectado
					player.check_connection();
				else:
					# Si coincide con otro jugador

					# Inicializar un nuevo objeto de juego para almacenar la información del juego.
					new_game = Game();
					# Asignar a ambos jugadores
					new_game.player1 = player;
					new_game.player2 = match_result;
					# Crear una cadena vacía para el contenido del tablero vacío
					new_game.board_content = list("         ");

					try:
						# El juego inicia
						new_game.start();
					except:
						logging.warning("Juego entre " + str(new_game.player1.id) +
							" y " + str(new_game.player2.id) +
							" se termina inesperadamente.");
					# Fin de este hilo
					return;
		except:
			print("Jugador " + str(player.id) + " desconectado.");
		finally:
			# Eliminar al jugador de la lista de espera
			self.waiting_players.remove(player);

	def matching_player(self, player):
		"""Revisa la lista de jugadores e intenta unir al jugador con otro jugador
		que también está esperando para jugar. Devuelve cualquier jugador emparejado si se encuentra."""
		# Intenta adquirir la cerradura
		self.lock_matching.acquire();
		try:
			# Bucle a través de cada jugador
			for p in self.waiting_players:
				# Si se encuentra a otro jugador esperando y no es el jugador mismo
				if(p.is_waiting and p is not player):
					# Jugador emparejado con p
					# Establecer su partida
					player.match = p;
					p.match = player;
					# Configurar sus roles
					player.role = "X";
					p.role = "O";
					# Establecer que el jugador ya no está esperando
					player.is_waiting = False;
					p.is_waiting = False;
					# Luego devuelve la identificación del jugador
					return p;
		finally:
			# Liberar el bloqueo
			self.lock_matching.release();
		# Devolver ninguno si no se encuentra nada
		return None;

class Player:
	"""La clase de jugador describe un cliente con conexión al servidor y
como jugador en el juego de gato dummy."""

	# Cuente los jugadores (para generar ID únicos)
	count = 0;

	def __init__(self, connection):
		"""Inicializar un jugador con su conexión al servidor"""
		# Generar una identificación única para este jugador
		Player.count = Player.count + 1
		self.id = Player.count;
		# Asignar la conexión correspondiente
		self.connection = connection;
		# Establezca el estado de espera del jugador en Verdadero
		self.is_waiting = True;

	def send(self, command_type, msg):
		"""Envía un mensaje al cliente con un token de tipo de comando acordado
         para garantizar que el mensaje se entregue de forma segura."""
		# Un carácter de tipo de comando de 1 byte se coloca al frente del mensaje
		# como una convención de comunicación
		try:
			self.connection.send((command_type + msg).encode());
		except:
			# If any error occurred, the connection might be lost
			self.__connection_lost();

	def recv(self, size, expected_type):
		"""Recibe un paquete con el tamaño especificado del cliente y verifica
          su integridad al comparar su token de tipo de comando con el esperado uno."""
		try:
			msg = self.connection.recv(size).decode();
			# Si recibe una señal de abandono del cliente
			if(msg[0] == "q"):
				# Imprima por qué la señal de dejar de fumar
				logging.info(msg[1:]);
				# Conexión perdida
				self.__connection_lost();
			# Si el mensaje no es el tipo esperado
			elif(msg[0] != expected_type):
				# Conexión perdida
				self.__connection_lost();
			# Si recibió un entero del cliente
			elif(msg[0] == "i"):
				# Regresa el entero
				return int(msg[1:]);
			# En otro caso
			else:
				# Regresa el mensaje
				return msg[1:];
			# Simplemente devuelva el mensaje sin formato si ocurre algo inesperado
			# porque ya no debería importar
			return msg;
		except:
			# Si ocurriera algún error, la conexión podría perderse
			self.__connection_lost();
		return None;

	def check_connection(self):
		"""Envía un mensaje para verificar si el cliente todavía está conectado correctamente."""
		# Envíe al cliente una señal de eco para pedirle que repita
		self.send("E", "z");
		# Compruebe si "e" se devuelve
		if(self.recv(2, "e") != "z"):
			# Si el cliente no confirmó, la conexión podría perderse
			self.__connection_lost();

	def send_match_info(self):
		"""Envía una información coincidente al cliente, que incluye
        el rol asignado y el jugador emparejado."""
		# Enviar al cliente el rol asignado
		self.send("R", self.role);
		# Esperando a que el cliente confirme
		if(self.recv(2,"c") != "2"):
			self.__connection_lost();
		# Se envió al cliente la identificación del jugador coincidente
		self.send("I", str(self.match.id));
		# Esperando a que el cliente confirme
		if(self.recv(2,"c") != "3"):
			self.__connection_lost();

	def __connection_lost(self):
		"""(Privado) Se llamará a esta función cuando se pierda la conexión."""
		# Este jugador ha perdido la conexión con el servidor.
		logging.warning("Jugador " + str(self.id) + " conexión perdida.");
		# Dile al otro jugador que el juego ha terminado.
		try:
			self.match.send("Q", "El otro jugador ha perdido la conexión." +
				" con el servidor.\nGame over.");
		except:
			pass;
		# Genera un error para que el hilo del cliente pueda terminar
		raise Exception;

class Game:
	"""La clase de juego describe un juego con dos jugadores diferentes."""

	def start(self):
		"""Inicia el juego."""
		# Enviar a ambos jugadores la información del partido
		self.player1.send_match_info();
		self.player2.send_match_info();

		# Imprime la información del partido en la pantalla
		logging.info("Jugador " + str(self.player1.id) +
			" Se empareja con el jugador " + str(self.player2.id));

		while True:
			# Jugador 1 movimiento
			if(self.move(self.player1, self.player2)):
				return;
			# Jugador 2 movimiento
			if(self.move(self.player2, self.player1)):
				return;

	def move(self, moving_player, waiting_player):
		"""Deja que un jugador haga un movimiento."""
		# Enviar a ambos jugadores el contenido actual del tablero
		moving_player.send("B", ("".join(self.board_content)));
		waiting_player.send("B", ("".join(self.board_content)));
		# Deje que el jugador en movimiento se mueva, Y significa sí, es el turno de moverse,
		# y N significa no y espera
		moving_player.send("C", "Y");
		waiting_player.send("C", "N");
		# Recibe el movimiento del jugador en movimiento.
		move = int(moving_player.recv(2, "i"));
		# Envía el movimiento al jugador que espera.
		waiting_player.send("I", str(move));
		# Verifique si la posición está vacía
		if(self.board_content[move - 1] == " "):
			# Escríbalo en la pizarra
		 	self.board_content[move - 1] = moving_player.role;
		else:
			logging.warning("Jugador " + str(moving_player.id) +
				" está intentando tomar una posición que ya está" +
				"tomada");


		# Comprueba si esto resultará en una victoria
		result, winning_path = self.check_winner(moving_player);
		if(result >= 0):
			# Si hay un resultado
			# Enviar de vuelta el último contenido del foro
			moving_player.send("B", ("".join(self.board_content)));
			waiting_player.send("B", ("".join(self.board_content)));

			if(result == 0):
				# Si este juego termina con un empate
				# Envía a los jugadores el resultado.
				moving_player.send("C", "D");
				waiting_player.send("C", "D");
				print("Juego entre jugador " + str(self.player1.id) + " y jugador "
					+ str(self.player2.id) + " termina con un empate.");
				return True;
			if(result == 1):
				# Si este jugador gana el juego
				# Envía a los jugadores el resultado.
				moving_player.send("C", "W");
				waiting_player.send("C", "L");
				# Envía a los jugadores el camino ganador.
				moving_player.send("P", winning_path);
				waiting_player.send("P", winning_path);
				print("Jugador " + str(self.player1.id) + " vence al jugador "
					+ str(self.player2.id) + " y termina el juego.");
				return True;
			return False;

	def check_winner(self, player):
		"""Comprueba si el jugador gana el juego. Devuelve 1 si gana,
        0 si es un empate, -1 si aún no hay resultados."""
		s = self.board_content;

		# Comprobar columnas
		if(len(set([s[0], s[1], s[2], player.role])) == 1):
			return 1, "012";
		if(len(set([s[3], s[4], s[5], player.role])) == 1):
			return 1, "345";
		if(len(set([s[6], s[7], s[8], player.role])) == 1):
			return 1, "678";

		# Comprobar filas
		if(len(set([s[0], s[3], s[6], player.role])) == 1):
			return 1, "036";
		if(len(set([s[1], s[4], s[7], player.role])) == 1):
			return 1, "147";
		if(len(set([s[2], s[5], s[8], player.role])) == 1):
			return 1, "258";

		# Comprobar diagonal
		if(len(set([s[0], s[4], s[8], player.role])) == 1):
			return 1, "048";
		if(len(set([s[2], s[4], s[6], player.role])) == 1):
			return 1, "246";

		# Si no queda ninguna posición vacía, dibuja
		if " " not in s:
			return 0, "";

		# El resultado aún no se puede determinar
		return -1, "";

# Define el programa principal.
def main():
	# Si hay más de 2 argumentos
	if(len(argv) >= 2):
		# Establezca el número de puerto en el argumento 1
		port_number = argv[1];
	else:
		# Le Pide al usuario que ingrese el número de puerto
		port_number = input("Por favor ingrese el puerto:");

	try:
		# Inicializar el objeto del servidor
		server = TTTServerGame();
		# Vincula el servidor con el puerto
		server.bind(port_number);
		# Inicia el servidor
		server.start();
		# CIerra el servidor
		server.close();
	except BaseException as e:
		logging.critical("Falla crítica del servidor.\n" + str(e));

if __name__ == "__main__":
	# Si este script se ejecuta como un programa independiente,
	# iniciar el programa principal
	main();