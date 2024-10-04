#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <string.h>
#include <unistd.h>

#include <iostream>
#include <string>

using namespace std;

int main(){
    int s=socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP);
    if(s<0) return 1;

    //bind 하는 과정
    struct sockaddr_in serverAddr;
    memset(&serverAddr,0,sizeof(serverAddr));
    serverAddr.sin_family=AF_INET;
    serverAddr.sin_addr.s_addr=INADDR_ANY;
    serverAddr.sin_port=htons(10000+229);
    if(bind(s,(struct sockaddr *)&serverAddr,sizeof(serverAddr))<0){
        cerr<<strerror(errno)<<endl;
        return 0;
    }
    
    while(true){
        char buf[65536]; //받은 데이터 저장할곳
        struct  sockaddr_in sin;  
        memset(&sin,0,sizeof(sin));
        socklen_t sin_size=sizeof(sin);
        int numBytes=recvfrom(s,buf,sizeof(buf),0,(struct sockaddr *)&sin,&sin_size);
        cout<<"Recevied!: "<<numBytes<<endl;
        cout<<"From "<<inet_ntoa(sin.sin_addr)<<endl;

        //받은 데이터에 대한 응답 전송
        int numBytes2=sendto(s,buf,numBytes,0,(struct sockaddr *) &sin, sizeof(sin));
        cout << "Sent: "<<numBytes2<<endl;
    }
   
    close(s);
    return 0;
}