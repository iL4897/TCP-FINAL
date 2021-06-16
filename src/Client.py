import socket
import threading
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import datetime

class Client:
    client_sock = None
    data = ''

    def __init__(self, IP, PORT):
        self.initialize_socket(IP, PORT)
        self.initialize_gui()
        self.threads()
    
    def initialize_socket(self, IP, PORT):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock.connect((IP, PORT))

    def threads(self):
        # 클라이언트의 메시지를 보낼 쓰레드
        send_thread = threading.Thread(target=self.Send, args=(self.client_sock, self.data,))
        send_thread.daemon = True
        send_thread.start()

        # 서버로부터 다른 클라이언트의 메시지를 받을 쓰레드
        receive_thread = threading.Thread(target=self.Receive, args=(self.client_sock,))
        receive_thread.daemon = True
        receive_thread.start()

    def send_name(self):
            name = self.name_entry.get()
            if not name:
                messagebox.showwarning("경고", "닉네임을 입력해주세요")
                self.name_entry.delete(0, 'end')
            else:
                send_name = 'Name:' + name
                self.Send(self.client_sock, send_name)
                self.name_label.destroy()
                self.name_entry.destroy()
                self.name_button.destroy()
                self.root.title(name + '님')
                self.send_text.configure(state='normal')
                self.send_btn.configure(state='normal')
                self.chat.grid(row=1, column=0, columnspan=3)
                self.send_text.grid(row=2, column=0, columnspan=2, sticky='nswe')
                self.send_btn.grid(row=2, column=2, sticky='nswe')

    def initialize_gui(self):
        self.root = Tk()
        self.root.title('닉네임을 입력해주세요!')
        self.root.resizable(width=False, height=False)
        self.send_btn = Button(self.root, text='전송', command=self.btn_click)
        self.chat = ScrolledText(self.root, background='#9bbbd4')
        self.send_text = Entry(self.root)
        self.chat.configure(state='disabled')
        self.send_text.configure(state='disabled')
        self.send_btn.configure(state='disabled')
        
        self.name_label = Label(self.root, text='닉네임:')
        self.name_entry = Entry(self.root)
        self.name_button = Button(self.root, text='입장', command=self.send_name)
        self.name_label.grid(row=0, column=0)
        self.name_entry.grid(row=0, column=1)
        self.name_button.grid(row=0, column=2)

    def Send(self, client_sock, data):
        send_data = data.encode('utf-8')
        self.client_sock.send(send_data)

    def btn_click(self):
        # 엔트리에서 값 불러옴
        data = self.send_text.get()
        # 입력값이 있을 때만
        if data != '':
            # 현재 시간 모듈
            now = datetime.datetime.now()
            nowTime = now.strftime('%H:%M:%S')
            # 채팅방 접근 허용
            self.chat.configure(state='normal')
            self.chat.tag_configure('tag-right', justify='right')
            # 채팅, 시간 레이블 생성
            self.label_data = Label(self.chat, text=data, background='#fef01b', justify='right', padx=5, pady=5)
            self.label_time = Label(self.chat, text=nowTime, background='#9bbbd4', foreground='#556677', justify='right', pady=5, anchor='s')
            # 채팅방 설정 (본인: 우측)
            self.chat.insert('end', '\n ', 'tag-right')
            # 채팅방에 입력 값 저장
            self.chat.window_create('end', window=self.label_time)
            self.chat.window_create('end', window=self.label_data)
            self.chat.insert('end', '\n ', 'tag-right')
            self.chat.yview(END)
            self.send_text.delete(0, 'end')
            # 채팅방 접근 금지 (클릭, 수정)
            self.chat.configure(state='disabled')
            # 입력 값 서버로 전송
            self.Send(self.client_sock, data)

    def Receive(self, client_sock):
        while True:
            # 서버로부터 받아온 데이터
            receive_mesage = self.client_sock.recv(1024).decode()
            # 데이터가 없는 경우
            if not receive_mesage:
                break
            # 채팅방 접근 허용
            self.chat.configure(state='normal')
            # 새로운 클라이언트 접속시
            if '님' in receive_mesage:
                # 새로운 클라이언트 메시지 출력
                self.chat.tag_configure('tag-center', justify='center')
                self.chat.insert('end', ' \n ', 'tag-center')
                self.label_message = Label(self.chat, text=receive_mesage, background='#92a4b2', foreground='white', justify='center', font=(None, 8))
                self.chat.window_create('end', window=self.label_message)
                self.chat.insert('end', ' \n ', 'tag-center')
                self.chat.yview(END)
                # 채팅방 접근 금지 (클릭, 수정)
                self.chat.configure(state='disabled')
            # 게임 도중 새로운 클라이언트 접속시
            elif '마지막 단어는' in receive_mesage:
                self.chat.tag_configure('tag-center', justify='center')
                self.chat.insert('end', ' \n ', 'tag-center')
                self.label_message = Label(self.chat, text=receive_mesage, background='#92a4b2', foreground='white', justify='center')
                self.chat.window_create('end', window=self.label_message)
                self.chat.insert('end', ' \n ', 'tag-center')
                self.chat.yview(END)
                # 채팅방 접근 금지 (클릭, 수정)
                self.chat.configure(state='disabled')
            # 채팅 넘겨받을 시
            else:
                # 현재 시간 모듈
                now = datetime.datetime.now()
                nowTime = now.strftime('%H:%M:%S')
                # 채팅방 설정 (상대: 좌측)
                name = receive_mesage.split('/')[0]
                data = receive_mesage.split('/')[1]
                self.chat.tag_configure('tag-left', justify='left')
                self.chat.insert('end', '\n', 'tag-left')
                self.label_name = Label(self.chat, text=name, background='#9bbbd4', foreground='#556677', justify='left', anchor='s')
                self.label_data = Label(self.chat, text=data, background='white', justify='left', padx=5, pady=5)
                self.label_time = Label(self.chat, text=nowTime, background='#9bbbd4', foreground='#556677', justify='left', pady=5, anchor='s')
                self.chat.window_create('end', window=self.label_name)
                self.chat.insert('end', '\n', 'tag-left')
                self.chat.window_create('end', window=self.label_data)
                self.chat.window_create('end', window=self.label_time)
                self.chat.insert('end', '\n', 'tag-left')
                self.chat.yview(END)
                # 채팅방 접근 금지 (클릭, 수정)
                self.chat.configure(state='disabled')
        self.client_sock.close()
        
# TCP Client
if __name__ == '__main__':
    IP = 'localhost'
    PORT = 9000
    
    Client(IP, PORT)
    print('Connecting to ', IP, PORT)

    mainloop()