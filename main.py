#!/usr/bin/env python
from twisted.internet import protocol, reactor
from json import loads, dumps, dump
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint, connectProtocol
from twisted.internet.task import LoopingCall
from subprocess import Popen, PIPE
import optparse
import psutil

serverInst = None
taskSender = None

def log(data):
    print(f"[-] {data}")

def getopts():
    parser = optparse.OptionParser("Process Netcat", version="% 0.1")
    parser.add_option("-c", "--client", dest="client", type="string", help="Address to connect to (client mode)")
    parser.add_option("-p", "--port", dest="port", type=int, default=1876, help="Port to connect to (client mode) or listen on (server mode)")
    parser.add_option("-w", "--whitelist", dest="whitelist", action="append", help="Whitelist of addresses to allow (server mode)")
    parser.add_option("-s", "--send", dest="send", action="store_true", default=False, help="We will send the PS output")
    parser.add_option("-f", "--file", dest="file", type="string", default="tasks.json", help="File to store JSON from tasks into")
    (options, args) = parser.parse_args()

    if options.client:
        if options.whitelist:
            log("WARNING - Using client mode but whitelist specified, ignoring")
        log(f"Starting up in client mode to {options.client}")
    else:
        log(f"Starting up in server mode on port {options.port}")
    return options


class ProcessNetcat(protocol.Protocol): # This is both a client and a server
    def connectionMade(self):
        self.addr = self.transport.getPeer()
        log(f"Connection: {self.addr.host}")
        if options.whitelist:
            if not self.addr.host in options.whitelist:
                log(f"Peer not whitelisted, dropping connection: {self.addr.host}")
                self.transport.loseConnection()

    def connectionLost(self, reason):
        global taskSender
        log(f"Connection lost: {self.addr.host}: {reason.getErrorMessage()}")
        if not taskSender == None:
            taskSender.stop() # Don't continue to try sending tasks if the connection isn't
            log(f"Ceasing task sending")
            taskSender = None

    def connectionFailed(self, reason):
        log(f"Connection failed: {self.addr.host}: {reason.getErrorMessage()}")

    def parse(self, data):
        if "type" in data.keys():
            dtype = data["type"]
        else:
            return

        if dtype == "hello":
            if not "send" in data.keys():
                return
            if data["send"] and options.send:
                msg = f"We're both sending PS output, please configure the -s flag only on one side"
                log(msg)
                self.send_err(msg)
            elif not data["send"] and not options.send:
                msg = f"Neither side is sending PS output, please configure the -s flag on one side"
                log(msg)
                self.send_err(msg)
            elif options.send:
                log(f"OK: We are sending PS")
                self.send_ok()
                self.send_tasks()

            elif data["send"]:
                log(f"OK: They are sending PS")
                self.send_ok()

        elif dtype == "tasks":
            if "tasks" in data.keys():
                log(f"Received tasks from {self.addr.host}")
                self.store_tasks(data["tasks"])

        elif dtype == "err":
            if not "msg" in data.keys():
                return
            log(f"Error from the other side: {data['msg']}")

        elif dtype == "ok":
            log("Received OK from server")
            if options.send:
                log("Starting PS transmission")
                self.send_tasks()

    def dataReceived(self, data):
        dataSplit = data.split(b"\r\n") # Allow multiple messages at once without getting confused
        for i in dataSplit:
            if not i == b"":
                toParse = loads(i)
                self.parse(toParse)

    def say(self, data):
        data += "\r\n"
        data = data.encode("utf-8", "replace")
        self.transport.write(data)

    def send_hello(self):
        hello = dumps({
            "type": "hello",
            "send": options.send}) # Tell the other server whether or not we expect to send
                                   #  PS output, so they can check if both or neither sides
                                   #  have it configured and let us know
        self.say(hello)
        return

    def send_ok(self): # Let the other side know all is okay, they can start transmitting if
        msg = dumps({  #  that is appropriate
            "type": "ok"})
        self.say(msg)
        return

    def send_err(self, msg):
        msg = dumps({
            "type": "err",
            "msg": msg})
        self.say(msg)
        return

    def send_tasks(self):
        global taskSender
        lc = LoopingCall(self._send_tasks)
        lc.start(5)
        taskSender = lc

    def _send_tasks(self):
        tasks = {}
        for i in psutil.process_iter():
            tasks[i.pid] = {
                    "name": i.name(),
                    "status": i.status(),
                    "created": i.create_time()}
        self.say(dumps({
            "type": "tasks",
            "tasks": tasks}))
        log(f"Sent tasks")

    def store_tasks(self, tasks):
        with open(options.file, "w") as f:
            dump(tasks, f, indent=4)

class ProcessNetcatFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return ProcessNetcat()

def gotProtocol(p):
    p.send_hello()

def startListener():
    global serverInst
    if options.client:
        point = TCP4ClientEndpoint(reactor, options.client, options.port)
        d = connectProtocol(point, ProcessNetcat())
        d.addCallback(gotProtocol)
    else:
        serverInst = ProcessNetcatFactory()
        endpoint = TCP4ServerEndpoint(reactor, options.port)
        endpoint.listen(serverInst)
    reactor.run()

if __name__ == "__main__":
    options = getopts()
    startListener()
