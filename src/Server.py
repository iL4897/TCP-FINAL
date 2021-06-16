from socket import *
from threading import *
from queue import Queue
import requests
import xml.etree.ElementTree as ET

def Send(client_list, send_queue):
    while True:
        try:
            receive_queue = send_queue.get()
            # 새로운 클라이언트 접속시
            if receive_queue == 'New Client Added':
                break
            # 기존 쓰레드 종료 후 새로운 클라이언트가 포함된 client_list 리스트를 인자로 갖는 쓰레드 재생성
            # receive_queue[0] = 메시지, [1] = connection, [2] = name
            name = str(receive_queue[2])
            word = str(receive_queue[0])
            
            isYes, message = game(word)
            for connection in client_list:
                # 단어가 성공적으로 등록된 경우
                if isYes:
                    # 닉네임과 단어를 전송
                    msg = name + '/' + word
                    # 자기 자신을 제외한 다른 클라이언트에게 해당 단어 전송
                    if receive_queue[1] != connection:
                        connection.send(msg.encode('utf-8'))
                # 단어에 오류가 발생한 경우 오류 메세지 출력
                else:
                    # 자기 자신에게만 오류메세지 전송
                    if receive_queue[1] == connection:
                        msg = '에러' + '/' + message
                        connection.send(msg.encode('utf-8'))
        except:
            break

def Receive(connection, count, send_queue):
    while True:
        try:
            # data는 클라이언트로부터 받은 데이터
            # Name:@@@ 형식으로 닉네임을 받아오고,
            # @@@ 형식으로 단어를 받아옴
            # 비어있는 값이 넘어오는 경우는 클라이언트가 종료된 경우
            receive_message = connection.recv(1024).decode()

            # 닉네임 값을 넘겨받은 경우 사용자 추가
            if 'Name' in receive_message:
                name = receive_message.split(':')[1]
                name_list.append(name)
                msg = name + '님이 입장하셨습니다.'
                print(msg)

                # 접속자 중에서 자기 자신을 제외한 모두에게 입장 메세지 전송
                for connection in client_list:
                    if client_list[-1] != connection:
                        connection.send(msg.encode('utf-8'))
                # 게임 도중에 입장한 경우 새로운 접속한 클라이언트에게만 마지막 단어 전송
                if word_list:
                    receive_message = "마지막 단어는 '" + str(word_list[-1]) + "' 입니다."
                    # 마지막으로 접속한 클라이언트에게만 안내 메세지 전송
                    for connection in client_list:
                        if client_list[-1] == connection:
                            connection.send(receive_message.encode('utf-8'))

            # 닉네임이 아닌 값을 받은 경우
            elif 'Name' not in receive_message:
                word = receive_message

            # 클라이언트가 접속을 종료한 경우, 해당 클라이언트 정보 삭제
            if not receive_message:
                # 접속 정보 활용
                idx = client_list.index(connection)
                msg = str(name_list[idx]) + ' 님이 퇴장하셨습니다.'
                print(msg)
                del client_list[idx]
                del name_list[idx]
                # 그룹 내 모든 클라이언트에게 안내 메세지 전송
                for connection in client_list:
                    connection.send(msg.encode('utf-8'))
                count = count - 1
                break
            # 사용자로부터 입력받은 값을 서버에 남김
            print(name + ':' + word)
            # 각각의 클라이언트 메시지, 소켓 정보를 보냄
            send_queue.put([word, connection, name])
        except:
            continue
            
# 단어 유무 검색 메소드
def word_yes(string):
    # 국립국어원 API
    url = 'https://stdict.korean.go.kr/api/search.do?certkey_no=2356&key='
    key = '9717EC333DE82602C2A671DA6CBFF851'
    search = '&type_search=search&q='
    link = url + key + search + string
    # 링크 접속
    response = requests.get(link)
    # XML 로드
    root = ET.fromstring(response.text)
    # 단어와 일치되는 검색 결과의 수 (total = 검색된 단어 개수)
    total = int(root.find("total").text)
    # 없으면 False 리턴
    if total == 0:
        return False
    # 있으면 True 리턴
    else:
        return True

# 끝말잇기, 유무 값과 에러메세지 리턴
def game(word):
    # 단어 유무 검색 메소드 실행
    if word_yes(word):
        # 첫 실행인 경우, 리스트에 추가
        if len(word_list) == 0:
            word_list.append(word)
            return True, ''
        # 두 번째 이상 실행인 경우
        else:
            # 입력받은 값의 첫 글자와 리스트 마지막 단어의 마지막 글자 비교
            if word[0] != word_list[-1][-1]:
                return False, '마지막 단어가 일치하지 않습니다.'
            else:
                # 첫번째 로직 통과 후 단어 중복 여부 판별
                if word in word_list:
                    return False, '이미 사용된 단어입니다.'
                # 모든 로직 통과 후 단어 삽입
                else:
                    word_list.append(word)
                    return True, ''
    # 단어가 없는 경우
    else:
        return False, '없는 단어입니다.'

if __name__ == '__main__':
    # 새로운 접속 정보 및 클라이언트 정보를 담을 큐
    send_queue = Queue()
    # 서버 정보
    IP = ''
    PORT = 9000
    server_sock = socket(AF_INET, SOCK_STREAM)
    # 중복 포트 사용시 에러 처리
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_sock.bind((IP, PORT))
    server_sock.listen(10)
    # 총 접속 클라이언트 개수
    count = 0
    # 연결된 클라이언트 정보를 담을 리스트
    client_list = []
    # 사용자 이름 리스트
    name_list = []
    # 끝말잇기를 위한 단어 저장 리스트
    word_list = []
    
    while True:
        count = count + 1
        connection, address = server_sock.accept()
        print('Connected ' + str(address))
        # 연결된 클라이언트의 소켓 정보 추가
        client_list.append(connection)

        # 소켓에 연결된 모든 클라이언트에게 동일한 메시지를 보내기 위한 쓰레드(브로드캐스터)
        # 연결된 클라이언트가 1명 이상일 경우 변경된 client_list 리스트로 반영
        if count > 1:
            send_queue.put('New Client Added')
            send_thread = Thread(target=Send, args=(client_list, send_queue,))
            send_thread.start()
            pass
        else:
            send_thread = Thread(target=Send, args=(client_list, send_queue,))
            send_thread.start()


        # 소켓에 연결된 각각의 클라이언트의 메시지를 받을 쓰레드
        receive_thread = Thread(target=Receive, args=(connection, count, send_queue,))
        receive_thread.start()
