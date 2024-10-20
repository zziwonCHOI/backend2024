import sys
import threading

sum=0
m=threading.Lock()
cv=threading.condition(m)

def f():
    global sum
    for i in range(10*1000*1000):
        sum+=1
    m.aquire()
    cv.nofity()
    m.release()

def main(argv):
    t=threading.Thread(target=f)
    t.start()

    m.require()
    cv.wait()
    print('Sum',sum)
    m.release()

    t.join()

if __name__=='__main__':
    main(sys.argv)