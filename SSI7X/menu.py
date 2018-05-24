'''
Created on 02 feb. 2018

@author: luis.aragon
'''


import time, json, jwt

from flask_restful import request, Resource
from wtforms import Form, validators, StringField

from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
import Static.config as conf  # @UnresolvedImport
import Static.config_DB as dbConf  # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.labels as labels  # @UnresolvedImport
import Static.opciones_higia as optns  # @UnresolvedImport
from ValidacionSeguridad import ValidacionSeguridad  # @UnresolvedImport
from wtforms.fields.core import IntegerField

'''
    Declaracion de variables globales

'''

Utils = Utils()
validacionSeguridad = ValidacionSeguridad()
ld_fcha_actl = time.ctime()
Pconnection = ConnectDB()

'''
    class Acceso
    @author: Luis.aragon
    @since:02-02-2018
    @summary: Acceso a envio de campos para crear opcion menu
    @param Form: request.form
'''


class Acceso(Form):
    lc_ordn = StringField(labels.lbl_ordn, [validators.DataRequired(message=errors.ERR_NO_ORDN)])
    lc_dscrpcn = StringField(labels.lbl_prgnta, [validators.DataRequired(message=errors.ERR_NO_Dscrpcn)])
    ln_id_mnu = IntegerField(labels.lbl_id_mnu)
    lc_lnk = StringField(labels.lbl_lnk)

'''
    class ActualizarAcceso
    @author: luis.aragon
    @since:02-02-2018
    @summary: Acceso a envio de campos para actualizar opcion menu
    @param Form: request.form

'''


class ActualizarAcceso(Form):
    ln_id_mnu_ge = StringField(labels.lbl_id_mnu_ge, [validators.DataRequired(message=errors.ERR_NO_SN_PRMTRS)])
    lc_ordn = StringField(labels.lbl_ordn, [validators.DataRequired(message=errors.ERR_NO_ORDN)])
    lc_dscrpcn = StringField(labels.lbl_prgnta, [validators.DataRequired(message=errors.ERR_NO_Dscrpcn)])
    ln_id_mnu = IntegerField(labels.lbl_id_mnu)
    lc_lnk = StringField(labels.lbl_lnk)



'''
    class Menu
    @author: luis.aragon
    @since:02-02-2018
    @summary:Clase que contiene metodos de funcionalidades CRUD de opciones para el menu
    @param Form:Parametro Formulario que recibe recurso que provee la API
    @return:N/A,  no aplican parametros

'''


class Menu(Resource):
    '''
        def post
        @author: luis.aragon
        @since:02-02-2018
        @summary: metodo que retorna funcionalidad acorde a la ruta asociada
        @param Form:
        @return:retorna metodo de la ruta
    '''

    def post(self, **kwargs):

        if kwargs['page'] == 'listar':
            return self.listar()
        elif kwargs['page'] == 'crear':
            return self.crear()
        elif kwargs['page'] == 'actualizar':
            return self.actualizar()
        elif kwargs['page'] == 'agregar_favorito':
            return self.agregar_favorito()
        elif kwargs['page'] == 'remover_favorito':
            return self.remover_favorito()


    '''
        def crear
        @author: luis.aragon
        @since:02-02-2018
        @summary: metodo que permite crear una opcion para el menu, a partir de la autorizacion que contiene el headers del token y el permiso de la accion
        @param:
        @return:retorna Json del objeto creado

    '''

    def crear(self):
        key = request.headers['Authorization']
        ln_opcn_mnu = request.form["opt_id_mnu_ge"]
        ln_id_grpo_emprsrl = request.form["id_grpo_emprsrl"]
        if key:
            validacionSeguridad.ValidacionToken(key)
            if validacionSeguridad :
                token =Pconnection.querySelect(dbConf.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
                DatosUsuarioToken = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
                if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Optmenu']):
                    datosUsuario = validacionSeguridad.ObtenerDatosUsuario(DatosUsuarioToken['lgn'])[0]
                    arrayValues={}
                    if request.form["ln_parent"] == '':
                        arrayValues['id_mnu'] = str(0)
                    else:
                        arrayValues['id_mnu'] = request.form["ln_parent"]
                    arrayValues['ordn'] = request.form["lc_ordn"]
                    arrayValues['dscrpcn'] = request.form["lc_dscrpcn"]
                    arrayValues['lnk'] = request.form["lc_lnk"]
                    arrayValues['id_lgn_crcn_ge'] = str(datosUsuario['id_lgn_ge'])
                    arrayValues['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                    ln_id_mnu =  self.crearMenu(arrayValues,'tbmenu')
                    if ln_id_mnu:
                        arrayValuesDetalle={}
                        arrayValuesDetalle['id_mnu'] = str(ln_id_mnu)
                        arrayValuesDetalle['id_grpo_emprsrl'] = str(ln_id_grpo_emprsrl)
                        arrayValuesDetalle['id_lgn_crcn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValuesDetalle['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValuesDetalle['fcha_mdfccn'] = str(ld_fcha_actl)
                        ln_id_mnu_ge = self.crearMenu(arrayValuesDetalle,'tbmenu_ge')
                        return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_RGSTRO_EXTSO,"id":str(ln_id_mnu_ge)},200)
                    else:
                        return Utils.nice_json({labels.lbl_stts_error:errors.ERR_PRBLMS_GRDR},400)
                else:
                    return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_SSN}, 400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_PRMTRS}, 400)

    '''
        def actualizar
        @author: Luis.aragon
        @since:02-02-2018
        @summary: metodo que permite actualizar menu, a partir de la autorizacion que contiene el headers del token y el permiso de la accion
        @param:
        @return: status 200 actualizacion exitosa

    '''
    def actualizar(self):
        key = request.headers['Authorization']
        ln_opcn_mnu = request.form["opt_id_mnu_ge"]
        if key:
            validacionSeguridad.ValidacionToken(key)
            if validacionSeguridad :
                token =Pconnection.querySelect(dbConf.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
                DatosUsuarioToken = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
                if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Optmenu']):
                    datosUsuario = validacionSeguridad.ObtenerDatosUsuario(DatosUsuarioToken['lgn'])[0]
                    lb_estdo    = request.form["lb_estdo"]
                    a_menu_ge = {}
                    a_menu = {}
                    # Actualizo tabla ge
                    a_menu_ge['id'] = request.form['ln_id_mnu_ge']
                    a_menu_ge['fcha_mdfccn'] = str(ld_fcha_actl)
                    a_menu_ge['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                    if request.form["ln_parent"] == '':
                        a_menu['id_mnu'] = str(0)
                    else:
                        a_menu['id_mnu'] = request.form["ln_parent"]
                    Cursor = Pconnection.querySelect(dbConf.DB_SHMA +'.tbmenu_ge', 'id_mnu', "id="+a_menu_ge['id'])
                    if Cursor :
                        data  = json.loads(json.dumps(Cursor[0], indent=2))
                        ln_id_mnu  = data['id_mnu']
                        a_menu['id'] = ln_id_mnu
                        a_menu['ordn'] = request.form["lc_ordn"]
                        a_menu['dscrpcn'] = request.form["lc_dscrpcn"]
                        a_menu['lnk'] = request.form["lc_lnk"]
                        a_menu['estdo']=str(lb_estdo)
                        a_menu['fcha_mdfccn'] = str(ld_fcha_actl)
                        a_menu['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                        self.actualizarMenu(a_menu_ge, 'tbmenu_ge')
                        ln_id_mnu = self.actualizarMenu(a_menu, 'tbmenu')
                        if ln_id_mnu:
                            return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_ACTLZCN_EXTSA}, 200)
                        else:
                            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_PRBLMS_GRDR},400)
                else:
                    return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_SSN}, 400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_PRMTRS}, 400)

    '''
        def listar
        @author: Luis.aragon
        @since:02-02-2018
        @summary: metodo que permite listar preguntas de seguridad, a partir de la autorizacion que contiene el headers del token y el permiso de la accion
        @param:
        @return:retorna objetos listados

    '''

    def listar(self):
        ln_opcn_mnu = request.form["id_mnu_ge_opt"]
        ln_id_grpo_emprsrl = request.form["id_grpo_emprsrl"]
        key = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()
        lb_val = validacionSeguridad.Principal(key, ln_opcn_mnu, optns.OPCNS_MNU['Optmenu'])
        a_prmtrs = {}
        lc_prmtrs = ''
        try:
            a_prmtrs['ordn'] = request.form['ordn']
            lc_ordn = a_prmtrs['ordn']
            lc_prmtrs += "  and a.ordn like '%" + lc_ordn + "%'"
        except:
            pass
        try:
            a_prmtrs['dscrpcn'] = request.form['dscrpcn']
            lc_dscrpcn = a_prmtrs['dscrpcn']
            lc_prmtrs += "  and a.dscrpcn like '%" + lc_dscrpcn + "%' "
        except:
            pass

        try:
            a_prmtrs['id_mnu_ge'] = request.form['id_mnu_ge']
            ln_id_prgnta_ge = a_prmtrs['id_mnu_ge']
            lc_prmtrs += "  and b.id = '" + ln_id_prgnta_ge + "'"
        except:
            pass

        if lb_val:

            StrSql = " select "\
                                " a.id_mnu as parent,"\
                                " b.id,"\
                                " a.ordn,"\
                                " a.dscrpcn,"\
                                "a.lnk,"\
                                " case when a.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo"\
                                " from "\
                                " "+str(dbConf.DB_SHMA)+".tbmenu a inner join "+str(dbConf.DB_SHMA)+".tbmenu_ge b on "\
                                " a.id=b.id_mnu "\
                                " where "\
                                " b.estdo = true and id_grpo_emprsrl = "+ln_id_grpo_emprsrl+" "\
                                + str(lc_prmtrs)
            Cursor = Pconnection.queryFree(StrSql)
            if  Cursor :
                data = json.loads(json.dumps(Cursor, indent=2))
                return Utils.nice_json(data, 200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_RGSTRS}, 400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN}, 400)



    def crearMenu(self, objectValues, table_name):
        return Pconnection.queryInsert(dbConf.DB_SHMA + "." + str(table_name), objectValues, 'id')

    def actualizarMenu(self, objectValues, table_name):
        return Pconnection.queryUpdate(dbConf.DB_SHMA + "." + str(table_name), objectValues, 'id=' + str(objectValues['id']))

    '''
        def agregar_favorito
        @author: Robin.Valencia
        @since:16-05-2018
        @summary: metodo que permite agregar un item de menu a favorito si y solo si tiene menos de 5 favoritos y si es un enlace y es accesible por el perfil.
        @param: por request el id_menu_ge,
        @return:retorna
    '''
    def agregar_favorito(self):
        key = request.headers['Authorization']
        if key:
            validacionSeguridad.ValidacionToken(key)
            if validacionSeguridad :
                token = Pconnection.querySelect(dbConf.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
                tmp_data = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
                datosUsuario = validacionSeguridad.ObtenerDatosUsuario(tmp_data['lgn'])[0]
                id_lgn_prfl_scrsl = validacionSeguridad.validaUsuario(tmp_data['lgn'])


                ld_id_mnu_ge = request.form['id_mnu_ge']

                #consulta el id_lgn_prfl_mnu
                ld_id_lgn_prfl_mnu = Pconnection.querySelect(dbConf.DB_SHMA+'.tblogins_perfiles_menu', "id", "id_lgn_prfl_scrsl='"+str(id_lgn_prfl_scrsl['id_prfl_scrsl'])+"' and id_mnu_ge='"+str(ld_id_mnu_ge)+"' and estdo is true")[0]
                #consulta cuantos favoritos tiene

                cntdd_fvrts = self.get_cant_favoritos(id_lgn_prfl_scrsl)

                if cntdd_fvrts < 5:
                    #Buscar si existe el elemento y si el estado es true
                    lo_current = self.busca_favorito(id_lgn_prfl_scrsl['id_prfl_scrsl'],ld_id_mnu_ge)
                    arrayValues = {}
                    if not lo_current:#Inserta
                        arrayValues['id_lgn_prfl_mnu'] = str(ld_id_lgn_prfl_mnu['id'])
                        arrayValues['id_lgn_crcn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValues['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValues['fcha_crcn'] = str(ld_fcha_actl)
                        arrayValues['fcha_mdfccn'] = str(ld_fcha_actl)
                        result = Pconnection.queryInsert(dbConf.DB_SHMA+".tbfavoritosmenu",arrayValues)
                    else:#actualiza
                        if not lo_current['estdo']:
                            arrayValues['estdo'] = 'true'
                            Pconnection.queryUpdate(dbConf.DB_SHMA +'.tbfavoritosmenu',arrayValues,'id='+str(lo_current['id']))

                    return Utils.nice_json({labels.lbl_stts_success:labels.FVRTO_AGRGDO}, 200)
                else:
                    return Utils.nice_json({labels.lbl_stts_error:errors.ERR_EXCDE_CNT_FVRTS}, 200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_SSN}, 400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_PRMTRS}, 400)

    def remover_favorito(self):
        #return Utils.nice_json({labels.lbl_stts_success:labels.FVRTO_BRRDO}, 200)
        key = request.headers['Authorization']
        if key:
            validacionSeguridad.ValidacionToken(key)
            if validacionSeguridad :
                token = Pconnection.querySelect(dbConf.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
                tmp_data = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
                datosUsuario = validacionSeguridad.ObtenerDatosUsuario(tmp_data['lgn'])[0]
                id_lgn_prfl_scrsl = validacionSeguridad.validaUsuario(tmp_data['lgn'])
                ld_id_mnu_ge = request.form['id_mnu_ge']
                #busco el favorito
                lo_current = self.busca_favorito(id_lgn_prfl_scrsl['id_prfl_scrsl'],ld_id_mnu_ge)
                arrayValues = {}
                arrayValues['estdo'] = 'false'
                Pconnection.queryUpdate(dbConf.DB_SHMA +'.tbfavoritosmenu',arrayValues,'id='+str(lo_current['id']))
                return Utils.nice_json({labels.lbl_stts_success:labels.FVRTO_BRRDO}, 200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_PRMTRS}, 400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_SN_PRMTRS}, 400)


    '''
        def agregar_favorito
        @author: Robin.Valencia
        @since:21-05-2018
        @summary: metodo que permite conocer la cantidad de favoritos de un usuario con su id_lgn_prfl_scrsl
        @param: id_lgn_prfl_scrsl
        @return:retorna la cantidad de foritos
    '''
    def get_cant_favoritos(self,id_lgn_prfl_scrsl):
            strQuery ='select count(1) cntdd_fvrts from '+ dbConf.DB_SHMA +'.tbfavoritosmenu fm '\
                        'left join '+ dbConf.DB_SHMA +'.tblogins_perfiles_menu lpm on lpm.id=fm.id_lgn_prfl_mnu '\
                        'where lpm.id_lgn_prfl_scrsl='+str(id_lgn_prfl_scrsl['id_prfl_scrsl']) +' and fm.estdo=true'
            favoritos = Pconnection.queryFree(strQuery)[0]

            return favoritos['cntdd_fvrts']

    '''
        def agregar_favorito
        @author: Robin.Valencia
        @since:21-05-2018
        @summary: busca un favorito de un usuario
        @param: id_lgn_prfl_scrsl
        @return: id del favorito,id_mnu_ge, y el estdo de un favorito
    '''
    def busca_favorito(self, id_prfl_scrsl, id_mnu_ge):
        strQuery ='select fm.id,lpm.id_mnu_ge,fm.estdo from '+ dbConf.DB_SHMA +'.tbfavoritosmenu fm '\
                    'left join '+ dbConf.DB_SHMA +'.tblogins_perfiles_menu lpm on lpm.id=fm.id_lgn_prfl_mnu '\
                    'where lpm.id_lgn_prfl_scrsl='+str(id_prfl_scrsl) +' and lpm.id_mnu_ge='+str(id_mnu_ge)
        lo_current = Pconnection.queryFree(strQuery)[0]
        return lo_current
