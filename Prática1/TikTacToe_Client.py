#! /usr/bin/python3

# Importa el módulo de socket
import socket
# Importar argumentos de línea de comando
from sys import argv

class TTTClient:
	"""TickTackToe_Client se ocupa de las redes y la comunicación con el TickTacToe_Server."""

	def __init__(self):
		"""Inicializa el cliente y crea un socket de cliente."""
		# Crear un socket TCP / IP
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);

	def connect(self, address, port_number):
		"""Sigue repitiéndose la conexión al servidor y devuelve True si
        conectado con éxito"""
		while True:
			try:
				print("Conectándose al servidor del juego...");
				# Tiempo de conexión de 10 segundos
				self.client_socket.settimeout(10);
				# Conéctese al host y puerto especificados
				self.client_socket.connect((address, int(port_number)));
				# Devuelve True si está conectado correctamente
				return True;
			except:
				# Caught an error
				print("Hay un error al intentar conectarse a " +
					str(address) + "::" + str(port_number));
				self.__connect_failed__();
		return False;

	def __connect_failed__(self):
		"""(Privado) Se llamará a esta función cuando intente conectarse
        ha fallado. Esta función puede ser anulada por el programa GUI."""
		# Pregunte al usuario qué hacer con el error.
		choice = input("[A]bortar, [C]cambiar la dirección y puerto o [R]eintetar?");
		if(choice.lower() == "a"):
			exit();
		elif(choice.lower() == "c"):
			address = input("Por favor ingrese la dirección:");
			port_number = input("Por favor ingrese el puerto:");

	def s_send(self, command_type, msg):
		"""Envía un mensaje al servidor con un token de tipo de comando acordado
        para garantizar que el mensaje se entregue de forma segura."""
		# Un carácter de tipo de comando de 1 byte se coloca al frente del mensaje
		# como una convención de comunicación
		try:
			self.client_socket.send((command_type + msg).encode());
		except:
			# Si ocurriera algún error, la conexión podría perderse
			self.__connection_lost();

	def s_recv(self, size, expected_type):
		"""Recibe un paquete con el tamaño especificado del servidor y verifica
           su integridad al comparar su token de tipo de comando con el esperado uno."""
		try:
			msg = self.client_socket.recv(size).decode();
			# Si recibió una señal de salida del servidor
			if(msg[0] == "Q"):
				why_quit = "";
				try:
					# Intenta recibir toda la razón por la cual lo dejo
					why_quit = self.client_socket.recv(1024).decode();
				except:
					pass;
				# Imprime el motivo
				print(msg[1:] + why_quit);
				# Arroja un error
				raise Exception;
			# Si recibió una señal de eco del servidor
			elif(msg[0] == "E"):
				# Echo el mensaje de vuelta al servidor
				self.s_send("e", msg[1:]);
				# Recuperar recursivamente el mensaje deseado
				return self.s_recv(size, expected_type);
			# Si el token de tipo de comando no es el tipo esperado
			elif(msg[0] != expected_type):
				print("El tipo de comando recibido \"" + msg[0] + "\" no " +
					"coincidir con el tipo esperado \"" + expected_type + "\".");
				# Conexión perdida
				self.__connection_lost();
			# Si recibió un entero del servidor
			elif(msg[0] == "I"):
				# Devuelve el entero
				return int(msg[1:]);
			# En otro caso
			else:
				# Devuelve el mensaje
				return msg[1:];
			# Simplemente devuelva el mensaje sin formato si ocurre algo inesperado
			# porque ya no debería importar
			return msg;
		except:
			# Si ocurriera algún error, la conexión podría perderse
			self.__connection_lost();
		return None;

	def __connection_lost(self):
		"""(Privado) Se llamará a esta función cuando se pierda la conexión."""
		print("Error: se perdió la conexión.");
		try:
			# Intente y envíe un mensaje de vuelta al servidor para notificar la conexión perdida
			self.client_socket.send("q".encode());
		except:
			pass;
		# Levanta un error para terminar
		raise Exception;

	def close(self):
		"""Shut down the socket and close it"""
		# Apague el socket para evitar más envíos / recibos
		self.client_socket.shutdown(socket.SHUT_RDWR);
		# Cierra el socket
		self.client_socket.close();

class TTTClientGame(TTTClient):
	"""TickTaclToe_Client trata con la lógica del juego en el lado del cliente."""

	def __init__(self):
		"""Inicializa el objeto del juego del cliente."""
		TTTClient.__init__(self);

	def start_game(self):
		"""Inicia el juego y obtiene información básica del juego del servidor."""
		# Reciba la identificación del jugador del servidor
		self.player_id = int(self.s_recv(128, "A"));
		# Confirme que la identificación ha sido recibida
		self.s_send("c","1");

		# Informe al usuario que se ha establecido la conexión.
		self.__connected__();

		# Recibe el rol asignado del servidor
		self.role = str(self.s_recv(2, "R"));
		# Confirme que se ha recibido el rol asignado
		self.s_send("c","2");

		# Reciba la identificación del jugador mactched del servidor
		self.match_id = int(self.s_recv(128, "I"));
		# Confirme que se ha recibido la identificación del jugador mactched
		self.s_send("c","3");

		print(("Ahora estás emparejado con el jugador " + str(self.match_id)
			+ "\nTu eres el \"" + self.role + "\""));

		# Llame a la función __game_started (), que podría ser implementada por
		# El programa GUI para interactuar con la interfaz de usuario.
		self.__game_started__();

		# Inicia el bucle principal
		self.__main_loop();

	def __connected__(self):
		"""(Privado) Esta función se llama cuando el cliente se ejecuta correctamente
		conectado al servidor Esto podría ser anulado por el programa GUI."""
		# Bienvenida al usuario
		print("Bienvenido a Tic Tac Toe en línea, jugador " + str(self.player_id)
			+ "\nEspera a que otro jugador se una al juego ...");

	def __game_started__(self):
		"""(Privado) Esta función se llama cuando se inicia el juego."""
		# This is a virtual function
		# La implementación real está en la subclase (el programa GUI)
		return;

	def __main_loop(self):
		"""El bucle principal del juego."""
		while True:
			# Obtenga el contenido de la placa del servidor
			board_content = self.s_recv(10, "B");
			# Obtenga el comando del servidor
			command = self.s_recv(2, "C");
			# Actualiza el tablero
			self.__update_board__(command, board_content);

			if(command == "Y"):
				# Si es el turno de este jugador para moverse
				self.__player_move__(board_content);
			elif(command == "N"):
				# Si el jugador solo necesita esperar
				self.__player_wait__();
				# Obtenga el movimiento que hizo el otro jugador desde el servidor
				move = self.s_recv(2, "I");
				self.__opponent_move_made__(move);
			elif(command == "D"):
				# Si el resultado es un empate
				print("Empate.");
				break;
			elif(command == "W"):
				# Si este jugador gana
				print("Ganaste!");
				# Empate camino ganador
				self.__draw_winning_path__(self.s_recv(4, "P"));
				# Rompe el bucle y termina
				break;
			elif(command == "L"):
				# Si este jugador pierde
				print("Perdiste.");
				# Empate camino ganador
				self.__draw_winning_path__(self.s_recv(4, "P"));
				# Rompe el bucle y termina
				break;
			else:
				# Si el servidor devuelve algo irreconocible
				# Simplemente imprímalo
				print("Error: se envió un mensaje desconocido desde el servidor");
				# Y acaba
				break;

	def __update_board__(self, command, board_string):
		"""(Privado) Actualiza el tablero. Esta función puede ser anulada por
        El programa GUI."""
		if(command == "Y"):
			# Si le toca a este jugador moverse, imprima el actual
			# tablero con " " convertido al número de posición correspondiente
			print("Tablero actual:\n" + TTTClientGame.format_board(
				TTTClientGame.show_board_pos(board_string)));
		else:
			# Imprime el tablero actual
			print("Tablero actual:\n" + TTTClientGame.format_board(
				board_string));

	def __player_move__(self, board_string):
		"""(Privado) Permite que el usuario ingrese el movimiento y lo devuelve al
        servidor. Esta función puede ser anulada por el programa GUI."""
		while True:
			# Solicitar al usuario que ingrese una posición
			try:
				position = int(input('Por favor, introduzca la posición (1-9):'));
			except:
				print("Entrada inválida.");
				continue;

			# Asegúrese de que los datos ingresados por el usuario sean válidos
			if(position >= 1 and position <= 9):
				# Si la posición es entre 1 y 9
				if(board_string[position - 1] != " "):
					# Si la posición ya ha sido tomada,
					# Imprime una advertencia
					print("Esa posición ya ha sido tomada." +
						"Por favor elije otro.");
				else:
					# Si la entrada del usuario es válida, rompa el ciclo
					break;
			else:
				print("Ingrese un valor entre 1 y 9 que" +
					"corresponde a la posición en el tablero de la cuadrícula.");
			# Bucle hasta que el usuario ingrese un valor válido

		# Enviar la posición de vuelta al servidor
		self.s_send("i", str(position));

	def __player_wait__(self):
		"""(Privado) Le permite al usuario saber que está esperando que el otro jugador
        hacer un movimiento. Esta función puede ser anulada por el programa GUI."""
		print("Esperando a que el otro jugador haga un movimiento ...");

	def __opponent_move_made__(self, move):
		"""(Privado) Muestra al usuario el movimiento que ha tomado el otro jugador.
        Esta función puede ser anulada por el programa GUI."""
		print("Tu oponente tomó el número" + str(move));

	def __draw_winning_path__(self, winning_path):
		"""(Privado) Muestra al usuario la ruta que ha provocado que el juego
        ganar o perder. Esta función puede ser anulada por el programa GUI."""
		# Generar una nueva cadena de ruta legible por humanos
		readable_path = "";
		for c in winning_path:
			readable_path += str(int(c) + 1) + ", "

		print("El camino es: " + readable_path[:-2]);


	def show_board_pos(s):
		"""(Estático) Convierte las posiciones vacías "" (un espacio) en el tablero
        cadena a su número de índice de posición correspondiente."""

		new_s = list("123456789");
		for i in range(0, 8):
			if(s[i] != " "):
				new_s[i] = s[i];
		return "".join(new_s);

	def format_board(s):
		"""(Estático) Formatea el tablero de la cuadrícula."""

		# Si la longitud de la cadena no es 9
		if(len(s) != 9):
			# Luego imprima un mensaje de error
			print("Error: debe haber 9 símbolos.");
			# Lanza un error
			raise Exception;

		# Dibuja la cuadrícula
		#print("|1|2|3|");
		#print("|4|5|6|");
		#print("|7|8|9|");
		return("|" + s[0] + "|" + s[1]  + "|" + s[2] + "|\n"
			+ "|" + s[3] + "|" + s[4]  + "|" + s[5] + "|\n"
			+ "|" + s[6] + "|" + s[7]  + "|" + s[8] + "|\n");

# Define el programa principal.
def main():
	# Si hay más de 3 argumentos
	if(len(argv) >= 3):
		# Establezca la dirección en el argumento 1 y el número de puerto en el argumento 2
		address = argv[1];
		port_number = argv[2];
	else:
		# Solicite al usuario que ingrese la dirección y el número de puerto
		address = input("Por favor ingrese la dirección:");
		port_number = input("Por favor ingrese el puerto:");

	# Inicializar el objeto del cliente
	client = TTTClientGame();
	# Conectarse al servidor
	client.connect(address, port_number);
	try:
		# Comienza el juego
		client.start_game();
	except:
		print(("Game finished unexpectedly!"));
	finally:
		# Cerrar el cliente
		client.close();

if __name__ == "__main__":
	# Si este script se ejecuta como un programa independiente,
	# inicia el programa principal
	main();