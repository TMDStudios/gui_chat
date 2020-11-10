import socket
import threading


class Server:
    PORT = 5050
    SERVER = "0.0.0.0"  # this server will only work locally, you can use AWS to create an online server
    FORMAT = 'utf-8'

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connections = []  # track active connections
    users = {}  # connect address to username
    active_names = ['helpBot']  # track unique usernames
    clients_list = ''  # convert active_names to string and send it as clients list
    connection_accepted = False

    def __init__(self):
        self.sock.bind((self.SERVER, self.PORT))
        self.sock.listen(1)

    def handler(self, connection, address):
        while True:
            # make sure data exists
            try:
                data = connection.recv(1024)

                # check for new user
                if str(data, self.FORMAT).find('^name^') > -1:
                    # update username
                    self.users.update({address: str(data, self.FORMAT)[6:]})

                    if not self.connection_accepted:
                        if self.users.get(address) in self.active_names:
                            connection.send(bytes('^InvalidName^', self.FORMAT))
                        else:
                            self.connection_accepted = True
                            self.active_names.append(self.users.get(address))
                            print(self.active_names)
                            self.update_clients()

                    connection.send(bytes(f'Welcome {self.users.get(address)}{self.clients_list}', self.FORMAT))

                    # display new user to others
                    if self.connection_accepted:
                        for conn in self.connections:
                            conn.send(bytes(f'{self.users.get(address)} has joined the chat{self.clients_list}',
                                            self.FORMAT))
                            self.connection_accepted = False

                else:
                    # send message
                    if len(str(data, self.FORMAT)) > 0:
                        message = f'{self.users.get(address)}: {str(data, self.FORMAT)}{self.clients_list}'
                        for conn in self.connections:
                            conn.send(bytes(message, self.FORMAT))

            # handle user exit
            except ConnectionResetError:
                print(self.users.get(address), "has left the chat")
                self.active_names.remove(self.users.get(address))
                self.update_clients()
                self.connections.remove(connection)
                for conn in self.connections:
                    if conn != connection:
                        conn.send(bytes(f'{self.users.get(address)} has left the chat{self.clients_list}', self.FORMAT))
                connection.close()
                break

    def update_clients(self):
        self.clients_list = ''
        self.active_names.sort()
        # keep helpBot at the top
        bot_index = self.active_names.index('helpBot')
        self.active_names.pop(bot_index)
        self.active_names.insert(0, 'helpBot')
        for i in self.active_names:
            self.clients_list += "^c^" + i  # create a string of clients separated by '^c^'

    def run(self):
        while True:
            # c, a = connection, address
            c, a = self.sock.accept()
            conn_thread = threading.Thread(target=self.handler, args=(c, a))
            conn_thread.daemon = True
            conn_thread.start()
            self.connections.append(c)

            # display new connections in console
            self.users.update({a: a})
            print(self.users.get(a), "connected")


server = Server()
server.run()
