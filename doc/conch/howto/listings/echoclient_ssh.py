#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

if __name__ == '__main__':
    import sys
    import echoclient
    from twisted.internet.task import react
    react(echoclient.main, sys.argv[1:])

import os, getpass

from twisted.python.filepath import FilePath
from twisted.python.usage import Options
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Factory, Protocol
from twisted.conch.ssh.keys import EncryptedKeyError, Key
from twisted.conch.client.knownhosts import KnownHostsFile, ConsoleUI
from twisted.conch.endpoints import SSHCommandEndpoint

class EchoOptions(Options):
    optParameters = [
        ("host", "h", "localhost", "hostname of the SSH server to which to connect"),
        ("port", "p", 22, "port number of SSH server to which to connect", int),
        ("username", "u", getpass.getuser(), "username with which to authenticate with the SSH server"),
        ("identity", "i", "~/.ssh/id_rsa", "file from which to read a private key to use for authentication"),
        ("password", None, None, "password to use for authentication"),
        ("knownhosts", "k", "~/.ssh/known_hosts", "file containing known ssh server public key data"),
        ]



class NoiseProtocol(Protocol):
    def connectionMade(self):
        self.finished = Deferred()
        self.strings = ["bif", "pow", "zot"]
        self.sendNoise()


    def sendNoise(self):
        if self.strings:
            self.transport.write(self.strings.pop(0) + "\n")
        else:
            self.transport.loseConnection()


    def dataReceived(self, data):
        print "Server says:", data
        self.sendNoise()


    def connectionLost(self, reason):
        self.finished.callback(None)


def readKey(path):
    try:
        return Key.fromFile(path)
    except EncryptedKeyError:
        passphrase = getpass.getpass("%r keyphrase: " % (path,))
        return Key.fromFile(path, passphrase=passphrase)



def main(reactor, *argv):
    config = EchoOptions()
    config.parseOptions(argv)

    ui = ConsoleUI(lambda: open("/dev/tty", "r+"))

    keyPath = os.path.expanduser(config["identity"])
    if os.path.exists(keyPath):
        keys = [readKey(keyPath)]
    else:
        keys = []
    knownHostsPath = FilePath(os.path.expanduser(config["knownhosts"]))
    if knownHostsPath.exists():
        knownHosts = KnownHostsFile.fromPath(knownHostsPath)
    else:
        knownHosts = None

    endpoint = SSHCommandEndpoint(
        reactor,
        config["host"], config["port"],
        command="/bin/cat", username=config["username"],
        keys=keys, password=config["password"],
        knownHosts=knownHosts,
        ui=ui)

    factory = Factory()
    factory.protocol = NoiseProtocol

    d = endpoint.connect(factory)
    d.addCallback(lambda proto: proto.finished)
    return d

