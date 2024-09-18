import sys
from Server import requests
from Client.ClientSockClass import *
from DB import utils


MAX_SIZE_TRANSFER = 64
ENCOD = 'utf-8'
FAIL_CONNEXION = "erro de conexao"
TOKEN_NOT_DEFINED = "Usuario nao conectado"


def send_request(request, client:ClientSocket):

    if client.connect():
        size_transfer = str(len(request)).encode(requests.ConstantsManagement.FORMAT.value)
        size_transfer += b' ' * (requests.ConstantsManagement.MAX_PKT_SIZE.value - len(size_transfer))
        client.client_socket.settimeout(5)
        try:
            client.client_socket.send(size_transfer)
            client.client_socket.send(request.encode(requests.ConstantsManagement.FORMAT))
            size_transfer = client.client_socket.recv(requests.ConstantsManagement.MAX_PKT_SIZE)
            response_str = client.client_socket.recv(int(size_transfer.decode(requests.ConstantsManagement.FORMAT))).decode(requests.ConstantsManagement.FORMAT)
            server_response = requests.Response()
            server_response.from_json(response_str)
            response = server_response

        except socket.error as e:
            response = requests.Response(data={'execpt':str(e)}, rs_type=requests.ConstantsManagement.NETWORK_FAIL, status=requests.ConstantsManagement.NETWORK_ERROR)
            print(str(e))
        client.end()
    else:
        response = requests.Response()
    return response


def buying(routes, client:ClientSocket):
    if client.token == '':
        return  0, TOKEN_NOT_DEFINED

    buy_request = requests.Request(client_token=client.token, rq_data=[], rq_type=requests.ConstantsManagement.BUY)

    for fligth in routes:
        route = utils.Route()
        route.from_string(fligth)
        buy_request.rq_data.append(route.id)

    response = send_request(buy_request.to_json(), client)

    return response.status, response.data

def connect(email, client:ClientSocket):
    connect_request = requests.Request(rq_data=email, rq_type=requests.ConstantsManagement.GETTOKEN)
    response = send_request(connect_request.to_json(), client)

    return response.status, response.data


def search_routes(match, destination, client:ClientSocket):
    route_request = requests.Request(client_token=client.token, rq_type=requests.ConstantsManagement.GETROUTES, rq_data={'match':match, 'destination':destination})
    response = send_request(route_request.to_json(), client)
    return response.status, response.data


def create_account(email, client:ClientSocket):
    create_account_request = requests.Request(rq_type=requests.ConstantsManagement.CREATE_USER, rq_data=email)
    response = send_request(create_account_request.to_json(), client)

    return response.status, response.data

def search_bougths(client:ClientSocket):
    if client.token == '':
        return  0, TOKEN_NOT_DEFINED

    bougths_request = requests.Request(client_token=client.token, rq_data=[], rq_type=requests.ConstantsManagement.GETTICKETS)

    response = send_request(bougths_request.to_json(), client)

    return response.status, response.data