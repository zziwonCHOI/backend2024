#include <arpa/inet.h>
#include <errno.h>
#include <string.h>
#include <sys/socket.h>

#include <unistd.h>
#include <iostream>
using namespace std;

int main(){
    int s=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);
    if(s<0){
        cerr<<"socket() failed: "<<strerror(errno)<<endl;
        return 1;
    }
    
    struct sockaddr_in sin; //소켓의 주소 정보를 담는다. 
    memset(&sin,0,sizeof(sin)); //구조체를 0으로 초기화
    sin.sin_family=AF_INET;
    sin.sin_addr.s_addr=inet_addr("127.0.0.1");//ip 주소를 네트워크 바이트 오더로 변환
    sin.sin_port=htons(10000+229); //포트 번호 네트워크 바이트 오더로 변환
    if(connect(s,(struct sockaddr *) &sin, sizeof(sin))<0){
        cerr<<"connect() failed: "<<strerror(errno)<<endl;
        return 1;
    }
    char buf[1024];
    int r=send(s,buf,sizeof(buf),0);
    if(r<0){
        cerr<<"send() failed: "<<strerror(errno)<<endl; // 이 과정이 없으면 그냥 죽어버린다. 에러처리를 해주는 과정
    }else{
        cout<<"Sent: "<<r<<"bytes"<<endl;
    }
    //응답 받기
    r=recv(s,buf,sizeof(buf),0);
    if(r<0){
        cerr<<"recv() failed: "<<strerror(errno)<<endl;
    }else{
        cout<<"Recevied: "<<r<<"bytes"<<endl;
    }
    close(s);
    return 0;
}