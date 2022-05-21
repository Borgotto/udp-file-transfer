'''
protocol specifics can be found in the README file
packet structure example
MD5 + CMD_DEL + command + CMD_DEL + content + MSG_DEL
packets over 'PKT_SIZE' bytes will be split each with it's own PKT_NUM at the start
'''

import hashlib # used for MD5 hashing

# define static variables
PKT_SIZE = 512
PKT_NUM = lambda i: i.to_bytes(8,'big') # 32 bytes of PKT_NUM
CMD_DEL = b' /SEP/ '
MSG_DEL = b' /EOF/ \r\n/'
ERROR = b'ProtocolError' # special case of command/response
TIMEOUT_MAX = 10.0
MAX_CLIENTS = 2
SERVER_PORT = 4000
CRC = lambda bytes: hashlib.md5(bytes).hexdigest().encode()


class Command():
    '''
    class that defines a command to be sent via the network protocol

    - name: [str]
        command name
    - encode_func: [callable]
        function that encodes any objects to bytes ready to send
    - decode_func: [callable]
        function that decodes incoming bytes from the response
    '''
    def __init__(self,
                 name: str,
                 encode_func: callable,
                 decode_func: callable):
        self.name = name
        self._encode_func = encode_func
        self._decode_func = decode_func

    def obj_to_bytes(self, obj: any) -> bytes:
        '''convert the object passed to bytes ready to be packaged and sent'''
        return self._encode_func(obj)

    def obj_from_bytes(self, bytes: bytes) -> any:
        '''convert the received bytes to object'''
        return self._decode_func(bytes)

class CommandError(Exception):
    '''base class for Protocol Exceptions'''
    def __init__(self, message: str):
        self.message = message
        super().__init__(message[:PKT_SIZE-len((ERROR+MSG_DEL).decode("utf8"))])

    @property
    def bytes(self):
        return make_packets(ERROR+self.message.encode())[0]

def make_packets(bytes: bytes):
    '''takes bytes and returns a byte array with packets of PKT_SIZE each'''

    bytes = CRC(bytes) + CMD_DEL + bytes + MSG_DEL
    packets = []

    PKT_CONTENT_SIZE = PKT_SIZE-(len(PKT_NUM(0))+len(CMD_DEL))
    for i in range(0, len(bytes), PKT_CONTENT_SIZE):
        packets.append(PKT_NUM(int(i/PKT_CONTENT_SIZE))+CMD_DEL+bytes[i:i+PKT_CONTENT_SIZE])
    return packets

def read_packets(packets : "list[bytes]") -> bytes:
    '''takes packeted bytes and returns bytes'''

    sorted_packets = {}
    for packet in packets:
        sorted_packets[int.from_bytes(packet.split(CMD_DEL,1)[0],'big')] = packet.split(CMD_DEL,1)[1]
    bytes = b''.join(sorted_packets.values())[32+len(CMD_DEL):-len(MSG_DEL)]

    # check message CRC, raise exception if it fails, otherwise return the bytes
    if CRC(bytes) == sorted_packets[0][:32]:
        return bytes
    else:
        raise CommandError("checksum failed, packets got corrupted")


# commands utility functions
def list():
    '''returns list[str] representing the files of the current directory'''
    from os import listdir
    from os.path import isfile, join
    return [f for f in listdir() if isfile(join('', f))]

def bytes_to_file(bytes: bytes):
    '''given bytes in format "filename + CMD_DEL + content" it saves them to file'''
    try:
        filename = bytes.split(CMD_DEL, 1)[0].decode("utf8")
        with open(filename, "wb") as file:
            return file.write(bytes.split(CMD_DEL, 1)[1])
    except IOError:
        raise CommandError("could not write file "+filename)

def file_to_bytes(filename: str):
    '''given the file name it return bytes in format "filename + CMD_DEL + content"'''
    try:
        with open(filename, "rb") as file:
            return filename.encode() + CMD_DEL + file.read()
    except FileNotFoundError:
        raise CommandError("file not found "+filename)
    except IOError:
        raise CommandError("could not open file "+filename)


# define commands, clients and servers can have different commands
client_commands = {
    "list": Command("list",
                    lambda cmd_str: cmd_str.encode()+CMD_DEL,
                    lambda rec_bytes: print(rec_bytes.split(CMD_DEL,1)[1].decode("utf8"))),
    "get": Command("get",
                    lambda cmd_str: cmd_str.encode().replace(b" ",CMD_DEL,1),
                    lambda bytes: print(f"received {str(bytes_to_file(bytes.split(CMD_DEL,1)[1]))} bytes")),
    "put": Command("put",
                    lambda cmd_str: b'put'+CMD_DEL+file_to_bytes(cmd_str.split(' ',1)[1]),
                    lambda rec_bytes: print(f"sent {rec_bytes.split(CMD_DEL,1)[1].decode('utf8')} bytes"))
}

server_commands = {
    "list": Command("list",
                    lambda obj: b'list'+CMD_DEL+str(list()).encode(),
                    lambda rec_bytes: rec_bytes.decode("utf8")),
    "get": Command("get",
                    lambda filename: b'get'+CMD_DEL+file_to_bytes(filename),
                    lambda rec_bytes: rec_bytes.split(CMD_DEL,1)[1].decode("utf8")),
    "put": Command("put",
                    lambda bytes: b'put'+CMD_DEL+str(bytes_to_file(bytes)).encode(),
                    lambda rec_bytes: rec_bytes.split(CMD_DEL,1)[1])
}