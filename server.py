#!/usr/bin/env python3

import socket
import protocol

clients : "dict[tuple[str, int], list[bytes]]" = {}

# instantiating UPD socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind(('', protocol.SERVER_PORT))
    sock.settimeout(protocol.TIMEOUT_MAX)

    # starting the server
    print("server started - waiting for commands...")
    while True:
        try:
            # receive the packets
            address: "tuple[str, int]"
            while True:
                data, address = sock.recvfrom(protocol.PKT_SIZE)


                if address not in clients:
                    if len(clients) >= protocol.MAX_CLIENTS:
                        raise protocol.CommandError("max client connections reached")
                    clients[address] = [data]
                else:
                    clients[address].append(data)

                if not data or data.endswith(protocol.MSG_DEL):
                    break

            # convert the received packets into readable bytes
            received_bytes = protocol.read_packets(clients[address])


            # get the command from the received bytes
            command_name = received_bytes.split(protocol.CMD_DEL, 1)[0].decode("utf8")
            command = protocol.responses.get(command_name)
            if command is None:
                raise protocol.CommandError('invalid server command')

            # log client command
            print(address, command_name)

            # convert the received bytes to object
            received_obj = command.obj_from_bytes(received_bytes)

            # do something with the object and return response bytes
            bytes = command.obj_to_bytes(received_obj)

            # send all of the response divided in packets of PKT_SIZE bytes
            packets = protocol.make_packets(bytes)
            for packet in packets:
                sock.sendto(packet, address)

        # raised in case of protocol errors
        except protocol.CommandError as e:
            sock.sendto(e.bytes, address)

        except socket.timeout as e:
            pass

        except Exception as e:
            sock.sendto(protocol.CommandError("the server encountered and error: "+str(e)).bytes, address)

        finally:
            try:
                del clients[address] # remove client from list of peers
            except:
                pass
