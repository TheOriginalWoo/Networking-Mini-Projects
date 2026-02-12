<div align="center">

# Networking Mini Projects

</div>

Note:
> These are just small sketches i made while learning about these stuff so they ain't
> perfect and i don't plan to fix them either. Feel free to use these though.


## Current projects  
1. Echo server 
2. Dynamic http forwarder  
3. Https proxy  
4. Minimal Symmetric encryption client.
5. Minimal RSA encryption client.
  
### Echo Server 
* supports multiple clients
* supports bidirectional communication between client and server

### Dynamic Http Forwarder
* Can forward to any (probably) http web address

### Https Proxy
* A proxy that uses `http CONNECT` to proxy https traffic.

Note:  
> both `Dynamic Http Forwarder` and `Https Proxy` have Echo Server's features.  
  
### Minimal Symmetric Encryption Client.

* Two client 'chat' that uses AES symmetric encryption.  
* Used cryptography.Fernet for encryption.
* Didn't bother make this able to `recv` messages beyond the `BUFFER_SIZE`.
* Supports bidirectional communication.

### Minimal RSA Encryption Client.

* Similer to the one above.
* Also don't support messages beyond `BUFFER_SIZE`.
