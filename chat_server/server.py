import socket
import threading
import select
import json
import sys
import queue
import logging
from absl import app, flags
import message_pb2 as pb


FLAGS = flags.FLAGS

flags.DEFINE_string('ip', default='127.0.0.1', help='서버 IP 주소')
flags.DEFINE_integer('port', default=None, required=True, help='서버 port 번호')
flags.DEFINE_enum('format', default='json', enum_values=['json', 'protobuf'], help='메시지 포맷')
flags.DEFINE_integer('threads', default=2, help='사용할 작업 쓰레드 수')

message_queue = queue.Queue()
clients = {}
rooms = {}
worker_threads=[]
shutdown_event = threading.Event()
message_lock = threading.Lock()


class NoTypeFieldInMessage(RuntimeError):
    pass

class UnknownTypeInMessage(RuntimeError):
    def __init__(self, _type):
        self.type = _type
    def __str__(self):
        return str(self.type)

# JSON 메시지 처리 함수
def process_json_message(data):
    if data.startswith(b'\x00'):
        data = data[1:]
    try:
        return json.loads(data.decode('utf-8'))
    except json.JSONDecodeError:
        print("잘못된 JSON 메시지")
        return None

# Protobuf 메시지 처리 함수
def process_protobuf_message(data):
    try:
        type_message = pb.Type()
        type_message.ParseFromString(data[0])
        print(type_message)
        # type 필드 검증
        if not hasattr(type_message, 'type'):
            raise ValueError("type_message에 'type' 필드가 없습니다.")

        # MessageType 추출
        message_type = type_message.type
        print(f"추출된 message_type: {message_type}")
         
        if message_type==pb.Type.MessageType.CS_NAME:
            cs_name_message=pb.CSName()
            cs_name_message.ParseFromString(data[1])
            result={
                "type":"CS_NAME",
                "name":cs_name_message.name
            }
            return result
        elif message_type==pb.Type.MessageType.CS_CREATE_ROOM:
            cs_room_message=pb.CSCreateRoom()
            cs_room_message.ParseFromString(data[1])
            result={
                "type":"CS_CREATE_ROOM",
                "title":cs_room_message.title
            }
            return result
        elif message_type==pb.Type.MessageType.CS_ROOMS:
            cs_room_message=pb.CSRooms()
            cs_room_message.ParseFromString(data[1])
            result={
                "type":"CS_ROOMS",
            }
            return result
        elif message_type==pb.Type.MessageType.CS_JOIN_ROOM:
            cs_room_message=pb.CSJoinRoom()
            cs_room_message.ParseFromString(data[1])
            result={
                "type":"CS_JOIN_ROOM",
                "roomId":cs_room_message.roomId
            }
            return result
        elif message_type==pb.Type.MessageType.CS_CHAT:
            cs_room_message=pb.CSChat()
            cs_room_message.ParseFromString(data[1])
            result={
                "type":"CS_CHAT",
                "member":cs_room_message.member,
                "text":cs_room_message.text
            }
            return result
        elif message_type==pb.Type.MessageType.CS_LEAVE_ROOM:
            cs_room_message=pb.CSLeaveRoom()
            cs_room_message.ParseFromString(data[1])
            result={
                "type":"CS_LEAVE_ROOM",
            }
            return result
        elif message_type==pb.Type.MessageType.CS_SHUTDOWN:
            cs_room_message=pb.CSShutdown()
            cs_room_message.ParseFromString(data[1])
            result={
                "type":"CS_SHUTDOWN",
            }
            return result

        
        

    except Exception as e:
        print(f"Protobuf 파싱 중 오류 발생: {e}")
        return None

# 클라이언트로 메시지 전송
def send_message_to_client(client_sock, message):
    # 메시지를 JSON 또는 Protobuf 형식으로 직렬화
    if FLAGS.format == 'json':
        serialized = bytes(json.dumps(message), encoding='utf-8')
        message_length = int.to_bytes(len(serialized), byteorder='big', length=2)
        client_sock.send(message_length+serialized)
    else:
        
        print("protobuf 클라이언트로 응답 내기")
        print(f"보내기전 {message}")
        if message['type'] == 'SCSystemMessage':
            # 메시지 타입 정의
            type_message = pb.Type()

            type_message.type = pb.Type.MessageType.SC_SYSTEM_MESSAGE


            # 시스템 메시지 본문 정의
            system_message = pb.SCSystemMessage()
            system_message.text = message['text']
        
            # 각각 직렬화
            serialized_type = type_message.SerializeToString()
            serialized_response = system_message.SerializeToString()

            # 타입 메시지 길이 전송
            type_length = len(serialized_type)
            type_length_bytes = int.to_bytes(type_length, byteorder='big', length=2)
            client_sock.send(type_length_bytes + serialized_type)
            print(f"전송 완료: {type_length_bytes + serialized_type}")

            # 시스템 메시지 길이 전송
            response_length = len(serialized_response)
            response_length_bytes = int.to_bytes(response_length, byteorder='big', length=2)
            client_sock.send(response_length_bytes + serialized_response)
            print(f"전송 완료: {response_length_bytes + serialized_response}")
        elif message['type'] == 'SCRoomsResult':
            # 메시지 타입 정의
            type_message = pb.Type()
            type_message.type = pb.Type.MessageType.SC_ROOMS_RESULT

            # SCRoomsResult 메시지 정의
            rooms_result_message = pb.SCRoomsResult()

            # 방 정보 추가 (rooms는 message에 포함된 rooms 데이터에 따라 다를 수 있음)
            for room in message['rooms']:
                room_info = rooms_result_message.RoomInfo()
                room_info.roomId = room['roomId']
                room_info.title = room.get('title', '')
                room_info.members.extend(room['members'])  # 여러 멤버 추가

                rooms_result_message.rooms.append(room_info)

            # 각각 직렬화
            serialized_type = type_message.SerializeToString()
            serialized_response = rooms_result_message.SerializeToString()

            # 타입 메시지 길이 전송
            type_length = len(serialized_type)
            type_length_bytes = int.to_bytes(type_length, byteorder='big', length=2)
            client_sock.send(type_length_bytes + serialized_type)
            print(f"전송 완료: {type_length_bytes + serialized_type}")

            # SCRoomsResult 메시지 길이 전송
            response_length = len(serialized_response)
            response_length_bytes = int.to_bytes(response_length, byteorder='big', length=2)
            client_sock.send(response_length_bytes + serialized_response)
            print(f"전송 완료: {response_length_bytes + serialized_response}") 
        elif message['type'] == 'SCChat':
            # 메시지 타입 정의
            type_message = pb.Type()
            type_message.type = pb.Type.MessageType.SC_CHAT

            # SCChat 메시지 본문 정의
            chat_message = pb.SCChat()
            chat_message.member = message['member']
            chat_message.text = message['text']

            # 각각 직렬화
            serialized_type = type_message.SerializeToString()
            serialized_response = chat_message.SerializeToString()

            # 타입 메시지 길이 전송
            type_length = len(serialized_type)
            type_length_bytes = int.to_bytes(type_length, byteorder='big', length=2)
            client_sock.send(type_length_bytes + serialized_type)
            print(f"전송 완료: {type_length_bytes + serialized_type}")

            # SCChat 메시지 길이 전송
            response_length = len(serialized_response)
            response_length_bytes = int.to_bytes(response_length, byteorder='big', length=2)
            client_sock.send(response_length_bytes + serialized_response)
            print(f"전송 완료: {response_length_bytes + serialized_response}")



# 대화방에 있는 모든 클라이언트에게 메시지 전송
def send_message_to_room(room_id, message, exclude_sock=None):
    print(f"모든방{message}")
    room = rooms.get(room_id)
    if room:
        for member in room["members"]:
            if member['sock'] != exclude_sock:  # exclude_sock이 있는 경우 해당 소켓은 제외
                send_message_to_client(member['sock'], message)

def on_sc_name(sock, message, address):
    # if FLAGS.format == 'json':
    new_name = message.get('name')
    if not new_name:
        error_message = {"type": "SCSystemMessage", "text": "이름을 적어주세요."}
        send_message_to_client(sock, error_message)
        return

    clients[address]['name'] = new_name
    system_message = {"type": "SCSystemMessage", "text": f"이름이 {new_name}으로 변경되었습니다."}
    send_message_to_client(sock, system_message)

    # 대화방에 있는 모든 클라이언트에게 시스템 메시지 전송
    for room_id, room in rooms.items():
        for member in room["members"]:
            if member['sock'] == sock:  # 본인이 속한 방만 확인
                send_message_to_room(room_id, system_message) 

    

def on_sc_create(sock, message, address):
    room_name = message.get('title')

    if not room_name:
        error_message = {"type": "SCSystemMessage", "text": "방 이름을 적어주세요."}
        send_message_to_client(sock, error_message)
        return
    
    if address in clients and clients[address].get('room'):
        error_message = {"type": "SCSystemMessage", "text": "대화방에 있을 때는 방을 개설할 수 없습니다."}
        send_message_to_client(sock, error_message)
        return
    
    # 새로운 방을 rooms에 추가
    room_id = len(rooms) + 1
    rooms[room_id] = {"name": room_name, "members": []}

    # 클라이언트를 해당 방에 추가
    clients[address]['room'] = room_id
    rooms[room_id]["members"].append({'sock': sock, 'name': clients[address]['name']})

    system_message = {"type": "SCSystemMessage", "text": f"방제 {room_name} 방에 입장했습니다."}
    send_message_to_client(sock, system_message)

    send_message_to_room(room_id, {"type": "SCSystemMessage", "text": f"방제 [{room_name}] 방에 입장했습니다."},exclude_sock=sock)

def on_sc_rooms_result(sock, message, address):
    room_list = {"rooms": []}
    for room_id, room in rooms.items():
        member_names = [member['name'] for member in room["members"]]
        room_list['rooms'].append({
            "roomId": room_id,
            "title": room["name"],
            "members": member_names
        })
    
    room_list_message = {"type": "SCRoomsResult", "rooms": room_list["rooms"]}
    send_message_to_client(sock, room_list_message)

def on_sc_join(sock, message, address):
    room_id = message.get('roomId')

    # 클라이언트가 이미 다른 방에 참여중인 경우
    if address in clients and clients[address].get("room"):
        error_message = {"type": "SCSystemMessage", "text": "대화 방에 있을 때는 다른 방에 들어갈 수 없습니다."}
        send_message_to_client(sock, error_message)
        return

    # 방 번호가 존재하는지 확인
    if room_id not in rooms:
        error_message = {"type": "SCSystemMessage", "text": "대화방이 존재하지 않습니다!"}
        send_message_to_client(sock, error_message)
        return

    # 방에 참여
    room = rooms[room_id]
    room_name = room["name"]

    new_member = {"name": clients[address]["name"], "sock": sock}

    # 클라이언트를 해당 방에 추가
    room["members"].append(new_member)
    clients[address]["room"] = room_id

    # 방에 입장 메시지를 해당 클라이언트에게 전송
    join_message = {"type": "SCSystemMessage", "text": f"방제[{room_name}] 방에 입장했습니다."}
    send_message_to_client(sock, join_message)

    # 방에 있는 모든 멤버에게 입장 메시지 전송
    for member in room["members"]:
        if member["sock"] != sock:  # 자기 자신에게는 메시지 보내지 않음
            enter_message = {"type": "SCSystemMessage", "text": f"{new_member['name']} 님이 입장했습니다."}
            send_message_to_client(member["sock"], enter_message)

def on_sc_leave_room(sock, message, address):
    if address not in clients or 'room' not in clients[address] or not clients[address]['room']:
        error_message = {"type": "SCSystemMessage", "text": "현재 대화방에 들어가 있지 않습니다."}
        send_message_to_client(sock, error_message)
        return
    
    room_id = clients[address]['room']
    room_name = rooms[room_id]["name"]
    client_name = clients[address]['name']

    # 방에서 클라이언트를 제거
    rooms[room_id]["members"] = [member for member in rooms[room_id]["members"] if member['sock'] != sock]

    # 방에 남아있는 멤버들에게 퇴장 메시지 전송
    leave_message = {"type": "SCSystemMessage", "text": f"[{client_name}] 님이 퇴장했습니다."}
    send_message_to_room(room_id, leave_message, exclude_sock=sock)

    # 나간 유저에게 방 퇴장 알림 메시지 전송
    exit_message = {"type": "SCSystemMessage", "text": f"방제 [{room_name}] 대화 방에서 퇴장했습니다."}
    send_message_to_client(sock, exit_message)

    clients[address]['room'] = None

    if not rooms[room_id]["members"]:
        del rooms[room_id]

def on_sc_shutdown(sock, message, address):
    print("서버 중지가 요청됨")
    shutdown_message = {"type": "SCSystemMessage", "text": "서버가 곧 종료됩니다."}
    
    # 서버 종료 이벤트 설정
    shutdown_event.set()
    send_message_to_client(sock, shutdown_message)

def on_chat(sock, message,address):
    if address not in clients or 'room' not in clients[address] or not clients[address]['room']:
        error_message = {"type": "SCSystemMessage", "text": "현재 대화방에 들어가 있지 않습니다."}
        send_message_to_client(sock, error_message)
        return
    
    room_id=clients[address]['room']
    text_message={
        "type":"SCChat",
        "member":clients[address]['name'],
        "text":message.get('text')
    }

    send_message_to_room(room_id,text_message,exclude_sock=sock)

def handle_unknown_command(sock, message, address):
    on_chat(sock,message,address)

command_handlers = {
    "CSName": on_sc_name,
    "CSCreateRoom": on_sc_create,
    "CSRooms": on_sc_rooms_result,
    "CSJoinRoom": on_sc_join,
    "CSLeaveRoom": on_sc_leave_room,
    "CSShutdown": on_sc_shutdown,
    "SCCha":on_chat
}
protobuf_message_handlers = {
    "CS_NAME": on_sc_name,
    "CS_ROOMS":on_sc_rooms_result,
    "CS_CREATE_ROOM": on_sc_create,
    "CS_JOIN_ROOM":on_sc_join,
    "CS_LEAVE_ROOM": on_sc_leave_room,
    "CS_CHAT": on_chat,
    "CS_SHUTDOWN": on_sc_shutdown,
}

def handle_command(sock, message, address):
    if FLAGS.format=='json':
        command_type = message.get('type')
        handler = command_handlers.get(command_type, handle_unknown_command)
        handler(sock, message, address)
    elif FLAGS.format=='protobuf':
        # Protobuf 메시지에서 type 필드를 확인
        command_type = message.get('type')
        handler = protobuf_message_handlers.get(command_type, handle_unknown_command)
        handler(sock, message, address)
        
       

def handle_client(sock, address):
    try:
        inputs=[sock]
        client_format=None
        received_data=[]
        total_length=0
        current_length=0
        while True:
            if shutdown_event.is_set():
                break  # 종료 이벤트가 설정되면 루프 종료

            readable,_,_=select.select(inputs,[],[],1)
            for s in readable:
                length_data = sock.recv(2)
                if not length_data:
                    break

                # 메시지 길이 추출
                message_length = int.from_bytes(length_data, byteorder='big')
                data = sock.recv(message_length)
                print(f"메시지 길이: {message_length}/ 데이터:{data}")

                if not data:
                    break
                
                if client_format is None:
                    client_format=identify_format(data)
                    if client_format:
                        FLAGS.format=client_format

                # 메시지 파싱
                if client_format == 'json':
                    message = process_json_message(data)
                    if message:
                        handle_command(sock, message, address)

                elif client_format=='protobuf':
                    # 수신된 데이터를 리스트에 추가
                    received_data.append(data)
                    current_length += len(data)
                    total_length += message_length  # 전체 메시지 길이 업데이트
                    print(f"Received data: {received_data}")

                    # 전체 데이터가 수신되었는지 확인
                    if current_length >= total_length:
                        # 모든 데이터가 수신되었을 때 처리
                        print(f"Processing Protobuf message with data: {received_data}")
                        message = process_protobuf_message(received_data)
                        if message:
                            handle_command(sock, message, address)
                        # 데이터 초기화
                        received_data.clear()  # 리스트 초기화
                        current_length = 0  # 현재 길이 초기화
                        total_length = 0  # 전체 길이 초기화

                else:
                    raise ValueError("지원되지 않는 메시지 포맷")
            
                
    
    except Exception as e:
        print(f"클라이언트 핸들링 중 오류 발생: {e}")
    finally:
        if address in clients:
            clients.pop(address)
        try:
            if sock.fileno() != -1:  # 소켓이 유효한지 확인
                sock.close()
        except Exception as e:
            print(f"소켓 닫기 중 오류: {e}")
def identify_format(data):
    """
    데이터에서 JSON 또는 Protobuf 포맷을 구분하는 함수
    """
    try:
        # JSON 형식인지 확인 (첫 번째 바이트가 '{'로 시작하면 JSON)
        if data[0] == 0x7B:  # JSON 시작 ('{')
            print(f"JSON: {data}")
            return 'json'
        else:
            # Protobuf 형식으로 처리
            try:
                # Protobuf의 Type 메시지를 파싱
                type_message = pb.Type()  # 임포트한 Protobuf 타입 사용
                type_message.ParseFromString(data)
                return 'protobuf'
            except Exception as e:
                print(f"1Protobuf 파싱 오류: {e}")
                return None
    except Exception:
        return None

def worker_thread():
    while True:
        message = message_queue.get()
        if message is None:
            break
        with message_lock:
            print(f'처리된 메시지: {message}')
            for client in clients.values():
                try:
                    client['sock'].sendall(str(message).encode('utf-8'))
                except Exception as e:
                    print(f"메시지 전송 오류: {e}")
    print(f"메시지 작업 쓰레드 #{threading.current_thread().name} 종료")

def start_server():
    # 서버 소켓 설정 및 시작
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((FLAGS.ip, FLAGS.port))
    server_sock.listen(5)
    server_sock.settimeout(1)

    for i in range(FLAGS.threads):
        thread = threading.Thread(target=worker_thread,daemon=True,name=f"{i}")
        thread.daemon = True
        thread.start()
        worker_threads.append(thread)
        print(f'메시지 작업 쓰레드 #{i} 생성')

    
    print(f"Port 번호 {FLAGS.port}에서 서버 동작 중")

    try:
        while not shutdown_event.is_set():  # 종료 이벤트가 발생하기 전까지 루프 유지
            # 클라이언트 연결 수락
            try:
                client_sock, client_address = server_sock.accept()
            except socket.timeout:
                continue

            if shutdown_event.is_set():  # 종료 요청이 있을 경우 새로운 클라이언트 수락 중단
                print("서버 종료 중, 새로운 클라이언트 수락 중단")
                client_sock.close()
                continue
            
            print(f"새로운 클라이언트 접속 {client_address}")

            # 클라이언트 정보 저장
            clients[client_address] = {"sock": client_sock, "name": f"{client_address[0]}:{client_address[1]}", "room": None}

            # 클라이언트 핸들링 쓰레드 시작
            threading.Thread(target=handle_client, args=(client_sock, client_address)).start()

    except KeyboardInterrupt:
        print("키보드로 프로그램 강제 종료 요청")

    finally:
        print("Main thread 종료 중")
        shutdown_event.set()

        for client in clients.values():
            try:
                if client['sock'].fileno() != -1:  # 소켓이 유효한지 확인
                    client['sock'].close()
            except Exception as e:
                print(f"클라이언트 소켓 닫기 중 오류 발생: {e}")
        clients.clear()  # 클라이언트 목록 초기화

        # 메시지 큐에 None 추가하여 작업 쓰레드 종료
        for _ in worker_threads:
            message_queue.put(None)
            
        # 서버 소켓 및 쓰레드 정리
        server_sock.close()
        for thread in worker_threads:
            print("작업 쓰레드 join() 시작")
            thread.join()
            print("작업 쓰레드 join() 완료")
        

def main(argv):
    start_server()

if __name__ == '__main__':
    app.run(main)