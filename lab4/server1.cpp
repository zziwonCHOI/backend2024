#include <arpa/inet.h>
#include <errno.h>
#include <string.h>
#include <sys/socket.h>

#include <unistd.h>
#include <iostream>
using namespace std;

int main(){
    //서버 소켓 생성
    int passiveSock=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);

    struct sockaddr_in sin;
    memset(&sin,0,sizeof(sin));
    sin.sin_family=AF_INET;
    sin.sin_addr.s_addr=INADDR_ANY; //서버가 모든 네트워크 인터페이스에서 오는 연결을 수신하도록
    sin.sin_port=htons(10000+229);

    //소켓에 주소정보 바인딩
    if(bind(passiveSock,(struct sockaddr *)&sin,sizeof(sin))<0){
        cerr<<"bind() failed: "<<strerror(errno)<<endl;
        return 1;
    }
    //서버 소켓을 수시 대기 상태로 설정 하면서 대기 중인 연결을 처리할 수 있는 큐의 크기를 10개로 지정
    if(listen(passiveSock,10)<0){
        cerr<<"listen() failed: "<<strerror(errno)<<endl;
        return 1;
    }

    //대기중인 클라이언트 연결 수락하고, 새로운 소켓 clientSocket 생성
    memset(&sin,0,sizeof(sin));//다시 구조체 초기화
    unsigned int sin_len=sizeof(sin);
    //연결된 클라이언트 통신은 이 새로운 소켓을 통해 이루어진다. (acctive socket)
    int clientSock=accept(passiveSock,(struct sockaddr *)&sin, &sin_len);
    if(clientSock<0){
        cerr<<"accept() failed: "<<strerror(errno)<<endl;
        return 1;
    }
    
    //클라이언트로부터 데이터 수신
    char buf[65536];
    int numRecv=recv(clientSock,buf,sizeof(buf),0);
    if(numRecv==0){
        cout<<"Socket closed: "<<clientSock<<endl;
    }else if(numRecv<0){
        cerr<<"recv() failed: "<<strerror(errno)<<endl;
    }else{
        cout<<"Recevied: "<<numRecv<<"bytes, clientSock"<<clientSock<<endl;
    }

    //수신 데이터를 클라이언트로 다시 전송
    int offset=0; //데이터를 전송한 바이트 수를 추적하여 남은 데이터를 전송하는데 사용
    //send()는 한번에 전송할 수 있는 데이터양이 제한될 수 있으므로, 남은 데이터가 있을 경우 offset을 업데이트하며 반복 전송
    while(offset<numRecv){
        int numSend=send(clientSock,buf+offset,numRecv-offset,0);
        if(numSend<0){
            cerr<<"send() failed: "<<strerror(errno)<<endl;
        }else{
            cout<<"Sent: "<<numSend<<endl;
            offset+=numSend;
        }
    }
    close(clientSock);
    close(passiveSock);
}