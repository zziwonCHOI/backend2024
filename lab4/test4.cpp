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
    // connect() 과정 없이 바로 send 하는 상황
    close(s);
   char buf[1024];
   int r=send(s,buf,sizeof(buf),MSG_NOSIGNAL);
   if(r<0){
    cerr<<"send() failed: "<<strerror(errno)<<endl; // 이 과정이 없으면 그냥 죽어버린다. 에러처리를 해주는 과정
   }else{
    cout<<"Sent: "<<r<<"bytes"<<endl;
   }
    close(s);
    return 0;
}