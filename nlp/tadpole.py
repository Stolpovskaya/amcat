#!/usr/bin/python
#by Wouter van Atteveldt (adapted from Maarten van Gompel, who adapted it from code by Rogier Kraf), licensed under GPLv3

from socket import *
import re
import lemmata


TADPOLE_POSMAP = {"VZ" : "P",
                  "N" : "N",
                  "ADJ" : "A",
                  "LET" : ".",
                  "VNW" : "O",
                  "LID" : "D",
                  "SPEC" : "M",
                  "TW" : "Q",
                  "WW" : "V",
                  "BW" : "B",
                  "VG" : "C",
                  "TSW" : "I",
                  "MWU" : "U"
                  }
def TadpoleToken( position, word, lemma, morph, pos, *args):
    # *args catches stuff like dependency info which we ignore
    major, minor = token.pos.split("(")
    minor = minor.split(")")[0]
    pos = TADPOLE_POSMAP[major]
    return lemmata.Token(position-1, word, lemma, poscat, posmajor, posminor)

class TadpoleClient(object):
    def __init__(self,host="localhost",port="12345", tadpole_encoding="iso-8859-1", client_encoding="utf-8"):
        self.BUFSIZE = 1024
        self.socket = socket(AF_INET,SOCK_STREAM)
        self.socket.connect( (host,port) )
        self.tadpole_encoding = tadpole_encoding
        self.client_encoding = client_encoding

    def process(self, input_data):
        input_data = input_data.strip(' \t\n')
        if not isinstance(input_data, unicode):
            input_data = input_data.decode(self.client_encoding)
        self.socket.send(input_data.encode(self.tadpole_encoding) +'\n')

        buffer = ""
        done = False
        while not done:
            data = self.socket.recv(self.BUFSIZE).decode(self.tadpole_encoding)
            if not data: raise Exception("No data received but READY not given?")
            buffer += data

            # get completed lines from buffer, add last (incomplete?) line to buffer
            lines = buffer.split("\n")
            if buffer[-1] <> "\n":
                buffer = lines[-1]
                lines = lines[:-1]
            else:
                buffer = ""

            for line in lines:
                if line == "READY":
                    done = True
                elif line:
                    yield TadpoleToken(*line.split("\t"))

    def __del__(self):
        self.socket.close()

if __name__ == '__main__':
    import sys
    port = 12345
    host = "localhost"
    
    if len(sys.argv) <= 1:
        print >>sys.stderr, "Usage: python tadpoleclient [-pPORT] [-hHOST] SENTENCE"
        print >>sys.stderr, "If SENTENCE is "-", read input from STDIN"
        sys.exit()

    if sys.argv[1].startswith("-p"):
        port = int(sys.argv[1][2:])
        del sys.argv[1]
    if sys.argv[1].startswith("-h"):
        host = sys.argv[1][2:]
        del sys.argv[1]

    print >>sys.stderr, "Setting up connection with TadPole daemon at %s:%i" % (host, port)
    client = TadpoleClient(host, port)
    
    sentence = " ".join(sys.argv[1:])
    if sentence == "-":
        sentences = sys.stdin
        print >>sys.stderr, "Sending sentences from stdin"
    else:
        print >>sys.stderr, "Sending sentence %r" % sentence
        sentences = [sentence]

    for sentence in sentences:
        lagpos = None
        for token in client.process(sentence):
            if not lagpos or (token.position <> lagpos+1):
                print
            lagpos = token.position
            print token,