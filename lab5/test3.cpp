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
}

//protobuf의 직렬화는 객체를 바이트 시퀀스로 변환하여 저장하거나 전송할 수 있도록 해준다. 