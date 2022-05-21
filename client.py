#!/usr/bin/env python3

import sys
import socket
import protocol

# get server ip through command args
try:
    address = (sys.argv[1], protocol.SERVER_PORT)
except IndexError:
    sys.exit("you need to specify the server ip to send commands to it")

# instantiating UPD socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.settimeout(protocol.TIMEOUT_MAX)

    # starting the client
    print("client started\ninput commands:")
    while True:
        try:
            # get input from user and convert it to a Command object
            user_input : str = input().strip()
            command = protocol.client_commands.get(next(iter(user_input.split()),''))
            if not command:
                raise protocol.CommandError("invalid client command")

            # convert the user input to bytes
            bytes = command.obj_to_bytes(user_input)

            # package bytes and send them to the server
            packets = protocol.make_packets(bytes)
            for packet in packets:
                sock.sendto(packet, address)

            # receive response packets
            received_packets = []
            while True:
                data, ret_addr = sock.recvfrom(protocol.PKT_SIZE)
                if ret_addr == address: received_packets.append(data)
                if not data or data.endswith(protocol.MSG_DEL): break

            # unpack the response into bytes
            received_bytes = protocol.read_packets(received_packets)

            # check the server's response for errors
            if received_bytes.startswith(protocol.ERROR):
                raise protocol.CommandError(received_bytes.split(protocol.ERROR,1)[1].decode("utf8"))
            if not received_bytes.startswith(command.name.encode()):
                raise protocol.CommandError("invalid response command")

            # do something with the response
            response_obj = command.obj_from_bytes(received_bytes)

        # raised in case of protocol errors
        except protocol.CommandError as e:
            print(e)

        except socket.timeout as e:
            print("command timed out")

        except KeyboardInterrupt:
            print("closing client")
            break
