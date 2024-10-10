#include <fstream>
#include <string>
#include <iostream>
#include <unistd.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#include "person.pb.h"

using namespace std;
using namespace mju;

int main(){
    Person *p=new Person;
    p->set_name("MJ KIM");
    p->set_id(12345678);

    Person::PhoneNumber *phone= p->add_phones(); //PhoneNumber의 객체를 리스트에 추가
    phone->set_number("010-111-1234");
    phone->set_type(Person::MOBILE);
    
    phone = p->add_phones();
    phone->set_number("02-100-1000");
    phone->set_type(Person::HOME);

    const string s=p->SerializeAsString(); //객체를 직렬화 하여 string 타입으로 반환
    cout<<"Length: "<<s.length()<<endl;
    cout<<s<<endl;

    int soc=socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP);
    if(soc<0) return 1;

    string buf=s;
    struct sockaddr_in sin;
    memset(&sin,0,sizeof(sin));
    sin.sin_family=AF_INET;
    sin.sin_port=htons(10001);
    sin.sin_addr.s_addr=inet_addr("127.0.0.1");

    int numBytes=sendto(soc,buf.c_str(),buf.length(),0,(struct sockaddr *) &sin,sizeof(sin));
    cout<<"Sent: "<<numBytes<<endl<<endl;

    char buf2[65536];
    memset(&sin,0,sizeof(sin));
    socklen_t sin_size=sizeof(sin);
    numBytes=recvfrom(soc,buf2,sizeof(buf2),0,(struct sockaddr *) &sin,&sin_size);
    cout<<"Recevied: "<<numBytes<<endl;
    cout<<"From "<<inet_ntoa(sin.sin_addr)<<endl<<endl;
    //recvfrom 함수가 반환하는 데이터는 단순한 바이트 배열이기 때문에 string 타입으로 변환해준다.
    string recived(buf2,numBytes);

    Person *p2=new Person;
    p2-> ParseFromString(recived);
    cout<<"Name: "<<p2->name()<<endl;
    cout<<"ID: "<<p2->id()<<endl;
    for(int i=0;i<p2->phones_size();i++){
        cout<<"Type: "<<p2->phones(i).type()<<endl;
        cout<<"Phone: "<<p2->phones(i).number()<<endl;
    }
    close(soc);
}

//protobuf는 endian을 고려해서 serialize/deserialize 하기 때문에 따로 htons()/htonl()할 필요 업ㅂㅅ다. 