import json
import sys

def main(argv):
    obj1={
        'name':'MJ Kim',
        'id':12345678,
    }

    # JSON 문자열로 serialize 하는 코드
    s=json.dumps(obj1)
    
    print(s)
    print('Type',type(s).__name__)

if __name__=='__main__':
    main(sys.argv)