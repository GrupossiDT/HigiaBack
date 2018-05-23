import json
from flask import make_response
from user_agents import parse
from random import randint
from pysimplesoap.client import SoapClient

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

    def aleatoria_n_digitos(self,n):
        range_start = 10**(n-1)
        range_end = (10**n)-1
        return randint(range_start, range_end)

    def webServiceSMS(self,lc_url,ln_cllr,lc_sms,lc_lgn,lc_clve):
        client = SoapClient(wsdl=lc_url)
        getEnvioSMSResponse = client.getEnvioSMS(
            celular = ln_cllr,
            mensaje = lc_sms,
            login = lc_lgn,
            clave = lc_clve
        )

        return getEnvioSMSResponse['return']

