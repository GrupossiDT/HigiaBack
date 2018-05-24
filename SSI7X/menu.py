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
        ln_opcn_mnu = request.form["id_mnu_ge"]
        ln_id_grpo_emprsrl = request.form["id_grpo_emprsrl"]
        if key:
            validacionSeguridad.ValidacionToken(key)
            if validacionSeguridad :
                token =Pconnection.querySelect(dbConf.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
                DatosUsuarioToken = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
                if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
                    datosUsuario = validacionSeguridad.ObtenerDatosUsuario(DatosUsuarioToken['lgn'])[0]
                    arrayValues={}
                    arrayValues['cdgo'] = request.form["cdgo"]
                    arrayValues['dscrpcn'] = request.form["dscrpcn"]
                    ##validacion de datos repetidos
                    Cursor = Pconnection.querySelect(dbConf.DB_SHMA +'.tbperfiles', 'cdgo', "cdgo='"+str(arrayValues['cdgo'])+"' or dscrpcn like '%"+str(arrayValues['dscrpcn'])+"%' ")
                    if Cursor :
                        return Utils.nice_json({labels.lbl_stts_error:errors.ERR_RGSTRO_RPTDO},400)

                    ln_id_prfl =  Pconnection.queryInsert(dbConf.DB_SHMA+".tbperfiles", arrayValues,'id')
                    if ln_id_prfl:
                        arrayValuesDetalle={}
                        arrayValuesDetalle['id_mnu'] = str(ln_id_prfl)
                        arrayValuesDetalle['id_grpo_emprsrl'] = str(ln_id_grpo_emprsrl)
                        arrayValuesDetalle['id_lgn_crcn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValuesDetalle['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValuesDetalle['fcha_mdfccn'] = str(ld_fcha_actl)
                        ln_id_prfl_une = Pconnection.queryInsert(dbConf.DB_SHMA+".tbperfiles_une", arrayValuesDetalle,'id')
                        return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_RGSTRO_EXTSO,"id":str(ln_id_prfl_une)},200)
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

    '''
        def actualizar
        @author: Luis.aragon
        @since:02-02-2018
        @summary: metodo que permite actualizar preguntas de seguridad, a partir de la autorizacion que contiene el headers del token y el permiso de la accion
        @param:
        @return:retorna objetos listados
    '''

    def actualizar(self):
        token = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        lb_val = validacionSeguridad.Principal(token, ln_opcn_mnu, optns.OPCNS_MNU['PreguntaSg'])
        u = ActualizarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({"error":u.errors}, 400)
        if lb_val :
            DatosUsuarioToken = jwt.decode(token, conf.SS_TKN_SCRET_KEY, 'utf-8')
            pn_id_lgn_ge_ssn = validacionSeguridad.ObtenerDatosUsuario(DatosUsuarioToken['lgn'])[0]
            lb_estdo    = request.form["estdo"]
            a_prgnta_ge = {}
            a_prgnta = {}
            # Actualizo tabla ge
            a_prgnta_ge['id'] = request.form['ln_id_prgnta_ge']
            a_prgnta_ge['fcha_mdfccn'] = str(ld_fcha_actl)
            a_prgnta_ge['id_lgn_mdfccn_ge'] = str(pn_id_lgn_ge_ssn['id_lgn_ge'])
            a_prgnta['cdgo'] = request.form['lc_cdgo']
            a_prgnta['dscrpcn'] = request.form['lc_dscrpcn']
            a_prgnta['estdo']=str(lb_estdo)
            a_prgnta['fcha_mdfccn'] = str(ld_fcha_actl)
            a_prgnta['id_lgn_mdfccn_ge'] = str(pn_id_lgn_ge_ssn['id_lgn_ge'])
            # validacion para evitar registros duplicados, se verifica que el codigo y la descripcion no existan en otros registros
            lc_tbls_query = dbConf.DB_SHMA + ".tbpreguntas_seguridad_ge a INNER JOIN " + dbConf.DB_SHMA + ".tbpreguntas_seguridad b on a.id_prgnta_sgrdd=b.id "
            CursorValidar = Pconnection.querySelect(lc_tbls_query, ' b.id ', "b.cdgo = '" + str(a_prgnta['cdgo']) + "' or b.dscrpcn like '%" + str(a_prgnta['dscrpcn']) + "%'")
            if CursorValidar:
                return Utils.nice_json({"error":errors.ERR_RGSTRO_RPTDO}, 400)
            self.PreguntaActualizaRegistro(a_prgnta_ge, 'tbpreguntas_seguridad_ge')
            # obtengo id_prgnta a partir del id
            Cursor = Pconnection.querySelect(dbConf.DB_SHMA + '.tbpreguntas_seguridad_ge', 'id_prgnta_sgrdd', "id=" + str(request.form['ln_id_prgnta_ge']))
            if Cursor :
                data = json.loads(json.dumps(Cursor[0], indent=2))
                ln_id_prgnta = data['id_prgnta_sgrdd']
            # Actualizo tabla principal
            a_prgnta['id'] = ln_id_prgnta
            self.PreguntaActualizaRegistro(a_prgnta, 'tbpreguntas_seguridad')
            return Utils.nice_json({"error":labels.SCCSS_ACTLZCN_EXTSA}, 200)
        else:
            return Utils.nice_json({"error":errors.ERR_NO_ATRZCN}, 400)



    def crearPregunta_seguridad(self, objectValues, table_name):
        return Pconnection.queryInsert(dbConf.DB_SHMA + "." + str(table_name), objectValues, 'id')

    def PreguntaActualizaRegistro(self, objectValues, table_name):
        return Pconnection.queryUpdate(dbConf.DB_SHMA + "." + str(table_name), objectValues, 'id=' + str(objectValues['id']))
