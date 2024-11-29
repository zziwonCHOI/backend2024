from http import HTTPStatus
import random
import requests
import json
import urllib
import mysql.connector
import string
import logging


from flask import abort, Flask, make_response, render_template, Response, redirect, request

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,  # 로깅 레벨 (DEBUG는 모든 로그를 출력)
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 콘솔에 로그 출력
        logging.FileHandler("app.log")  # 파일에 로그 저장
    ]
)
logger = logging.getLogger(__name__)

naver_client_id = "ZuJFqpkesPyg1E4mrIDF"
naver_client_secret = "LwVZHNpCiW"
naver_redirect_uri = "http://mylb-1575876311.ap-northeast-2.elb.amazonaws.com/auth"
user_id_map={}

def generate_random_string(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
db_config = {
    'host': '172.31.14.70',      # db서버 private ip
    'port':3306,
    'user': 'jw',               # MySQL 사용자
    'password': 'root',         # 비밀번호
    'database': 'memodb',       # 데이터베이스 이름
    'charset': 'utf8mb4',        # 문자셋 설정
}

def get_db_connection():
    """MySQL DB 연결"""
    connection = mysql.connector.connect(**db_config)
    if connection.is_connected():
        print('MySQL에 연결되었습니다.')
        cursor = connection.cursor()
        cursor.close()
        return connection
    else:
        raise Exception("MySQL에 연결할 수 없습니다.")


@app.route('/')
def home():
    # HTTP 세션 쿠키를 통해 이전에 로그인 한 적이 있는지를 확인한다.
    # 이 부분이 동작하기 위해서는 OAuth 에서 access token 을 얻어낸 뒤
    # user profile REST api 를 통해 유저 정보를 얻어낸 뒤 'userId' 라는 cookie 를 지정해야 된다.
    # (참고: 아래 onOAuthAuthorizationCodeRedirected() 마지막 부분 response.set_cookie('userId', user_id) 참고)
    userId = request.cookies.get('userId', default=None)
    print(userId)
    name = None

    ####################################################
    # TODO: 아래 부분을 채워 넣으시오.
    #       userId 로부터 DB 에서 사용자 이름을 얻어오는 코드를 여기에 작성해야 함
    if userId:
        # DB에서 userId로 사용자 이름을 조회
        try:
            conn = get_db_connection()  # DB 연결
            cursor = conn.cursor()
            # userId로 사용자 이름을 조회하는 SQL 쿼리
            query = "SELECT user_name FROM users WHERE user_id = %s"
            print(query)
            cursor.execute(query, (userId,))
            result = cursor.fetchone()
            print(f"result: {result}")
            if result:
                # 사용자 이름을 가져왔으면 name 변수에 저장
                name = result[0]
            else:
                # 사용자가 없으면 name은 None으로 유지
                name = "Unknown User"
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error occurred while fetching user data: {e}")
            


    ####################################################


    # 이제 클라에게 전송해 줄 index.html 을 생성한다.
    # template 로부터 받아와서 name 변수 값만 교체해준다.
    return render_template('index.html', name=name)


# 로그인 버튼을 누른 경우 이 API 를 호출한다.
# 브라우저가 호출할 URL 을 index.html 에 하드코딩하지 않고,
# 아래처럼 서버가 주는 URL 로 redirect 하는 것으로 처리한다.
# 이는 CORS (Cross-origin Resource Sharing) 처리에 도움이 되기도 한다.
#
# 주의! 아래 API 는 잘 동작하기 때문에 손대지 말 것
@app.route('/login')
def onLogin():
    params={
            'response_type': 'code',
            'client_id': naver_client_id,
            'redirect_uri': naver_redirect_uri,
            'state': random.randint(0, 10000)
        }
    urlencoded = urllib.parse.urlencode(params)
    url = f'https://nid.naver.com/oauth2.0/authorize?{urlencoded}'
    return redirect(url)


# 아래는 Authorization code 가 발급된 뒤 Redirect URI 를 통해 호출된다.
@app.route('/auth')
def onOAuthAuthorizationCodeRedirected():
    # TODO: 아래 1 ~ 4 를 채워 넣으시오.

    # 1. redirect uri 를 호출한 request 로부터 authorization code 와 state 정보를 얻어낸다.
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        abort(400)


    # 2. authorization code 로부터 access token 을 얻어내는 네이버 API 를 호출한다.
    token_url = 'https://nid.naver.com/oauth2.0/token'
    params = {
        'grant_type': 'authorization_code',
        'client_id': naver_client_id,
        'client_secret': naver_client_secret,
        'code': code,
        'state': state
    }
    response = requests.post(token_url, data=params)
    if response.status_code != 200:
        abort(500)

    token_data = response.json()
    access_token = token_data.get('access_token')
    if not access_token:
        abort(500)
    

    # 3. 얻어낸 access token 을 이용해서 프로필 정보를 반환하는 API 를 호출하고,
    #    유저의 고유 식별 번호를 얻어낸다.
    profile_url = 'https://openapi.naver.com/v1/nid/me'
    headers = {'Authorization': f'Bearer {access_token}'}
    profileresponse = requests.get(profile_url, headers=headers)
    if profileresponse.status_code != 200:
        abort(500)

    user_info=profileresponse.json()
    logger.info(f"데이터: {user_info}")
    response=user_info.get('response',{})
    user_id = response['id']
    user_name = user_info['response']['name']
    print(user_name)
    if not user_id or not user_name:
        abort(500)

    # 4. 얻어낸 user id 와 name 을 DB 에 저장한다.
    cookie_key = generate_random_string()
    conn = get_db_connection()
    cursor = conn.cursor()

    # user_id가 이미 존재하는지 확인
    check_query = "SELECT id FROM users WHERE user_id = %s"
    cursor.execute(check_query, (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        # 이미 존재하면 업데이트
        update_query = """
        UPDATE users SET user_name = %s, cookie_key = %s WHERE user_id = %s
        """
        cursor.execute(update_query, (user_name, cookie_key, user_id))
    else:
        # 존재하지 않으면 새로 추가
        insert_query = """
        INSERT INTO users (user_id, user_name, cookie_key)
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (user_id, user_name, cookie_key))
        print(f"확인: {user_name}")
    conn.commit()

    cursor.close()
    conn.close()

    user_id_map[cookie_key]=user_id
    # 5. 첫 페이지로 redirect 하는데 로그인 쿠키를 설정하고 보내준다.
    #    user_id 쿠키는 "dkmoon" 처럼 정말 user id 를 바로 집어 넣는 것이 아니다.
    #    그렇게 바로 user id 를 보낼 경우 정보가 노출되기 때문이다.
    #    대신 user_id cookie map 을 두고, random string -> user_id 형태로 맵핑을 관리한다.
    #      예: user_id_map = {}
    #          key = random string 으로 얻어낸 a1f22bc347ba3 이런 문자열
    #          user_id_map[key] = real_user_id
    #          user_id = key
    response = redirect('/')
    response.set_cookie('userId', cookie_key)
    return response


@app.route('/memo', methods=['GET'])
def get_memos():
    # 로그인이 안되어 있다면 로그인 하도록 첫 페이지로 redirect 해준다.
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    # TODO: DB 에서 해당 userId 의 메모들을 읽어오도록 아래를 수정한다.
    try:
        conn = get_db_connection()  # DB 연결
        cursor = conn.cursor()

        # userId로 메모를 조회하는 SQL 쿼리
        query = "SELECT id, content FROM memos WHERE user_id = %s"
        cursor.execute(query, (userId,))
        memos = cursor.fetchall()  # 결과를 가져옴
        print(memos)
        # 가져온 메모 목록을 JSON 형태로 변환
        result = [{"id": memo[0], "content": memo[1]} for memo in memos]

        cursor.close()
        conn.close()

        # 메모 목록을 클라이언트에 반환
        return {'memos': result}
    
    except Exception as e:
        print(f"Error occurred while fetching memos: {e}")
        abort(500)


@app.route('/memo', methods=['POST'])
def post_new_memo():
    # 로그인이 안되어 있다면 로그인 하도록 첫 페이지로 redirect 해준다.
    userId = request.cookies.get('userId', default=None)
    if not userId:
        return redirect('/')

    # 클라이언트로부터 JSON 을 받았어야 한다.
    if not request.is_json:
        abort(HTTPStatus.BAD_REQUEST)

    # TODO: 클라이언트로부터 받은 JSON 에서 메모 내용을 추출한 후 DB에 userId 의 메모로 추가한다.
     # 클라이언트에서 보낸 JSON 데이터를 파싱
    data = request.get_json()
    memo_content = data.get('text', None)
    print(memo_content)
    if not memo_content:
        abort(HTTPStatus.BAD_REQUEST)

    try:
        conn = get_db_connection()  # DB 연결
        cursor = conn.cursor()

        # 새로운 메모를 DB에 추가하는 SQL 쿼리
        query = "INSERT INTO memos (user_id, content) VALUES (%s, %s)"
        cursor.execute(query, (userId, memo_content))
        conn.commit()  # 변경사항 저장

        cursor.close()
        conn.close()

        # 성공적으로 메모가 추가되었으면 HTTP OK 반환
        return '', HTTPStatus.OK
    
    except Exception as e:
        print(f"Error occurred while adding memo: {e}")
        abort(500)

if __name__ == '__main__':
    app.run('0.0.0.0', port=10229, debug=True)