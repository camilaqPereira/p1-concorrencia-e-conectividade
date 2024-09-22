from enum import Enum
import socket
import json
import datetime
from DB.utils import *


##
#   @brief: Classe usada para o gerenciamento de constantes do protocolo
##
class ConstantsManagement(Enum):
    # Métodos de requisições
    BUY = "BUY"
    GETROUTES = "GETROUTES"
    CREATE_USER = "CREATEUSER"
    GETTOKEN = "GETTOKEN"
    GETTICKETS = "GETTICKETS"

    #Tipos de dados de retorno
    ROUTE_TYPE = "ROUTE"
    TICKET_TYPE = "TICKET"
    TOKEN_TYPE = "TOKEN"
    NO_DATA_TYPE = "NONE"
    NETWORK_FAIL = "NETWORK_FAIL"

    #Status
    OK = 100
    INVALID_TOKEN = 220
    OPERATION_FAILED = 240
    NOT_FOUND = 260
    NETWORK_ERROR = 280

    #Connection infos
    FORMAT = "utf-8" 
    MAX_PKT_SIZE = 64 #tamanho fixo do primeiro pacote em bytes
    DEFAULT_PORT = 8000
    HOST = socket.gethostbyname(socket.gethostname())


class Request:
    def __init__(self, rq_type: str = '', rq_data: any = None, client_token:str = ''):
        self.rq_type = rq_type
        self.rq_data = rq_data
        self.client_token = client_token

    def to_json(self):
        values = {"type":self.rq_type, "data":self.rq_data, "token":self.client_token}
        json_str = json.dumps(values)

        return json_str

    def from_json(self, json_str: str):
        values = json.loads(json_str)
        self.rq_type = values['type']
        self.rq_data = values['data']
        self.client_token = values['token']


class Response:
    def __init__(self, status = 0, data = None, rs_type = ''):
        self.timestamp = datetime.datetime.now()
        self.status = status
        self.data = data
        self.rs_type = rs_type

    def to_json(self):
        response = {'type':self.rs_type, 'timestamp':self.timestamp.strftime('%d/%m/%Y %H:%M:%S'), 'status':self.status, 'data':self.data}

        json_str = json.dumps(response)

        return json_str

    def from_json(self, json_str: str):
        response = json.loads(json_str)

        self.data = response['data']
        self.rs_type = response['type']
        self.timestamp = datetime.datetime.strptime(response['timestamp'], '%d/%m/%Y %H:%M:%S')
        self.status = response['status']


##
#   @brief: Classe utilizada para armazenar o gerenciamento de passagens/tickets
##
class Ticket:
    #Mutex para acessar o arquivo de tickets
    tickets_file_lock = Lock()

    def __init__(self, email:str='', routes = []):
        self.email = email
        self.timestamp:datetime.datetime = datetime.datetime.now()
        self.routes = routes

##
#   @brief: Realiza a leitura do arquivo de tickets
#
#   @return: dict carregado do arquivo json
#   @raises: FileNotFound caso o arquivo não seja encontrado 
##
    @classmethod
    def load_tickets(cls):
        with Ticket.tickets_file_lock:
            with open(FilePathsManagement.TICKETS_FILE_PATH.value, 'r') as file:
                all_tickets:dict = load(file)
        return all_tickets
        
#   @brief: Realiza a adição da instância ao arquivo de tickets
#
#   @return: True se a operação foi concluida. Caso contrário False
#   @raises: FileNotFound caso o arquivo não seja encontrado 
#            JSONDecodeError caso ocorra erros na leitura do arquivo
##        
    def save(self):
        data = {'timestamp': self.timestamp.strftime('%d/%m/%Y %H:%M:%S'), 'routes': self.routes}
        try:
            with Ticket.tickets_file_lock:
                with open(FilePathsManagement.TICKETS_FILE_PATH.value, 'r+') as file:
                    all_tickets:dict[str,list] = json.load(file)
                    if self.email in all_tickets:
                        all_tickets.get(self.email).append(data)
                    else:
                        all_tickets[self.email] = [data]
                    file.seek(0)
                    json.dump(all_tickets, file, indent=4)
            return True
        except FileNotFoundError:
            print(f'[SERVER] Error saving ticket! File not found')
            return False
        except json.JSONDecodeError:
            print(f'[SERVER] Error saving ticket! Tickets json file empty or invalid')

    def from_json(self, json_str):
        values = json.loads(json_str)
##
#   @brief: Realiza atualização dos atributos da instância por meio dos valores passados no dict
#
#   @param: dict contendos novos valores dos atributos
##
    def from_json(self, values):

        self.email = values['email']
        self.timestamp = datetime.datetime.strptime(values['timestamp'], '%d/%m/%Y %H:%M:%S')
        self.routes = values['routes']

##
#   @brief: Realiza a construção de um dict representativo da instância
#
#   @return: dict contendos os valores dos atributos da instância
##
    def to_json(self):
        json_str = {'email': self.email, 'timestamp':self.timestamp.strftime('%d/%m/%Y %H:%M:%S'), 'routes':self.routes}

        return json_str


