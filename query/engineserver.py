import  socket, sys, threading, Queue, hashlib, functools, time, traceback
import uuid
from dbpool import readi, sendi
import filter
import pickle
import datasource
    
PORT = 7000
NWORKERS = 5
KEY = '<\xdbW\x1bv9A\x8a\xb1\xf6{\x0f\xd1nN\x9e'
#PASSBYTES = hashlib.md5(PASSPHRASE).digest()

def deserialize(engine, obj):
    if isinstance(obj, datasource.Concept):
        return engine.model.getConcept(obj)
    if type(obj) == str:
        return engine.model.getConcept(obj)
    if type(obj) in (list, tuple):
        return type(obj)(deserialize(engine, o) for o in obj)
    if type(obj) == dict:
        return dict((k, deserialize(engine, v)) for (k,v) in obj.iteritems())
    if isinstance(obj, filter.Filter):
        obj.concept = deserialize(engine, obj.concept)
    return obj
    

def RequestHandler(engine, request):
    print "engine: %r\nrequest:%r" % (engine, request)
    print `request`
    args, kargs = deserialize(engine, request)
    print `args`, `kargs`
    return engine.getList(*args, **kargs)

def readobj(conn):
    s = readi(conn)
    return pickle.loads(s)

def sendobj(conn, obj):
    s = pickle.dumps(obj)
    sendi(conn, s)

def hash(s):
    return hashlib.md5(KEY+s).digest()
    
def authenticateToServer(conn):
    challenge = readi(conn)
    response = hash(challenge)
    sendi(conn, response)

def authenticateClient(conn):
    challenge = uuid.uuid4().bytes
    sendi(conn, challenge)
    response = readi(conn)
    if hash(challenge) <> response:
        raise Exception("Access denied")

    
class WorkerThread(threading.Thread):
    def __init__(self, queue, handler):
        threading.Thread.__init__(self, name="Worker-%i" % id(self))
        self.queue = queue
        self.handler = handler
        self.stop = False
    def run(self):
        while not self.stop:
            try:
                conn = self.queue.get(True, .1)
            except Queue.Empty:
                if self.stop: return
                continue
            try:
                authenticateClient(conn)
                request = readobj(conn)
                print str(self), request
                result = self.handler(request)
                sendobj(conn, result)
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                sendobj(conn, e)
            finally:
                conn.close()
def serve(queue):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            s.bind(('127.0.0.1', PORT))
            break
        except Exception, e:
            if "Address already in use" in str(e):
                print "Waiting for port %i to become available" % PORT
                time.sleep(2)
            else:
                raise
    try:
        s.listen(1)
        print >>sys.stderr, ("Listening to port %i" % PORT)
        while True:
            conn, addr = s.accept()
            queue.put(conn)
    finally:
        try:
            s.close()
        except:
            pass

def createServer(engine, port=PORT, nworkers=NWORKERS):    
    requestq = Queue.Queue()
    h = functools.partial(RequestHandler, engine)
    for i in range(NWORKERS):
        WorkerThread(requestq, h).start()
    serve(requestq)