'''
    Se encarga de gestionar la descarga en formatos xlsx,csv,pdf
    @author: Robin
    @since:03-04-2018
    @summary: Clase para la gestion de descarga de archivos.
'''

import hashlib, socket, json,random  # @UnresolvedImport
from urllib.parse import urlparse

from IPy import IP
from flask import make_response  # @UnresolvedImpor
from flask_restful import request, Resource
import jwt  # @UnresolvedImport
from wtforms import Form, validators, StringField

from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Ldap_connect import Conexion_ldap  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
import Static.config as conf  # @UnresolvedImport
import Static.config_DB as dbConf  # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.labels as labels  # @UnresolvedImport
from ValidacionSeguridad import ValidacionSeguridad  # @UnresolvedImport

lc_cnctn = ConnectDB()
Utils = Utils()
validacionSeguridad = ValidacionSeguridad()

class Descarga():
    def csv(self,data,separador):
        parsed = json.loads(data)
        str_csv = ''
        count = 0
        header =''
        row0=''
        for key, obj in enumerate(parsed):
            for index,k in enumerate(obj):
                if count == 0:
                    header += str(k)+separador
                    row0 += str(obj[k]) + separador
                else:
                    str_csv += str(obj[k]) + separador

            if count==0:
                header+='\n'
                str_csv += header + row0+'\n'

            if count > 0:
                str_csv +='\n'
            count+=1

        response = make_response(str_csv)
        cd = 'attachment;filename=rpt.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype='text/csv'
        return response


    def xlsx(self):
        pass

    def pdf(self):
        pass
