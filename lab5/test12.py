import json
import sys
import socket

def main(argv):
    obj1={
        'name':'MJ Kim',
        'id':12345678,
        'work':{
            'name':'Myongji Unviversity',
            'address':'116 Myongji-ro'
        }
    }
    # JSON 문자열로 serialize 하는 코드
    s=json.dumps(obj1)

    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,0)
    sock.sendto(bytes(s,encoding='utf-8'),('127.0.0.1',10001))
    (data,sender)=sock.recvfrom(65536)

    # deserialize 하는 코드
    obj2=json.loads(data)
    print(obj2['name'],obj2['id'],obj2['work']['address'])
    print(obj1==obj2)

    sock.close()
    
if __name__=='__main__':
    main(sys.argv)