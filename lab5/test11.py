import json
import sys

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
    # deserialize 하는 코드
    obj2=json.loads(s)
    print(obj2['name'],obj2['id'],obj2['work']['address'])
    print(obj1==obj2)

if __name__=='__main__':
    main(sys.argv)