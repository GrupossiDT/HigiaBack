'''
Created on 23/01/2018

@author: EDISON.BEJARANO
'''

from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
from flask_restful import request, Resource
from wtforms import Form, validators, StringField , IntegerField
from ValidacionSeguridad import ValidacionSeguridad  # @UnresolvedImport
import Static.labels as labels # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.opciones_higia as optns  # @UnresolvedImport
import Static.config_DB as dbConf # @UnresolvedImport
import Static.config as conf  # @UnresolvedImport
import time,json,jwt
import datetime

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
                                    " ssi7x.tbperfiles a inner join  ssi7x.tbperfiles_une b on "\
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
            Cursor = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tbperfiles_une', 'id_prfl', "id="+ln_id_prfl_une)
            if Cursor :
                data        = json.loads(json.dumps(Cursor[0], indent=2))
                ln_id_prfl  = data['id_prfl']
                #Actualizo tabla principal
                arrayValues['cdgo']   = str(lc_cdgo)
                arrayValues['dscrpcn']= lc_dscrpcn
                arrayValues['estdo']=  lb_estdo
                lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str('tbperfiles'), arrayValues,'id ='+str(ln_id_prfl))
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

            ln_id_prfl_une = request.form["id_prfl_une"]
            ln_id_undd_ngco = request.form["id_undd_ngco"]

            strSql ="SELECT * FROM( "\
                    "SELECT m.dscrpcn as text,m.id as id_mnu,m.ordn,(case when p.id is not null then true else false end)::boolean as seleccionado  "\
                    "FROM (select m.dscrpcn,mg.id,m.ordn from ssi7x.tbmenu m "\
                    "inner join ssi7x.tbmenu_ge mg on m.id=mg.id_mnu  "\
                    "where mg.id_grpo_emprsrl=2 and m.estdo=true and mg.estdo=true  "\
                    ") AS M  "\
                    "left join  "\
                    "(select  "\
                    "m.dscrpcn,mng.id from ssi7x.tbperfiles as p  "\
                    "inner join ssi7x.tbperfiles_une as pu on pu.id_prfl= p.id  "\
                    "inner Join ssi7x.tbperfiles_une_menu as pum ON pu.id= pum.id_prfl_une  "\
                    "inner join ssi7x.tbmenu_ge mng ON pum.id_mnu_ge = mng.id  "\
                    "inner join ssi7x.tbmenu m ON m.id = mng.id_mnu  "\
                    "where pu.id="+ln_id_prfl_une+" and pu.id_undd_ngco="+ln_id_undd_ngco+" and mng.id_grpo_emprsrl = 2  "\
                    "and mng.estdo=true and m.estdo=true and pum.estdo=true"\
                    ")as P ON P.id=M.id "\
                    ") AS H order by CAST(H.ordn as integer)"
            print(strSql)
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
                #estdo: true, existe: true, id: 253, stdo_envdo: true
                if obj["existe"] :
                    if obj["stdo_envdo"] != obj["estdo"]:
                        #queryUpdate(table,objectValues,clause = NULL)
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
                        objectValues["id_lgn_crcn_ge"] = str(ln_id_prfl_une)
                        objectValues["id_lgn_mdfccn_ge"] = str(ln_id_prfl_une)
                        objectValues["fcha_mdfccn"] = str(datetime.datetime.now()).split('.')[0]
                        lc_cnctn.queryInsert("ssi7x.tbperfiles_une_menu",objectValues)
            '''
            if len(lc_query_actlzr) > 0:
                #print(lc_query_actlzr)
                lc_cnctn.queryFree(lc_query_actlzr)

            if len(lc_query_insrtr) > 0:
                #print(lc_query_insrtr)
                lc_cnctn.queryFree(lc_query_insrtr)
            '''
            return Utils.nice_json(data,200)

        else:
            return Utils.nice_json({labels.lbl_stts_success:errors.ERR_NO_ATRZCN},400)

    def datos_perfil(self,ln_id_perfil_une,ls_data,ln_id_grpo_emprsrl):
        lo_data=json.loads(ls_data)

        #Creo un array con todos los id_mnu provenientes del front
        l_id_mnu=[];
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
