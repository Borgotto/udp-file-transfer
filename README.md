# udp-file-transfer

Basic client-server architecture to transfer files via UDP protocol.

Made specifically for the network programming course I'm taking

##

### Usage:
first, start the server:
```python server.py```

then, start the client specifying the server ip:
```python client.py <server_ip>```

now on the client side, you can use these commands:

- list the files on the server:
```list```
- get a file from the server:
```get <filename>```
- send a file to the server:
```put <filename>```

the server will log the activity to standard output
then respond with the status of the operation, which is either
```protocol.response.encode_func``` or ```protocol.ERROR```

##

### Protocol documentation:

the protocol.py file contains the protocol specification, notably the ```Command``` and ```CommandError``` classes/exceptions;

it also contains the ```make_packets``` and ```read_packets``` functions, which are used to encode and decodes the packets sent and received.
these functions also verify the integrity of the packets, and raise a ```CommandError``` exception if the packets are corrupted.;

then it defines ```commands/responses``` and their associated functions, which are used to execute the commands;
more ```commands/responses``` can be added by adding ```Command``` objects to the ```commands/responses``` dictionaries;
