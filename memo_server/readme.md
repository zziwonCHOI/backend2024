서버 접속
http://mylb-1575876311.ap-northeast-2.elb.amazonaws.com/memo/

로컬에서 구현은 됐지만 서비스 서버와 디비 서버 연결 부분에서 ssl 오류 해결을 못해 연결 하진 못했습니다.


디비 데이터베이스 구조
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,      
    user_id VARCHAR(255) NOT NULL,             
    user_name VARCHAR(255) NOT NULL,          
    cookie_key VARCHAR(255) NOT NULL UNIQUE,   
);CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci

ALTER TABLE users ADD UNIQUE (user_id);

CREATE TABLE memos (
    id INT AUTO_INCREMENT PRIMARY KEY,    
    user_id VARCHAR(255) NOT NULL, 
    content TEXT NOT NULL,                
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (user_id) REFERENCES users(user_id) 
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;


디비 연결
        host: '172.31.14.70',      # db서버 private ip
        port:3306,
        user: 'jw',               # MySQL 사용자
        password: 'root',         # 비밀번호
        database: 'memodb',       # 데이터베이스 이름
        charset: 'utf8mb4',        # 문자셋 설정