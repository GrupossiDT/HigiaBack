'''
Created on 23/01/2018

@author: EDISON.BEJARANO
'''

import datetime
import time
import json
from flask_restful import request
from flask_restful import Resource
from pyasn1.type.univ import Null
from wtforms import Form
from wtforms import validators
from wtforms import StringField
from wtforms import IntegerField
from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
import Static.config_DB as dbConf  # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.labels as labels  # @UnresolvedImport
import Static.opciones_higia as optns  # @UnresolvedImport
from ValidacionSeguridad import ValidacionSeguridad  # @UnresolvedImport


#Declaracion de variables globales
Utils = Utils()
lc_cnctn = ConnectDB()
fecha_act = time.ctime()
#clase de llamado para validar datos desde labels
class DatosPerfil(Form):
    cdgo    = StringField(labels.lbl_cdgo_prfl,[validators.DataRequired(message=errors.ERR_NO_Cdgo)])
    dscrpcn = StringField(labels.lbl_dscrpcn_prfl,[validators.DataRequired(message=errors.ERR_NO_Dscrpcn)])

class DatosUpdate(Form):
    cdgo    = StringField(labels.lbl_cdgo_prfl,[validators.DataRequired(message=errors.ERR_NO_Cdgo)])
    dscrpcn = StringField(labels.lbl_dscrpcn_prfl,[validators.DataRequired(message=errors.ERR_NO_Dscrpcn)])
    id_prfl_une = IntegerField(labels.lbl_id_prfl,[validators.DataRequired(message=errors.ERR_NO_ID)])


class Datos_perfiles_sucursales_update(Form):
    id = IntegerField(labels.lbl_id_lgn_prfl_scrsl,[validators.DataRequired(message=errors.ERR_NO_ID)])
    id_undds_ngcio = IntegerField(labels.lbl_id_undds_ngcio,[validators.DataRequired(message=errors.ERR_NO_DTOS)])
    id_scrsl = IntegerField(labels.lbl_id_scrsl,[validators.DataRequired(message=errors.ERR_NO_DTOS)])
    id_prfl_une = IntegerField(labels.lbl_id_prfl,[validators.DataRequired(message=errors.ERR_NO_DTOS)])

class Datos_perfiles_sucursales_new(Form):
    id_undds_ngcio = IntegerField(labels.lbl_id_undds_ngcio,[validators.DataRequired(message=errors.ERR_NO_DTOS)])
    id_scrsl = IntegerField(labels.lbl_id_scrsl,[validators.DataRequired(message=errors.ERR_NO_DTOS)])
    id_prfl_une = IntegerField(labels.lbl_id_prfl,[validators.DataRequired(message=errors.ERR_NO_DTOS)])


class Perfiles(Resource):

    def post(self,**kwargs):

        if kwargs['page']=='crear':
            return self.crear()
        if kwargs['page']=='listar':
            return self.listar()
        if kwargs['page']=='actualizar':
            return self.actualizar()
        if kwargs['page']=='obtenerOpcionesperfil':
            return self.obtenerOpcionesPerfil()
        if kwargs['page']=='gestionPermisos':
            return self.gestionPermisos()
        if kwargs['page']=='perfiles_sucursales':
            return self.perfiles_sucursales()
        if kwargs['page']=='actualizar_perfiles_sucursales':
            return self.actualizar_perfiles_sucursales()
        if kwargs['page']=='crear_perfiles_sucursales':
            return self.crear_perfiles_sucursales()



    def crear(self):
        lob_rspsta = DatosPerfil(request.form)
        if not lob_rspsta.validate():
            return self.Utils.nice_json({labels.lbl_stts_error:lob_rspsta.errors},400)

        ln_opcn_mnu = request.form["id_mnu_ge"]
        ln_id_undd_ngco = request.form["id_undd_ngco"]
        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()

        if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
            token = validacionSeguridad.ValidacionToken(key)
            datosUsuario = validacionSeguridad.ObtenerDatosUsuario(token['lgn'])[0]
            arrayValues={}
            arrayValues['cdgo'] = request.form["cdgo"]
            arrayValues['dscrpcn'] = request.form["dscrpcn"]

            # validacion para evitar registros duplicados, se verifica que el codigo y la descripcion no existan en otros registros
            Cursor1 = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tbperfiles', 'cdgo', "cdgo='"+str(arrayValues['cdgo'])+"'")
            Cursor2 = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tbperfiles', 'dscrpcn', "dscrpcn ='"+ arrayValues['dscrpcn']+"'")

            if Cursor1 and Cursor2:
                return Utils.nice_json({labels.lbl_stts_error:labels.lbl_cdgo_prfl +"  "+ labels.lbl_dscrpcn_prfl+" "+errors.ERR_RGSTRO_RPTDO},400)
            if Cursor1 :
                return Utils.nice_json({labels.lbl_stts_error:labels.lbl_cdgo_prfl+" "+errors.ERR_RGSTRO_RPTDO},400)
            if Cursor2 :
                return Utils.nice_json({labels.lbl_stts_error:labels.lbl_dscrpcn_prfl+" "+errors.ERR_RGSTRO_RPTDO},400)


            ln_id_prfl =  lc_cnctn.queryInsert(dbConf.DB_SHMA+".tbperfiles", arrayValues,'id')

            if ln_id_prfl:
                arrayValuesDetalle={}
                arrayValuesDetalle['id_prfl'] = str(ln_id_prfl)
                arrayValuesDetalle['id_undd_ngco'] = str(ln_id_undd_ngco)
                arrayValuesDetalle['id_lgn_crcn_ge'] = str(datosUsuario['id_lgn_ge'])
                arrayValuesDetalle['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                arrayValuesDetalle['fcha_crcn'] = str(fecha_act)
                arrayValuesDetalle['fcha_mdfccn'] = str(fecha_act)
                ln_id_prfl_une = lc_cnctn.queryInsert(dbConf.DB_SHMA+".tbperfiles_une", arrayValuesDetalle,'id')
                return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_RGSTRO_EXTSO,"id":str(ln_id_prfl_une)},200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_PRBLMS_GRDR},400)
        else:
            return Utils.nice_json({labels.lbl_stts_success:errors.ERR_NO_ATRZCN},400)

    def listar(self):

        ln_opcn_mnu = request.form["id_mnu_ge"]
        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()

        if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
            lc_dta = ''
            lc_cdgo  =''
            try:
                lc_cdgo     = request.form["cdgo"]
                lc_dta = lc_dta +" and a.cdgo = '" + lc_cdgo +"' "
            except Exception:
                pass
            lc_dscrpcn = ''
            try:
                lc_dscrpcn  = request.form["dscrpcn"]
                lc_dta = lc_dta + "  and a.dscrpcn like '%" + lc_dscrpcn + "%' "
            except Exception:
                pass
            ln_id_undd_ngco = request.form["id_undd_ngco"]

            strSql = " select b.id, "\
                                    " a.cdgo ,a.dscrpcn "\
                                    " ,case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tbperfiles a inner join "+" "+str(dbConf.DB_SHMA)+".tbperfiles_une b on "\
                                    " a.id=b.id_prfl "\
                                    " where "\
                                    " b.id_undd_ngco = "+str(ln_id_undd_ngco) +" "+ lc_dta +""\
                                    " order by a.dscrpcn"
            Cursor = lc_cnctn.queryFree(strSql)

            if Cursor :
                data = json.loads(json.dumps(Cursor, indent=2))
                return Utils.nice_json(data,200)
            else:
                return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    def actualizar(self):

        lob_rspsta = DatosUpdate(request.form)
        if not lob_rspsta.validate():
            return self.Utils.nice_json({labels.lbl_stts_error:lob_rspsta.errors},400)

        ln_opcn_mnu = request.form["id_mnu_ge"]
        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()

        if validacionSeguridad.Principal(key, ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
            token = validacionSeguridad.ValidacionToken(key)
            datosUsuario = validacionSeguridad.ObtenerDatosUsuario(token['lgn'])[0]

            lc_cdgo         = request.form["cdgo"]
            lc_dscrpcn      = request.form["dscrpcn"]
            ln_id_prfl_une  = request.form["id_prfl_une"]
            lb_estdo        = request.form["estdo"]
            ln_id_undd_ngco = request.form['id_undd_ngco']

            lc_tbls_query = dbConf.DB_SHMA+".tbperfiles_une a INNER JOIN "+dbConf.DB_SHMA+".tbperfiles b on a.id_prfl=b.id "
            CursorValidar1 = lc_cnctn.querySelect(lc_tbls_query, ' b.id ', " a.id <>'"+str(ln_id_prfl_une)+"' and b.cdgo ='"+str(lc_cdgo)+"' and a.id_undd_ngco ='"+str(ln_id_undd_ngco)+"'")
            CursorValidar2 = lc_cnctn.querySelect(lc_tbls_query, ' b.id ', " a.id <>'"+str(ln_id_prfl_une)+"' and b.dscrpcn= '"+str(lc_dscrpcn)+"' and a.id_undd_ngco ='"+str(ln_id_undd_ngco)+"'")
            if CursorValidar1:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_RGSTRO_RPTDO},400)
            if CursorValidar2:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_RGSTRO_RPTDO},400)

            arrayValues={}
            arrayValuesDetalle={}
            #Actualizo tabla une
            arrayValuesDetalle['id_lgn_mdfccn_ge']  =  str(datosUsuario['id_lgn_ge'])
            arrayValuesDetalle['estdo']             =  lb_estdo
            arrayValuesDetalle['fcha_mdfccn']       =  str(fecha_act)
            lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str('tbperfiles_une'), arrayValuesDetalle,'id='+str(ln_id_prfl_une))
            #obtengo id_lgn a partir del id_lgn_ge
            Cursor = lc_cnctn.querySelect(str(dbConf.DB_SHMA) +'.tbperfiles_une', 'id_prfl', "id="+ln_id_prfl_une)
            if Cursor :
                data        = json.loads(json.dumps(Cursor[0], indent=2))
                ln_id_prfl  = data['id_prfl']
                #Actualizo tabla principal
                arrayValues['cdgo']   = str(lc_cdgo)
                arrayValues['dscrpcn']= lc_dscrpcn
                arrayValues['estdo']=  lb_estdo
                lc_cnctn.queryUpdate(str(dbConf.DB_SHMA)+"."+str('tbperfiles'), arrayValues,'id ='+str(ln_id_prfl))
                return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_ACTLZCN_EXTSA},200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_PRBLMS_GRDR},400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)
    '''
    '''
    def obtenerOpcionesPerfil(self):

        ln_opcn_mnu = request.form["id_mnu_ge"]
        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()

        if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
            token = validacionSeguridad.ValidacionToken(key)
            datosUsuario = validacionSeguridad.ObtenerDatosUsuario(token['lgn'])[0]
            ln_id_grpo_emprsrl = datosUsuario['id_grpo_emprsrl']

            ln_id_prfl_une = request.form["id_prfl_une"]
            ln_id_undd_ngco = request.form["id_undd_ngco"]


            strSql ="SELECT * FROM(   "\
                    "SELECT m.dscrpcn as text,p.lnk,m.id as id_mnu,m.ordn,p.id_prfl_une_mnu,(case when p.id is not null then true else false end)::boolean as seleccionado   "\
                    ",5 AS id_crar,  "\
                    "(select (case when ppm.id is null then false else ppm.estdo end) AS activo from ssi7x.tbpermisos AS prmss  "\
                    "left join ssi7x.tbpermisos_perfiles_menu AS ppm on ppm.id_prmso=prmss.id   "\
                    "where (ppm.id_prfl_une_mnu = p.id_prfl_une_mnu or ppm.id_prfl_une_mnu is null) and prmss.cdgo='01' ) as crar,   "\
                    "6 AS id_act,  "\
                    "(select (case when ppm.id is null then false else ppm.estdo end) AS activo from ssi7x.tbpermisos AS prmss  "\
                    "left join ssi7x.tbpermisos_perfiles_menu AS ppm on ppm.id_prmso=prmss.id   "\
                    "where (ppm.id_prfl_une_mnu = p.id_prfl_une_mnu or ppm.id_prfl_une_mnu is null) and prmss.cdgo='02' ) as actlzr,  "\
                    "7 AS id_anlr,  "\
                    "(select (case when ppm.id is null then false else ppm.estdo end) AS activo from ssi7x.tbpermisos AS prmss  "\
                    "left join ssi7x.tbpermisos_perfiles_menu AS ppm on ppm.id_prmso=prmss.id   "\
                    "where (ppm.id_prfl_une_mnu = p.id_prfl_une_mnu or ppm.id_prfl_une_mnu is null) and prmss.cdgo='03' ) as anlr,  "\
                    "8 AS id_imprmr,  "\
                    "(select (case when ppm.id is null then false else ppm.estdo end) AS activo from ssi7x.tbpermisos AS prmss  "\
                    "left join ssi7x.tbpermisos_perfiles_menu AS ppm on ppm.id_prmso=prmss.id   "\
                    "where (ppm.id_prfl_une_mnu = p.id_prfl_une_mnu or ppm.id_prfl_une_mnu is null) and prmss.cdgo='04' ) as imprmr,  "\
                    "9 AS id_exprtr,   "\
                    "(select (case when ppm.id is null then false else ppm.estdo end) AS activo from ssi7x.tbpermisos AS prmss  "\
                    "left join ssi7x.tbpermisos_perfiles_menu AS ppm on ppm.id_prmso=prmss.id   "\
                    "where (ppm.id_prfl_une_mnu = p.id_prfl_une_mnu or ppm.id_prfl_une_mnu is null) and prmss.cdgo='05' ) as exprtr  "\
                    "FROM (select m.dscrpcn,mg.id,m.ordn from ssi7x.tbmenu m   "\
                    "inner join ssi7x.tbmenu_ge mg on m.id=mg.id_mnu  "\
                    "where mg.id_grpo_emprsrl=2 and m.estdo=true and mg.estdo=true   "\
                    ") AS M   "\
                    "left join   "\
                    "(select    "\
                    "m.dscrpcn,mng.id,pum.id AS id_prfl_une_mnu,m.lnk from ssi7x.tbperfiles as p "\
                    "inner join ssi7x.tbperfiles_une as pu on pu.id_prfl= p.id  "\
                    "inner Join ssi7x.tbperfiles_une_menu as pum ON pu.id= pum.id_prfl_une   "\
                    "inner join ssi7x.tbmenu_ge mng ON pum.id_mnu_ge = mng.id "\
                    "inner join ssi7x.tbmenu m ON m.id = mng.id_mnu "\
                    "where pu.id = "+ln_id_prfl_une+" and pu.id_undd_ngco= "+ln_id_undd_ngco+" and mng.id_grpo_emprsrl = " + str(ln_id_grpo_emprsrl) + "  "\
                    "and mng.estdo=true and m.estdo=true and pum.estdo=true  "\
                    ")as P ON P.id=M.id   "\
                    ") AS H order by H.ordn"

            Cursor = lc_cnctn.queryFree(strSql)
            if Cursor :
                data = json.loads(json.dumps(Cursor, indent=2))
                return Utils.nice_json(data,200)
            else:
                return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    def gestionPermisos(self):

        ln_opcn_mnu = request.form["id_mnu_ge"]

        ln_id_undd_ngco = request.form["id_undd_ngco"]
        ln_id_prfl_une = request.form["id_perfil_une"]
        ls_data = request.form["ls_data"]
        ls_data_permisos = request.form["ls_data_permisos"]

        key = request.headers['Authorization']

        validacionSeguridad = ValidacionSeguridad()

        if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
            token = validacionSeguridad.ValidacionToken(key)
            datosUsuario = validacionSeguridad.ObtenerDatosUsuario(token['lgn'])[0]
            #Obtengo el cursor con todos los elementos de la consulta
            Cursor = self.datos_perfil(ln_id_prfl_une,ls_data,2)
            #Obtngo un array Json con las opciones de perfil
            data = json.loads(json.dumps(Cursor, indent=2))

            lc_query_actlzr = ""
            lc_query_insrtr = ""
            for obj in data:
                if obj["existe"] :
                    if obj["stdo_envdo"] != obj["estdo"]:
                        objectValues={}
                        objectValues["estdo"] = str(obj["stdo_envdo"])
                        objectValues["id_lgn_mdfccn_ge"] = str(datosUsuario["id_lgn_ge"])
                        objectValues["fcha_mdfccn"]= str(datetime.datetime.now()).split('.')[0]
                        clause = "id_prfl_une = " + str(ln_id_prfl_une) + " AND id_mnu_ge=" + str(obj["id"])
                        lc_cnctn.queryUpdate("ssi7x.tbperfiles_une_menu",objectValues,clause)
                else:
                    if obj["stdo_envdo"]:
                        objectValues={}
                        objectValues["id_prfl_une"] = str(ln_id_prfl_une)
                        objectValues["id_mnu_ge"] = str(obj["id"])
                        objectValues["id_lgn_crcn_ge"] = str(datosUsuario['id_lgn_ge'])
                        objectValues["id_lgn_mdfccn_ge"] = str(datosUsuario['id_lgn_ge'])
                        objectValues["fcha_mdfccn"] = str(datetime.datetime.now()).split('.')[0]
                        lc_cnctn.queryInsert("ssi7x.tbperfiles_une_menu",objectValues)

            #TODO:verificar que el persmiso este activo.
            lo_data_permisos=json.loads(ls_data_permisos)

            for obj in lo_data_permisos:
                self.gestion_modos_acceso(obj,datosUsuario)

            return Utils.nice_json({labels.lbl_stts_success:"OK"},200)

        else:
            return Utils.nice_json({labels.lbl_stts_success:errors.ERR_NO_ATRZCN},400)

    def datos_perfil(self,ln_id_perfil_une,ls_data,ln_id_grpo_emprsrl):
        lo_data=json.loads(ls_data)

        #Creo un array con todos los id_mnu provenientes del front
        l_id_mnu=[]
        for obj in lo_data:
            l_id_mnu.append(str(obj["id_mnu"]))

        #Preparo un case para los valores enviados
        ls_case="(case"
        for obj in lo_data:
            ls_case += " when id=" +str(obj["id_mnu"]) + " then " + str(obj["seleccionado"])
        ls_case+=" end) as stdo_envdo"

        #Convierto el array en una cadena con los elementos del array separados por comas
        ls_id_mnu = ','.join(map(str, l_id_mnu))
        '''
        Es importante el orden tomando encuenta que primero seran los estados true,
        seguidos de los false y por ultimo los null.
        '''
        strSql="select enviados.id, "\
                "(case  when actuales.estdo is NULL then false else true end) existe, "\
                "actuales.estdo,enviados.stdo_envdo from "\
                "(select "+ str(ln_id_perfil_une)+" as id_prfl_une,id,"+ ls_case +" "\
                "from ssi7x.tbmenu_ge "\
                "where id in("+ls_id_mnu+") and id_grpo_emprsrl="+ str(ln_id_grpo_emprsrl)+""\
                "group by id "\
                ") AS enviados "\
                "left join "\
                "(select pum.id_prfl_une,pum.id_mnu_ge,pum.estdo from ssi7x.tbperfiles_une_menu pum "\
                "inner join ssi7x.tbperfiles_une pu on pu.id = pum.id_prfl_une "\
                "inner join ssi7x.tbmenu_ge mg on mg.id = pum.id_mnu_ge "\
                "where pum.id_mnu_ge in("+ls_id_mnu+") "\
                "and pum.id_prfl_une = "+ str(ln_id_perfil_une)+" "\
                "and mg.id_grpo_emprsrl="+ str(ln_id_grpo_emprsrl)+") as actuales "\
                "on actuales.id_mnu_ge=enviados.id "\
                "order by (case when actuales.estdo= true then 1 when actuales.estdo=false then 2 else 3 end) ASC,enviados.id ASC"
        Cursor = lc_cnctn.queryFree(strSql)
        return Cursor

    def gestion_modos_acceso(self,lo_data,usuario):

        #buscar si el permiso existe para el perfil.
        strSql ="select p.id as id_prmso, "+ str(lo_data["id_mnu"]) +" as id_mnu_ge_enviado, h.id_mnu_ge,h.id_prfl_une_mnu,"+ str(lo_data["id_prfl_une_mnu"]) +" as id_prfl_une_mnu_env , h.estdo_prfl_une_mnu, h.estdo_mnu_ge, "\
                "(case when h.id_prfl_une_mnu is not null then true else false end )::boolean as existe, h.estdo_prfl_une_mnu as estado,h.estdo_prmss_prfls_mnu "\
                "FROM(select "\
                "m.id as id_mnu, m.lnk,m.estdo as mnu_estdo,"\
                "mg.id as id_mnu_ge,"\
                "mg.estdo as estdo_mnu_ge,"\
                "pum.id as id_prfl_une_mnu,"\
                "pum.estdo as estdo_prfl_une_mnu,"\
                "ppm.estdo as estdo_prmss_prfls_mnu,"\
                "ppm.id as id_prmss_prfls_mnu,"\
                "ppm.id_prmso "\
                "from ssi7x.tbmenu as m "\
                "inner join ssi7x.tbmenu_ge mg on m.id = mg.id_mnu "\
                "inner join ssi7x.tbperfiles_une_menu as pum ON pum.id_mnu_ge=mg.id "\
                "inner join ssi7x.tbperfiles_une pu on pu.id = pum.id_prfl_une "\
                "inner join ssi7x.tbperfiles p on p.id=pu.id_prfl "\
                "left join ssi7x.tbpermisos_perfiles_menu ppm on ppm.id_prfl_une_mnu=pum.id "\
                "where (pum.id="+ str(lo_data["id_prfl_une_mnu"]) +" or pum.id is null))h "\
                "right join ssi7x.tbpermisos p on p.id = h.id_prmso"
        Cursor = lc_cnctn.queryFree(strSql)
        data = json.loads(json.dumps(Cursor, indent=2))
        for obj in data:
            ln_exste = False
            lc_permiso = None
            lc_estdo_envdo = None
            ln_id_perfil_une_mnu = None
            if lo_data["id_crar"] == obj["id_prmso"]:
                ln_exste = obj["existe"]
                lc_permiso = 5
                lc_estdo_envdo = lo_data["crar"]
                ln_id_perfil_une_mnu = obj["id_prfl_une_mnu"]
            elif lo_data["id_act"] == obj["id_prmso"]:
                ln_exste = obj["existe"]
                lc_permiso = 6
                lc_estdo_envdo = lo_data["actlzr"]
                ln_id_perfil_une_mnu = obj["id_prfl_une_mnu"]
            elif lo_data["id_anlr"] == obj["id_prmso"]:
                ln_exste = obj["existe"]
                lc_permiso = 7
                lc_estdo_envdo = lo_data["anlr"]
                ln_id_perfil_une_mnu = obj["id_prfl_une_mnu"]
            elif lo_data["id_imprmr"] == obj["id_prmso"]:
                ln_exste = obj["existe"]
                lc_permiso = 8
                lc_estdo_envdo = lo_data["imprmr"]
                ln_id_perfil_une_mnu = obj["id_prfl_une_mnu"]
            elif lo_data["id_exprtr"] == obj["id_prmso"]:
                ln_exste = obj["existe"]
                lc_permiso = 9
                lc_estdo_envdo = lo_data["exprtr"]
                ln_id_perfil_une_mnu = obj["id_prfl_une_mnu"]
                
            

            if ln_exste:

                if obj["estdo_prmss_prfls_mnu"] != lc_estdo_envdo:
                    objectValues={}
                    objectValues["estdo"] = str(lc_estdo_envdo)
                    objectValues["id_lgn_mdfccn_ge"] = str(usuario["id_lgn_ge"])
                    objectValues["fcha_mdfccn"] = str(datetime.datetime.now()).split('.')[0]

                    clause = "id_prmso="+ str(lc_permiso) +" and id_prfl_une_mnu="+ str(obj["id_prfl_une_mnu_env"])
                    ls_result_update =lc_cnctn.queryUpdate("ssi7x.tbpermisos_perfiles_menu",objectValues,clause)
            else:
                if lc_estdo_envdo == True:
                    objectValues={}
                    objectValues["estdo"] = str(lc_estdo_envdo)
                    objectValues["id_prmso"] = str( obj["id_prmso"])
                    objectValues["id_prfl_une_mnu"] = str(obj["id_prfl_une_mnu_env"])
                    objectValues["id_lgn_crcn_ge"] = str(usuario["id_lgn_ge"])
                    objectValues["id_lgn_mdfccn_ge"] = str(usuario["id_lgn_ge"])
                    objectValues["fcha_crcn"] = str(datetime.datetime.now()).split('.')[0]
                    objectValues["fcha_mdfccn"] = str(datetime.datetime.now()).split('.')[0]
                    lc_cnctn.queryInsert("ssi7x.tbpermisos_perfiles_menu",objectValues)

    def perfiles_sucursales(self):

        ln_id_lgn_ge = request.form["id_lgn_ge"]

        strSql ="select lgn_prfl_scrsl.id  as id_lgn_prfl_scrsl,"\
        "prfl.cdgo as cdgo_prfl,prfl.dscrpcn as dscrpcn_prfl,"\
        "lgn_prfl_scrsl.id_prfl_une as id_prfl_une,"\
        "case when lgn_prfl_scrsl.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo, "\
        "case when lgn_prfl_scrsl.mrca_scrsl_dfcto = true then 'ACTIVO' else 'INACTIVO' end as mrca_scrsl_dfcto, "\
        "scrsls.nmbre_scrsl as nmbre_scrsl, "\
        "lgn_prfl_scrsl.id_scrsl as id_scrsl, "\
        "lgn_prfl_scrsl.id_lgn_ge as id_lgn_ge, "\
        "lgn_prfl_scrsl.id_lgn_crcn_ge as id_lgn_crcn_ge, "\
        "lgn_prfl_scrsl.id_lgn_mdfccn_ge as id_lgn_mdfccn_ge, "\
        "lgn_prfl_scrsl.fcha_crcn::text as fcha_crcn, "\
        "lgn_prfl_scrsl.fcha_mdfccn::text as fcha_mdfccn, "\
        "undds_ngcio.nmbre_rzn_scl as undds_ngcio, "\
        "undds_ngcio.id as id_undds_ngcio, "\
        "lgn_prfl_scrsl.id_frma_pgo_dfcto_une as id_frma_pgo_dfcto_une, "\
        "lgn_prfl_scrsl.id_cnl_rcdo_dfcto_une as id_cnl_rcdo_dfcto_une, "\
        "lgn_prfl_scrsl.gdgt_sgmnto_trsldo as gdgt_sgmnto_trsldo,lgns.nmbre_usro, "\
        "lgn_prfl_scrsl.cntrl_cmprbnte as cntrl_cmprbnte, "\
        "lgn_prfl_scrsl.cntrl_cja_mnr as cntrl_cja_mnr, "\
        "lgn_prfl_scrsl.cntrl_atrzcn  as cntrl_atrzcn, "\
        "lgn_prfl_scrsl.mnto_rmblso_pac::text as mnto_rmblso_pac, "\
        "lgn_prfl_scrsl.gdgt_sgmnto_trsldo as gdgt_sgmnto_trsldo "\
        "from "\
        " "+str(dbConf.DB_SHMA)+".tblogins_perfiles_sucursales as lgn_prfl_scrsl    inner join "\
        " "+str(dbConf.DB_SHMA)+".tbperfiles_une as prfl_une "\
        "on lgn_prfl_scrsl.id_prfl_une = prfl_une.id    inner join "\
        " "+str(dbConf.DB_SHMA)+".tbperfiles as prfl "\
        "on prfl.id = prfl_une.id_prfl    inner join  "\
        " "+str(dbConf.DB_SHMA)+".tbsucursales as scrsls  "\
        "on scrsls.id = lgn_prfl_scrsl.id_scrsl    inner join  "\
        " "+str(dbConf.DB_SHMA)+".tbunidades_negocio as undds_ngcio "\
        "on undds_ngcio.id = scrsls.id_undd_ngco inner join "\
        " "+str(dbConf.DB_SHMA)+".tblogins_ge as lgns_ge   "\
        "on lgns_ge.id = lgn_prfl_scrsl.id_lgn_ge inner join "\
        " "+str(dbConf.DB_SHMA)+".tblogins as lgns  "\
        "on lgns_ge.id_lgn = lgns.id  "\
        "where lgn_prfl_scrsl.id_lgn_ge = "+str(ln_id_lgn_ge)+""\
         " order by prfl.dscrpcn "

        Cursor = lc_cnctn.queryFree(strSql)
        if Cursor :
            data = json.loads(json.dumps(Cursor, indent=2))
            return Utils.nice_json(data,200)
        else:
            return Utils.nice_json({labels.lbl_stts_success:labels.INFO_NO_DTS},200)

    def crear_perfiles_sucursales(self):
       
        lob_rspsta = Datos_perfiles_sucursales_new(request.form)
        if not lob_rspsta.validate():
            return Utils.nice_json({},400)
        
        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()
        token = validacionSeguridad.ValidacionToken(key)
        datosUsuario = validacionSeguridad.ObtenerDatosUsuario(token['lgn'])[0]
        arrayValues={}
                  
                  
        ln_id_lgn_ge=request.form["id_lgn_ge"]
        ln_id_scrsl=request.form["id_scrsl"]
        ln_id_prfl_une=request.form["id_prfl_une"]
        lb_mrca_scrsl_dfcto=request.form["mrca_scrsl_dfcto"]
        lb_estdo=request.form["estdo"]
        
        lb_cntrl_cmprbnte=request.form["cntrl_cmprbnte"]
        if lb_cntrl_cmprbnte =='':
            lb_cntrl_cmprbnte='false'
        
        lb_cntrl_cja_mnr=request.form["cntrl_cja_mnr"]
        if lb_cntrl_cja_mnr =='':
            lb_cntrl_cja_mnr='false'
        
        lb_cntrl_atrzcn=request.form["cntrl_atrzcn"]
        if lb_cntrl_atrzcn=='':
            lb_cntrl_atrzcn='false'       
        
        lb_gdgt_sgmnto_trsldo=request.form["gdgt_sgmnto_trsldo"]
        if lb_gdgt_sgmnto_trsldo =='':
            lb_gdgt_sgmnto_trsldo='false'
                        
        ln_mnto_rmblso_pac=request.form["mnto_rmblso_pac"]                                      
        ln_id_frma_pgo_dfcto_une = request.form["id_frma_pgo_dfcto_une"]
        ln_id_cnl_rcdo_dfcto_une=request.form["id_cnl_rcdo_dfcto_une"]
       
                          
        arrayValues['id_scrsl']=ln_id_scrsl
        arrayValues['id_lgn_ge']=ln_id_lgn_ge        
        arrayValues['id_prfl_une']=ln_id_prfl_une
        arrayValues['mrca_scrsl_dfcto']=lb_mrca_scrsl_dfcto
        arrayValues['estdo']= lb_estdo
        arrayValues['cntrl_cmprbnte']=lb_cntrl_cmprbnte
        arrayValues['cntrl_cja_mnr']=lb_cntrl_cja_mnr        
        if not ln_id_frma_pgo_dfcto_une == '0':
            arrayValues['id_frma_pgo_dfcto_une']=ln_id_frma_pgo_dfcto_une
        if not ln_id_cnl_rcdo_dfcto_une == '0':
            arrayValues['id_cnl_rcdo_dfcto_une']=ln_id_cnl_rcdo_dfcto_une        
        arrayValues['cntrl_atrzcn']=lb_cntrl_atrzcn
        arrayValues['gdgt_sgmnto_trsldo']=lb_gdgt_sgmnto_trsldo
        if not ln_mnto_rmblso_pac == '':
            arrayValues['mnto_rmblso_pac']=ln_mnto_rmblso_pac            
        arrayValues['id_lgn_crcn_ge']=str(datosUsuario['id_lgn_ge'])
        arrayValues['fcha_crcn']=str(fecha_act)
        arrayValues['id_lgn_mdfccn_ge']=str(datosUsuario['id_lgn_ge'])
        arrayValues['fcha_mdfccn']=str(fecha_act)
        
        id_lgn_prfl_scrsl =  lc_cnctn.queryInsert(dbConf.DB_SHMA+".tblogins_perfiles_sucursales", arrayValues,'id')      
        print(id_lgn_prfl_scrsl)
        if id_lgn_prfl_scrsl :
            return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_ACTLZCN_EXTSA,"id":str(id_lgn_prfl_scrsl)},200)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_PRBLMS_GRDR},400)

    def actualizar_perfiles_sucursales(self):
              
        lob_rspsta = Datos_perfiles_sucursales_update(request.form)
        if not lob_rspsta.validate():
            return self.Utils.nice_json({labels.lbl_stts_error:lob_rspsta.errors},400)

        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()
        token = validacionSeguridad.ValidacionToken(key)
        datosUsuario = validacionSeguridad.ObtenerDatosUsuario(token['lgn'])[0]

        ln_id=request.form["id"]
        ln_id_scrsl=request.form["id_scrsl"]
        ln_id_prfl_une=request.form["id_prfl_une"]
        lb_mrca_scrsl_dfcto=request.form["mrca_scrsl_dfcto"]
        lb_estdo=request.form["estdo"]
        lb_cntrl_cmprbnte=request.form["cntrl_cmprbnte"]
        lb_cntrl_cja_mnr=request.form["cntrl_cja_mnr"]
        ln_id_frma_pgo_dfcto_une=request.form["id_frma_pgo_dfcto_une"]
        
        if ln_id_frma_pgo_dfcto_une == '' or ln_id_frma_pgo_dfcto_une == '0':
            ln_id_frma_pgo_dfcto_une=None
        
        ln_id_cnl_rcdo_dfcto_une=request.form["id_cnl_rcdo_dfcto_une"]
        if ln_id_cnl_rcdo_dfcto_une=='' or  ln_id_cnl_rcdo_dfcto_une == '0':  
            ln_id_cnl_rcdo_dfcto_une=None
        
        ln_mnto_rmblso_pac=request.form["mnto_rmblso_pac"]    
        if ln_mnto_rmblso_pac == '' or ln_mnto_rmblso_pac == '0':
            ln_mnto_rmblso_pac=0 
                
        lb_cntrl_atrzcn=request.form["cntrl_atrzcn"]
        lb_gdgt_sgmnto_trsldo=request.form["gdgt_sgmnto_trsldo"]
        

        arrayValues={}

        arrayValues['id_scrsl']=ln_id_scrsl
        arrayValues['id_prfl_une']=ln_id_prfl_une
        arrayValues['mrca_scrsl_dfcto']=lb_mrca_scrsl_dfcto
        arrayValues['estdo']= lb_estdo
        arrayValues['cntrl_cmprbnte']=lb_cntrl_cmprbnte
        arrayValues['cntrl_cja_mnr']=lb_cntrl_cja_mnr
        arrayValues['id_frma_pgo_dfcto_une']=ln_id_frma_pgo_dfcto_une
        arrayValues['id_cnl_rcdo_dfcto_une']=ln_id_cnl_rcdo_dfcto_une
        arrayValues['cntrl_atrzcn']=lb_cntrl_atrzcn
        arrayValues['gdgt_sgmnto_trsldo']=lb_gdgt_sgmnto_trsldo
        arrayValues['mnto_rmblso_pac']=ln_mnto_rmblso_pac
        arrayValues['id_lgn_mdfccn_ge']=str(datosUsuario['id_lgn_ge'])
        arrayValues['fcha_mdfccn']=str(fecha_act)

        Cursor =  lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str('tblogins_perfiles_sucursales'), arrayValues,'id='+str(ln_id))
        if Cursor :
            return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_ACTLZCN_EXTSA},200)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_PRBLMS_GRDR},400)

    '''
    '''
