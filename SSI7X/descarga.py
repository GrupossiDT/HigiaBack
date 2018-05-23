'''
    Se encarga de gestionar la descarga en formatos xlsx,csv,pdf
    @author: Robin
    @since:03-04-2018
    @summary: Clase para la gestion de descarga de archivos.
'''

import hashlib, socket, json,random  # @UnresolvedImport

#para generacion y gestion en xlsx
import pandas as pd # @UnresolvedImport
import io
#para generacion de pdf


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


    def text(self,data):
        parsed = json.loads(data)
        str_text_plain = ''
        count = 0
        header =''
        row0=''
        for key, obj in enumerate(parsed):
            for index,k in enumerate(obj):
                if count == 0:
                    header += str(k)+'\t'
                    row0 += str(obj[k]) + '\t'
                else:
                    str_text_plain += str(obj[k]) + '\t'

            if count==0:
                header+='\n'
                str_text_plain += header + row0+'\n'

            if count > 0:
                str_text_plain +='\n'
            count+=1

        response = make_response(str_text_plain)
        cd = 'attachment;filename=rpt.txt'
        response.headers['Content-Disposition'] = cd
        response.mimetype='text/plain'
        return response

    def xlsx(self,data):
        # Create a Pandas dataframe from the data.
        parsed = json.loads(data)
        df = pd.DataFrame(parsed)

        output = io.BytesIO()

        # Use the BytesIO object as the filehandle.
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        # Write the data frame to the BytesIO object.
        df.to_excel(writer, sheet_name='Sheet1')

        writer.save()
        xlsx_data = output.getvalue()
        response = make_response(xlsx_data)
        cd = 'attachment;filename=rpt.xlsx'
        response.headers['Content-Disposition'] = cd
        response.mimetype='application/vnd.ms-excel'
        return response


    def pdf(self,data):
        html="<h1>Hol</h1>"


        response = make_response(html)

        cd = 'attachment;filename=rpt.pdf'
        response.headers['Content-Disposition'] = cd
        response.mimetype='application/pdf'
        return response
