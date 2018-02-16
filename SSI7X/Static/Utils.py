import json
from flask import make_response
from user_agents import parse 
class Utils:
    def nice_json(self,arg, status):
        response = make_response(json.dumps(arg, sort_keys = True, indent=4), status)
        response.headers['Content-type'] = "application/json"
        response.headers['charset']="utf-8"
        return response
    
    '''
    Methodo que recibe string del agent y lo parsea retornando un objeto con la informacion del
    agente.
    '''
    def DetectarDispositivo(self,str_agente):
        dispositivo_usuario = parse(str_agente)
        return dispositivo_usuario