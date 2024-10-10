#include <fstream>
#include <string>
#include <iostream>

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

    Person *p2=new Person;
    p2-> ParseFromString(s);
    cout<<"Name: "<<p2->name()<<endl;
    cout<<"ID: "<<p2->id()<<endl;
    for(int i=0;i<p2->phones_size();++i){
        cout<<"Type: "<<p2->phones(i).type()<<endl;
        cout<<"Phone: "<<p2->phones(i).number()<<endl;
    }
}

//protobuf는 endian을 고려해서 serialize/deserialize 하기 때문에 따로 htons()/htonl()할 필요 업ㅂㅅ다. 