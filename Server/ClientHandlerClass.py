import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from hashlib import sha256
from Server.TicketClass import Ticket
from Server.ResponseClass import Response
from Server.utils import *
from Client.RequestsClass import Request
from DB.routes import *
import socket
from json import load, dump

class ClientHandler:

    def __init__(self, conn:socket, addr):  
        self.conn = conn
        self.addr = addr
    
    def __create_token(self, email):
        return sha256(email.encode(FORMAT)).hexdigest()

    def __load_users(self):
        try:
            with open(USERS_FILE_PATH, 'r') as file:
                users = load(file)
        except FileNotFoundError:
            users = {}
        return users
    def __get_user(self, token):
        users:dict = self.__load_users()

        for user, client_token in users.items():
            if client_token == token:
                return user
        return None

    def search_user(self, email=None):
        users:dict = self.__load_users()
        return users.get(email) 

    def validate_token(self, token = None):
        users:dict = self.__load_users()
        return True if (token in users.values()) else False
    
    def create_user(self, email: str):
        return_data = None

        if email and not self.search_user(email=email):
            token = self.__create_token(email)
            users:dict = self.__load_users()
            users[email] = token
            with open(USERS_FILE_PATH, 'w') as file:
                dump(users, file)
            
            return_data = (OK, token, TOKEN_TYPE)
        else:
            return_data = (OPERATION_FAILED, None, NO_DATA_TYPE)
        return return_data
            
    def get_token(self, email:str):
        users:dict = self.__load_users()
        token = users.get(email)
        return (OK, token, TOKEN_TYPE) if token else (NOT_FOUND, None, NO_DATA_TYPE)
    
    def find_routes(self, routes_graph: Graph, matches_and_destinations:list, flights:dict, match, destination):
        if match not in matches_and_destinations or destination not in matches_and_destinations:
            return_data = (NOT_FOUND, None, NO_DATA_TYPE)
        else:
            found_routes = search_route(routes_graph, matches_and_destinations, flights, match, destination)
            return_data = (OK, found_routes, ROUTE_TYPE) if found_routes[0] else (NOT_FOUND, None, NO_DATA_TYPE)
        return return_data
    def buy_routes(self, token, routes_graph:Graph, matches_and_destinations:list, flights:dict, routes:list):
        routes_keys = []
        #lock
        for item in routes: #verificando validade dos voos 
            flight_key = (matches_and_destinations.index(item[0]), matches_and_destinations.index(item[1]))
            if not flights[flight_key].sits:
                return (OPERATION_FAILED, None, NO_DATA_TYPE)
            routes_keys.append(flight_key)

        for item in routes_keys:
            flights[item].sits -= 1
            if not flights[item]:
                routes_graph.set_edge_weight(item[0], item[1], 9999)
                routes_graph.sparse_matrix[item[0], item[1], 9999]
            try:
                with open(ROUTES_DATA_FILE_PATH, 'w') as file:
                    serialized = {key: value.to_string() for key, value in flights}
                    dump(serialized, file) 
            except FileNotFoundError:
                print("[SERVER] Could not update the graph file! File doesn't exist")  
        #unlock
        ticket = Ticket(self.__get_user(token), routes)
        ticket.save()
        return (OK, ticket.to_json(), TICKET_TYPE)

            
    
    def get_tickets(self, token):
        try:
            with open(TICKETS_FILE_PATH, 'r') as file:
                all_tickets:dict = load(file)   
            email = self.__get_user(token)
            users_tickets = all_tickets.get(email)
        except FileNotFoundError:
            users_tickets = None
    
        return (OK, users_tickets, TICKET_TYPE) if users_tickets else (NOT_FOUND, None, NO_DATA_TYPE)


    def receive_pkt(self):
        pkt = Request()
        try:
            pkt_size = self.conn.recv(MAX_PKT_SIZE).decode(FORMAT)
            if pkt_size:
                pkt_size = int(pkt_size)
                #recebendo segundo pacote -> mensagem
                pkt.from_json(self.conn.recv(pkt_size).decode(FORMAT))
                print(pkt.rq_data)
        except socket.error as err:
            print(f"[SERVER] Package reception from {self.addr} failed! {str(err)}\n")
            pkt = None

        return pkt

    def send_pkt(self, return_values:tuple):
        status = False
        pkt = Response(return_values[0], return_values[1], return_values[2])
        pkt_json = pkt.to_json()
        try:
            pkt_len = str(len(pkt_json)).encode(FORMAT)
            pkt_len += b' ' * (MAX_PKT_SIZE - len(pkt_len))
            self.conn.send(pkt_len)
            self.conn.send(pkt_json.encode(FORMAT))
            status = True
        except socket.error as err:
            print(f"Package transfer to {self.addr} failed! {str(err)}\n")
        return status