'''
    @author: Cristian Botina
    @since: 01/03/2018
'''
from flask_restful import request, Resource
from wtforms import Form, validators, StringField
import Static.config as conf  # @UnresolvedImport
from Static.ConnectDB import ConnectDB  # @UnresolvedImport
from Static.Utils import Utils  # @UnresolvedImport
import Static.errors as errors  # @UnresolvedImport
import Static.labels as labels  # @UnresolvedImport
import Static.opciones_higia as optns  # @UnresolvedImport
import time,hashlib,json #@UnresolvedImport
from ValidacionSeguridad import ValidacionSeguridad # @UnresolvedImport
import Static.config_DB as dbConf # @UnresolvedImport
from Static.UploadFiles import UploadFiles  # @UnresolvedImport
from descarga import Descarga

lc_cnctn = ConnectDB()
Utils = Utils()
validacionSeguridad = ValidacionSeguridad()

descarga = Descarga()

class ActualizarAcceso(Form):
    id_login_ge = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_SN_PRMTRS)])
    login = StringField(labels.lbl_lgn,[validators.DataRequired(message=errors.ERR_NO_INGSA_USRO)])
    password = StringField(labels.lbl_cntrsna,[validators.DataRequired(message=errors.ERR_NO_INGRSA_CNTRSNA)])
    nombre_usuario = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_INGSA_NMBRE_USRO)])


class AcInsertarAcceso(Form):
    login = StringField(labels.lbl_lgn,[validators.DataRequired(message=errors.ERR_NO_INGSA_USRO)])
    password = StringField(labels.lbl_cntrsna,[validators.DataRequired(message=errors.ERR_NO_INGRSA_CNTRSNA)])
    nombre_usuario = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_INGSA_NMBRE_USRO)])


'''
    @author:Cristian Botina
    @since:01/03/2018
    @summary:Clase para gestionar los usuarios (logins)
'''
class Usuarios(Resource):

    def post(self, **kwargs):
        if kwargs['page'] == 'listar':
            return self.ObtenerUsuarios()
        elif kwargs['page'] == 'crear':
            return self.InsertarUsuarios()
        elif kwargs['page'] == 'actualizar':
            return self.ActualizarUsuario()
        if kwargs['page'] == 'descarga_csv':
            return self.Descarga_csv()
        if kwargs['page'] == 'descarga_txt':
            return self.Descarga_txt()
        if kwargs['page'] == 'descarga_xlsx':
            return self.Descarga_xlsx()
        if kwargs['page'] == 'descarga_pdf':
            return self.Descarga_pdf()
    '''
        @author:Cristian Botina
        @since:01/03/2018
        @summary:Metodo para listar los usuarios
        @param: Self
        @return:Listado en formato Json
    '''
    def ObtenerUsuarios(self):
        print(request.headers)
        lc_tkn = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        lc_prmtrs=''

        try:
            ln_id_lgn_ge = request.form['id_login_ge']
            lc_prmtrs = lc_prmtrs + "  and a.id = " + ln_id_lgn_ge
        except Exception:
            pass
        try:
            lc_lgn = request.form['login']
            lc_prmtrs = lc_prmtrs + "  and lgn like '%" + lc_lgn + "%' "
        except Exception:
            pass
        try:
            ln_id_grpo_emprsrl = request.form['id_grpo_emprsrl']
            lc_prmtrs = lc_prmtrs + "  and id_grpo_emprsrl = " + ln_id_grpo_emprsrl + " "
        except Exception:
            pass

        if val:
            Cursor = lc_cnctn.queryFree(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + lc_prmtrs +
                                    " order by "\
                                    " b.lgn")
            if Cursor :
                data = json.loads(json.dumps(Cursor, indent=2))
                return Utils.nice_json(data,200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_RGSTRS},400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    '''
        @author:Cristian Botina
        @since:01/03/2018
        @summary:Metodo que inserta el registro en la tabla de logins y logins_ge
        @param: Self
        @return:Success, 400
    '''
    def InsertarUsuarios(self):
        lc_tkn = request.headers['Authorization']
        ld_fcha_actl = time.ctime()
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        lc_cntrsna = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
        #Validar los campos requeridos.
        u = AcInsertarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({labels.lbl_stts_error:u.errors},400)

        if val:
            '''
                Aqui insertamos los datos del usuario
            '''
            la_clmns_insrtr={}
            la_clmns_insrtr_ge={}
            la_clmns_insrtr['lgn']=request.form['login']
            la_clmns_insrtr['cntrsna']=lc_cntrsna #pendiente encriptar la contrase�a
            la_clmns_insrtr['nmbre_usro']=request.form['nombre_usuario']
            la_clmns_insrtr_ge['fcha_crcn']=str(ld_fcha_actl)
            la_clmns_insrtr_ge['fcha_mdfccn']=str(ld_fcha_actl)
            la_clmns_insrtr_ge['id_grpo_emprsrl']=request.form['id_grpo_emprsrl']

            '''
                Validar repetidos
            '''
            lc_tbls_query = dbConf.DB_SHMA+".tblogins_ge a INNER JOIN "+dbConf.DB_SHMA+".tblogins b on a.id_lgn=b.id "
            CursorValidar = lc_cnctn.querySelect(lc_tbls_query, ' b.id ', " b.lgn = '"+str(la_clmns_insrtr['lgn'])+"' ")
            if CursorValidar:
                return Utils.nice_json({labels.lbl_stts_error:labels.lbl_lgn+" "+errors.ERR_RGSTRO_RPTDO},400)

            ln_id_lgn = self.UsuarioInsertaRegistro(la_clmns_insrtr,'tblogins')
            la_clmns_insrtr_ge['id_lgn']=str(ln_id_lgn)
            lc_nmbre_imgn = str(hashlib.md5(str(ln_id_lgn).encode('utf-8')).hexdigest())+'.jpg'

            if request.files:
                la_grdr_archvo = self.GuardarArchivo(request.files,'imge_pth',conf.SV_DIR_IMAGES,lc_nmbre_imgn,True)
                if la_grdr_archvo['status']=='error':
                    return Utils.nice_json({labels.lbl_stts_error:la_grdr_archvo['retorno']},400)
                else:
                    la_clmns_insrtr['fto_usro'] = str(la_grdr_archvo["retorno"])

            '''
                Actualizo el registro con el nombre de la imagen
            '''
            la_clmns_insrtr['id']=str(ln_id_lgn)
            self.UsuarioActualizaRegistro(la_clmns_insrtr,'tblogins')

            '''
                Inserto la relacion en la tabla GE
            '''
            self.UsuarioInsertaRegistro(la_clmns_insrtr_ge,'tblogins_ge')

            '''
                obtengo id_lgn a partir del id_lgn_ge y se lo retorno al success
            '''
            Cursor = lc_cnctn.queryFree("select id from "+dbConf.DB_SHMA+".tblogins_ge order by id desc limit 1")
            if Cursor :
                data = json.loads(json.dumps(Cursor[0], indent=2))
                ln_id_lgn_ge = data['id']

            return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_RGSTRO_EXTSO,"id":ln_id_lgn_ge},200)
            '''
                Fin de la insercion de los datos
            '''
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    '''
        @author:Cristian Botina
        @since:01/03/2018
        @summary:Metodo que actualiza el registro en la tabla de logins y logins_ge
        @param: Self
        @return:Success, 400
    '''
    def ActualizarUsuario(self):
        lc_tkn = request.headers['Authorization']
        ld_fcha_actl = time.ctime()
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #Validar los campos requeridos.
        u = ActualizarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({labels.lbl_stts_error:u.errors},400)
        if val :
            md5 = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()

            '''
                INSERTAR DATOS
            '''
            la_clmns_actlzr={}
            la_clmns_actlzr_ge={}
            #Actualizo tabla ge
            la_clmns_actlzr_ge['id']=request.form['id_login_ge']
            la_clmns_actlzr_ge['fcha_mdfccn']=str(ld_fcha_actl)
            la_clmns_actlzr_ge['id_grpo_emprsrl']=request.form['id_grpo_emprsrl']
            la_clmns_actlzr['lgn']=request.form['login']
            la_clmns_actlzr['cntrsna']=md5 #pendiente encriptar la contrase�a
            la_clmns_actlzr['nmbre_usro']=request.form['nombre_usuario']
            lb_estdo    = request.form["estdo"]
            la_clmns_actlzr['estdo']= True  if lb_estdo == 'ACTIVO' else False

            '''
            Validar repetidos
            '''
            lc_tbls_query = dbConf.DB_SHMA+".tblogins_ge a INNER JOIN "+dbConf.DB_SHMA+".tblogins b on a.id_lgn=b.id "
            CursorValidar = lc_cnctn.querySelect(lc_tbls_query, ' b.id ', " a.id <> "+str(la_clmns_actlzr_ge['id'])+" AND b.lgn = '"+str(la_clmns_actlzr['lgn'])+"' ")
            if CursorValidar:
                return Utils.nice_json({labels.lbl_stts_error:labels.lbl_lgn+" "+errors.ERR_RGSTRO_RPTDO},400)

            '''
            Insertar en la tabla auxiliar y obtener id de creacion
            '''
            self.UsuarioActualizaRegistro(la_clmns_actlzr_ge,'tblogins_ge')
            #obtengo id_lgn a partir del id_lgn_ge
            Cursor = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tblogins_ge', 'id_lgn', "id="+str(la_clmns_actlzr_ge['id']))
            if Cursor :
                data = json.loads(json.dumps(Cursor[0], indent=2))
                ln_id_lgn = data['id_lgn']
            #Actualizo tabla principal
            la_clmns_actlzr['id']=ln_id_lgn

            '''
            Guardar la imagen en la ruta especificada
            '''
            lc_nmbre_imgn = str(hashlib.md5(str(la_clmns_actlzr['id']).encode('utf-8')).hexdigest())+'.jpg'
            la_grdr_archvo = self.GuardarArchivo(request.files,'imge_pth',conf.SV_DIR_IMAGES,lc_nmbre_imgn,True)
            if la_grdr_archvo['status']=='error':
                return Utils.nice_json({labels.lbl_stts_error:la_grdr_archvo['retorno']},400)
            else:
                la_clmns_actlzr['fto_usro'] = str(la_grdr_archvo["retorno"])

            #ACTUALIZACION TABLA LOGINS OK
            self.UsuarioActualizaRegistro(la_clmns_actlzr,'tblogins')
            return Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_ACTLZCN_EXTSA},200)
            '''
                FIN INSERTAR DATOS
            '''
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    def UsuarioInsertaRegistro(self,objectValues,table_name):
        return lc_cnctn.queryInsert(dbConf.DB_SHMA+"."+str(table_name), objectValues,'id')

    def UsuarioActualizaRegistro(self,objectValues,table_name):
        return lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str(table_name), objectValues,'id='+str(objectValues['id']))

    def GuardarArchivo(self,file,cmpo, drccn_imgn,nmbre_archvo,crr_drccn):
        la_rspsta = {}
        '''
            CARGA DE IMAGEN
        '''
        #guardar la imagen
        la_rslt_imge_upld={}
        if cmpo in file:
            mFile = UploadFiles(drccn_imgn,nmbre_archvo,crr_drccn)
            la_rslt_imge_upld = mFile.upload(file[cmpo])
            #Check status uploadimage
            if la_rslt_imge_upld["status"] == "OK":
                la_rspsta['status']='OK'
                la_rspsta['retorno']=la_rslt_imge_upld["namefile"]
            else:
                la_rspsta['status']='error'
                la_rspsta['retorno']=errors.ERR_NO_IMGN_GRDDA
        else:
            la_rspsta['status']='error'
            la_rspsta['retorno']=errors.ERR_NO_ARCVO_DFNDO
        return la_rspsta

    def Descarga_csv(self):
        lc_tkn = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #val=True
        lc_prmtrs=''

        try:
            ln_id_lgn_ge = request.form['id_login_ge']
            lc_prmtrs = lc_prmtrs + "  and a.id = " + ln_id_lgn_ge
        except Exception:
            pass
        try:
            lc_lgn = request.form['login']
            lc_prmtrs = lc_prmtrs + "  and lgn like '%" + lc_lgn + "%' "
        except Exception:
            pass
        try:
            ln_id_grpo_emprsrl = request.form['id_grpo_emprsrl']
            lc_prmtrs = lc_prmtrs + "  and id_grpo_emprsrl = " + ln_id_grpo_emprsrl + " "
        except Exception:
            pass

        if val:
            Cursor = lc_cnctn.queryFree(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + lc_prmtrs +
                                    " order by "\
                                    " b.lgn")
            if Cursor :
                result = descarga.csv(json.dumps(Cursor, indent=2),';')
                return result

        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    def Descarga_txt(self):
        lc_tkn = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #val=True
        lc_prmtrs=''

        try:
            ln_id_lgn_ge = request.form['id_login_ge']
            lc_prmtrs = lc_prmtrs + "  and a.id = " + ln_id_lgn_ge
        except Exception:
            pass
        try:
            lc_lgn = request.form['login']
            lc_prmtrs = lc_prmtrs + "  and lgn like '%" + lc_lgn + "%' "
        except Exception:
            pass
        try:
            ln_id_grpo_emprsrl = request.form['id_grpo_emprsrl']
            lc_prmtrs = lc_prmtrs + "  and id_grpo_emprsrl = " + ln_id_grpo_emprsrl + " "
        except Exception:
            pass

        if val:
            Cursor = lc_cnctn.queryFree(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + lc_prmtrs +
                                    " order by "\
                                    " b.lgn")
            if Cursor :
                result = descarga.text(json.dumps(Cursor, indent=2))
                return result

        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)

    def Descarga_xlsx(self):
        lc_tkn = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #val=True
        lc_prmtrs=''

        try:
            ln_id_lgn_ge = request.form['id_login_ge']
            lc_prmtrs = lc_prmtrs + "  and a.id = " + ln_id_lgn_ge
        except Exception:
            pass
        try:
            lc_lgn = request.form['login']
            lc_prmtrs = lc_prmtrs + "  and lgn like '%" + lc_lgn + "%' "
        except Exception:
            pass
        try:
            ln_id_grpo_emprsrl = request.form['id_grpo_emprsrl']
            lc_prmtrs = lc_prmtrs + "  and id_grpo_emprsrl = " + ln_id_grpo_emprsrl + " "
        except Exception:
            pass

        if val:
            Cursor = lc_cnctn.queryFree(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + lc_prmtrs +
                                    " order by "\
                                    " b.lgn")
            if Cursor :
                result = descarga.xlsx(json.dumps(Cursor, indent=2))
                return result

        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)
    def Descarga_pdf(self):
        lc_tkn = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #val=True
        lc_prmtrs=''

        try:
            ln_id_lgn_ge = request.form['id_login_ge']
            lc_prmtrs = lc_prmtrs + "  and a.id = " + ln_id_lgn_ge
        except Exception:
            pass
        try:
            lc_lgn = request.form['login']
            lc_prmtrs = lc_prmtrs + "  and lgn like '%" + lc_lgn + "%' "
        except Exception:
            pass
        try:
            ln_id_grpo_emprsrl = request.form['id_grpo_emprsrl']
            lc_prmtrs = lc_prmtrs + "  and id_grpo_emprsrl = " + ln_id_grpo_emprsrl + " "
        except Exception:
            pass

        if val:
            Cursor = lc_cnctn.queryFree(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + lc_prmtrs +
                                    " order by "\
                                    " b.lgn")
            if Cursor :
                result = descarga.pdf(json.dumps(Cursor, indent=2))
                return result

        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_ATRZCN},400)
