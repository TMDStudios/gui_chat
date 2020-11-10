import socket
import threading
from tkinter import *


class Client:
    PORT = 5050
    SERVER = '0.0.0.0'  # this server will only work locally, you can use AWS to create an online server
    FORMAT = 'utf-8'

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    username = ''
    user_accepted = False
    private = False
    help_messages = ['helpBot is at your service', 'Type #quit to exit', 'Type @username to send private message']

    def send_message(self, event=None):
        # get most recent message
        msg = gui.chat_window.my_msg.get()
        # reset message input field
        gui.chat_window.my_msg.set("")
        self.sock.send(bytes(msg, self.FORMAT))

    def __init__(self):
        self.sock.connect((self.SERVER, self.PORT))

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()

    def receive(self):
        while True:
            if self.user_accepted:
                # reset private flag
                self.private = False
                message = self.sock.recv(1024).decode(self.FORMAT)
                # filter unwanted messages
                if message.find("^InvalidName^") == -1 and message.find(f"{self.username} has joined") == -1:
                    # populate chat window and refresh current users
                    gui.chat_window.client_list.delete(0, END)
                    gui.chat_window.client_list.insert(END, "Current Users:")
                    # split the message into a list, the first item will be the message and the rest are the users
                    filtered_msg = message.split("^c^")
                    # check if user wants to quit
                    if filtered_msg[0].find(f"{self.username}: #quit") > -1:
                        gui.quit()
                    for user in filtered_msg[1:]:
                        gui.chat_window.client_list.insert(END, user)
                        if user == 'helpBot':
                            gui.chat_window.client_list.itemconfig(END, fg='blue')
                        # check for private message
                        if filtered_msg[0].find(f"@{user}") > -1 or filtered_msg[0].find("@helpBot") > -1:
                            self.private = True

                    if self.private:
                        # make sure only sender and correct recipient see the private message
                        if filtered_msg[0].find(f"@{self.username}") > -1 \
                                or filtered_msg[0].find(f"{self.username}:") > -1:
                            # handle help
                            if filtered_msg[0].find(f"{self.username}:") > -1 and filtered_msg[0].find("@helpBot") > -1:
                                self.show_help()
                            else:
                                # remove '@' and the username, change text color
                                private_msg = filtered_msg[0].replace(f"@{self.username} ", "")
                                gui.chat_window.msg_list.insert(END, private_msg)
                                gui.chat_window.msg_list.itemconfigure(END, fg='magenta')
                    else:
                        # ignore quit command from other users
                        if filtered_msg[0].find(": #quit") == -1:
                            gui.chat_window.msg_list.insert(END, filtered_msg[0])
                        # show help
                        if filtered_msg[0] == f"Welcome {self.username}":
                            self.show_help()

                    # color code messages
                    if message.find("has left the chat") > -1:
                        gui.chat_window.msg_list.itemconfigure(END, fg='red')
                    elif message.find("has joined the chat") > -1:
                        gui.chat_window.msg_list.itemconfigure(END, fg='green')
                    # scroll to bottom
                    gui.chat_window.msg_list.see(END)

    def show_help(self):
        for msg in self.help_messages:
            gui.chat_window.msg_list.insert(END, msg)
            gui.chat_window.msg_list.itemconfigure(END, fg='orange')


client = Client()
FONT = ("Verdana", 12)


class GUI(Tk):

    def __init__(self, *args, **kwargs):
        # initialize tkinter and create main container
        Tk.__init__(self, *args, **kwargs)
        container = Frame(self)
        container.pack(side="top", fill="both", expand=TRUE)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initialize frames
        self.main_window = MainWindow(container, self)
        self.chat_window = ChatWindow(container)

        self.frames = {}

        for f in (self.main_window, self.chat_window):
            frame = f
            self.frames[f] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(self.main_window)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


def name_entry(controller, name):
    gui.chat_window.my_msg.set("")
    gui.chat_window.my_msg.set('^name^' + name)
    client.send_message()
    message = client.sock.recv(1024).decode(client.FORMAT)
    # check if name is available
    if message.find("^InvalidName^") > -1:
        print("Duplicate name")
        gui.main_window.message_box.delete(0, END)
        gui.main_window.message_box.insert(END, "Please choose a different name")
    else:
        print("User accepted")
        client.user_accepted = True
        controller.show_frame(gui.chat_window)
        client.username = name
        gui.chat_window.my_msg.set('^name^' + name)
        client.send_message()


class MainWindow(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        label = Label(self, text="Main Window", font=FONT)
        label.pack(pady=10, padx=10)

        my_msg = StringVar()
        my_msg.set("Enter your name")

        submit_button = Button(self, text="Enter Chat", state=DISABLED,
                               command=lambda: name_entry(controller, self.message_box.get()))

        # reset input box
        def entry_click(event=None):
            my_msg.set("")
            submit_button.config(state=NORMAL)

        self.message_box = Entry(self, textvariable=my_msg, width=60, bg='white')
        self.message_box.pack()
        self.message_box.bind("<1>", entry_click)

        submit_button.pack()


class ChatWindow(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.configure(bg='blue')

        self.my_msg = StringVar()
        self.my_msg.set("Type your message here")
        self.scrollbar = Scrollbar(self)
        self.msg_list = Listbox(self, height=30, width=80, borderwidth=5, yscrollcommand=self.scrollbar)
        self.msg_list.grid(sticky=E, column=0, row=0)
        self.client_list = Listbox(self, height=30, width=20, borderwidth=5)
        self.client_list.grid(sticky=W+N+S, column=1, row=0)

        # reset input box
        def entry_click(event=None):
            self.my_msg.set("")

        # create message input field
        self.entry_field = Entry(self, textvariable=self.my_msg, width=100, borderwidth=11)
        self.entry_field.grid(row=1, column=0, columnspan=2)
        self.entry_field.bind("<Return>", client.send_message)  # enter sends message
        self.entry_field.bind("<1>", entry_click)


gui = GUI()
gui.mainloop()
