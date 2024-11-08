#!/usr/bin/python3
from flask import Flask
from flask import request,make_response,jsonify
from http import HTTPStatus
app=Flask(__name__)

def calculate(arg1,op,arg2):
    arg1=int(arg1)
    arg2=int(arg2)
    if op== '+':
        return arg1+arg2
    elif op=='-':
        return arg1-arg2
    elif op=='*':
        return arg1*arg2
    else: 
        return None


@app.route('/<arg1>/<op>/<arg2>',methods=['GET'])
def calculate_get(arg1,op,arg2):
    result=calculate(arg1,op,arg2)
    if result is not None:
        response = make_response(f'result: {result}\n {HTTPStatus.OK} OK')
        return response
    else:
        response = make_response(f'error: Bad Request,{HTTPStatus.BAD_REQUEST}')
        return response


@app.route('/',methods=['POST'])
def calculate_post():
    data=request.get_json()
    if not data or 'arg1' not in data or 'op' not in data or 'arg2' not in data:
        response = make_response(f'error: Bad Request, {HTTPStatus.BAD_REQUEST}')
        return response
        
    
    arg1=data['arg1']
    op=data['op']
    arg2=data['arg2']

    result=calculate(arg1,op,arg2)
    if result is not None:
        response = make_response(f'result: {result}\n{HTTPStatus.OK} OK')
        return response
    else:
        response = make_response(f'error: Bad Request, {HTTPStatus.BAD_REQUEST}')
        return response

if __name__=='__main__':
    app.run(host='0.0.0.0',port=10229)