from sys import argv, stderr
from socket import getaddrinfo, socket
from socket import AF_INET, SOCK_STREAM, AI_ADDRCONFIG, AI_PASSIVE
from socket import IPPROTO_TCP, SOL_SOCKET, SO_REUSEADDR
from posix import abort
from os import fork
from os import listdir
from os.path import isfile, join
import config
from time import sleep

# TO-DO
# Implementar arquivo config.py OK
# Habilitar multiprocessos no server.py OK
# Colocar instruções e explicar o que (não) funcionou no relatório
# Comentar bem o código
# Entender bem toda a estrutura para a apresentação
# Verificar necessidade de (mais) tratamentos de erro/msgs de erro
# 

# CASO1: ARQUIVO FOI ESPECIFICADO E EXISTE
# CASO2: ARQUIVO FOI ESPECIDIFADO E NÃO EXISTE (404)
# CASO3: ARQUIVO NÃO FOI ESPECIFICADO E A LISTA NÃO ESTÁ VAZIA
# CASO4: ARQUIVO NÃO FOI ESPEFICIDADO E A LISTA ESTÁ VAZIA (404)

def getEnderecoHost(porta):
    try:
        enderecoHost = getaddrinfo(
            None,
            porta,
            family = AF_INET, # Tipo de família com a qual o socket se comunica. Nesse caso IPv4
            type = SOCK_STREAM, # Connection-based protocol do tipo TCP
            proto = IPPROTO_TCP, 
            flags = (AI_ADDRCONFIG | AI_PASSIVE) # Realiza query para IPV4 e não necessariamente para IPv6
        )   
    except:
        print("Não obtive informações sobre o servidor ", file = stderr)
        abort()
    return enderecoHost

def criaSocket(enderecoServidor):
    fd = socket(enderecoServidor[0][0], enderecoServidor[0][1]) #Realiza a criação do socket
    if not fd:
        print("Não foi possível criar o socket", file = stderr)
        abort()
    return fd

def setModo(fd):
    fd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # https://stackoverflow.com/questions/21515946/what-is-sol-socket-used-for
    return                                     

def bindaSocket(fd, porta): # Associa um endereço IP e uma porta a um socket (bound)
    try:
        fd.bind(('', porta))
    except:
        print("Erro ao dar bind no socket do servidor", porta, file = stderr)
        abort()
    return

def escuta(fd): # Faz com que o servidor passe a aceitar conexões (listen)
    try:
        fd.listen(0)
    except:
        print("Erro ao começar a escutar a porta", file = stderr)
        abort()
    print("Iniciando o serviço")
    return

def conecta(fd): # Aceita a conexão (pré-requisitos: bound e listen)
    (con, cliente) = fd.accept()
    print("Servidor conectado com ", cliente)
    return con

def fazTudo(fd):
    while True:
        buffer = fd.recv(1024).decode("utf-8") # Tam max 1024 bytes
        if not buffer:
            break
        print("==>", buffer)
        fd.send(bytearray(buffer, "utf-8")) # Envia dados. Retorna o número de bytes enviados
    print("Conexão terminada com", fd)
    fd.close()
    return

def connHandler(conn):
    extensao = ""   #Extensão do arquivo
    nomeArquivo = ""    #Nome do arquivo

    request = conn.recv(1024).decode('utf-8') # Recebe dados enviados pelo cliente

    print("==>", request)

    splittedRequest = request.split(" ")    # Separação da request para uma maior facilidade em saber o tipo da requisição, no caso um GET

    files = [f for f in listdir(config.dir) if isfile(join(config.dir, f))] #Pegar todos os arquivos que estão presentes no diretório

    if(splittedRequest[0] == "GET"):
        dir = splittedRequest[1]

        # Caso o arquivo seja especificado
        if(dir != "/"):
            # Possui extensão 
            if("." in dir):

                indiceBarra = dir.find("/")
                indicePonto = dir.find(".")

                #Separação da extensão e do nome do arquivo para serem mostrados no header
                extensao = dir[indicePonto + 1:]
                nomeArquivo = dir[indiceBarra + 1:indicePonto]

                arquivoComExtensao = nomeArquivo + "." + extensao

                # Caso o arquivo esteja disponível, realiza o envio dele
                if(arquivoComExtensao in files):
                    
                    # Identifica o contentType
                    imageTypes = ["jpeg", "jpg", "png", "gif"]

                    if(extensao in imageTypes):
                        contentType = "image"
                    else:
                        contentType = "text"

                    # Realiza envio do header
                    conn.send("HTTP/1.1 200 OK\r\n".encode())
                    conn.send("Server: Python-Based Server/1.0\r\n".encode()) # Inventei
                    conn.send(f"Content-Type: {contentType}/{extensao}\r\n\r\n".encode())
            
                    # Realiza envio do arquivo pedido
                    if(extensao in imageTypes):
                        file = open(f"arquivos/{arquivoComExtensao}", "rb")
                        fileContent = file.read()
                        conn.send(fileContent)
                        file.close()    
                    else:
                        file = open(f"arquivos/{arquivoComExtensao}")
                        fileContent = file.read()
                        conn.send(fileContent.encode())
                        file.close()

                # Caso o arquivo pedido não esteja disponível, retorna erro 404
                else:
                    # Realiza envio do header
                    conn.send("HTTP/1.1 404 Not Found\n".encode())
                    conn.send("Server: Python-Based Server/1.0\n".encode()) # Inventei
                    conn.send("Content-Type: text/html\n\n".encode())
                    
                    # Realiza envio do "Page Not Found"
                    file = open(config.pagErro)
                    fileContent = file.read()
                    conn.send(fileContent.encode())
                    file.close()
            
            # Não possui extensão alguma (não é arquivo)
            else:
                # Realiza envio do header
                conn.send("HTTP/1.1 404 Not Found\n".encode())
                conn.send("Server: Python-Based Server/1.0\n".encode()) # Inventei
                conn.send("Content-Type: text/html\n\n".encode())
                
                # Realiza envio do "Page Not Found"
                file = open(config.pagErro)
                fileContent = file.read()
                conn.send(fileContent.encode())
                file.close()

        # Arquivo não especificado, retorna primeiro item da lista
        else:
            # Caso a lista não esteja vazia
            if(len(config.listaDeArquivos) > 0):
                
                for arq in config.listaDeArquivos:
                    
                    indicePonto = arq.find(".")

                    extensao = arq[indicePonto + 1:]

                    nomeArquivo = arq[:indicePonto]

                    arqFound = False

                    # Identifica o contentType
                    if arq in files:

                        imageTypes = ["jpeg", "jpg", "png", "gif"]

                        if(extensao in imageTypes):
                            contentType = "image"
                        else:
                            contentType = "text"

                        # Realiza envio do header
                        conn.send("HTTP/1.1 200 OK\n".encode())
                        conn.send("Server: Python-Based Server/1.0\n".encode()) # Inventei
                        conn.send(f"Content-Type: {contentType}/{extensao}\n\n".encode())

                        # Realiza envio do arquivo pedido
                        if(extensao in imageTypes):
                            file = open(f"arquivos/{arq}", "rb")
                            fileContent = file.read()
                            conn.send(fileContent)
                        else:
                            file = open(f"arquivos/{arq}")
                            fileContent = file.read()
                            conn.send(fileContent.encode())
                        
                        file.close()

                        arqFound = True
                        break
                
                if not arqFound:
                    conn.send("HTTP/1.1 404 Not Found\r\n".encode())
                    conn.send("Server: Python-Based Server/1.0\r\n".encode()) # Inventei
                    conn.send(f"Content-Type: text/html\r\n\r\n".encode())

                    #Realiza envio do "Page Not Found"
                    file = open(config.pagErro)
                    fileContent = file.read()
                    conn.send(fileContent.encode())
                    file.close()

            # Caso a lista de arquivos esteja vazia
            else:
                # Realiza envio do header
                conn.send("HTTP/1.1 404 Not Found\r\n".encode())
                conn.send("Server: Python-Based Server/1.0\r\n".encode()) # Inventei
                conn.send(f"Content-Type: text/html\r\n\r\n".encode())

                #Realiza envio do "Page Not Found"
                file = open(config.pagErro)
                fileContent = file.read()
                conn.send(fileContent.encode())
                file.close()

    # Caso o método recebido não seja GET, encerra a conexão
    else: 
        print("Método não suportado. Conexão encerrada com", conn)
        return

    print("Conexão encerrada com", conn)
    return

def main():
    if len(argv) == 2:
        porta = int(argv[1])
    else:
        porta = config.porta
    enderecoHost = getEnderecoHost(porta)   #Pega o endereço do host através da função
    fd = criaSocket(enderecoHost)   # Realiza a criação do socket baseado no endereço do host
    setModo(fd)     #Controla o comportamento do socket
    bindaSocket(fd, porta)  
    print("Servidor pronto em", enderecoHost)
    escuta(fd)
    while True:
        conn = conecta(fd) # Aceita a conexão (fd) e retorna fd
        pid = fork()
        if pid == 0:    #Faz a criação de processos filhos para permitir a conexão de mais de um cliente simultaneamente
            connHandler(conn)
            #sleep(10) #Para testar várias abas abertas (vários clientes)
            conn.close()
        else:
            conn.close()
    return

if __name__ == '__main__':
    main()
