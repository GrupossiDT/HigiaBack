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
import time,hashlib,json, random #@UnresolvedImport
from ValidacionSeguridad import ValidacionSeguridad # @UnresolvedImport
import Static.config_DB as dbConf # @UnresolvedImport
from Static.UploadFiles import UploadFiles  # @UnresolvedImport
from descarga import Descarga
from mail import correo
from IPy import IP
import socket
import re
import requests

lc_cnctn = ConnectDB()
Utils = Utils()
validacionSeguridad = ValidacionSeguridad()

descarga = Descarga()

class ActualizarAcceso(Form):
    id_login_ge = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_SN_PRMTRS)])
    login = StringField(labels.lbl_lgn,[validators.DataRequired(message=errors.ERR_NO_INGSA_USRO)])
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
        elif kwargs['page'] == 'claveTemporal':
            return self.claveTemporal()
        elif kwargs['page'] == 'validaClavetemporal':
            return self.validaclaveTemporal()
        elif kwargs['page'] == 'actualizarContrasena':
            return self.actualizarContrasena()
        elif kwargs['page'] == 'actualizarContrenaInterna':
            return self.actualizarContrenaInterna()
        elif kwargs['page'] == 'preguntasSeguridad':
            return self.preguntasSeguridad()
        elif kwargs['page'] == 'reponderPreguntasSeguridad':
            return self.reponderPreguntasSeguridad()


    '''
        @author:Cristian Botina
        @since:01/03/2018
        @summary:Metodo para listar los usuarios
        @param: Self
        @return:Listado en formato Json
    '''
    def ObtenerUsuarios(self):
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
                                    " a.id_grpo_emprsrl = "+ln_id_grpo_emprsrl+" "\
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

        '''
            Validar que la contrasena cumpla con el Patron de contraseas
        '''
        if not re.match(conf.EXPRESION_CLAVE_USUARIO, request.form['password']):
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_PTRN_CLVE},400)

        lc_cntrsna = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
        #Validar los campos requeridos.
        u = AcInsertarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({labels.lbl_stts_error:u.errors},400)
            #Utils.nice_json({labels.lbl_stts_success:labels.SCCSS_ACTLZCN_EXTSA},200)

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
            print(lc_tbls_query +"::"+str(la_clmns_insrtr['lgn']))
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
        lc_estdo = request.form["estdo"]

        '''
            Validar que la contrasena cumpla con el Patron de contraseas, excepto que tenga el campo vacio
        '''
        if request.form['password']!="":
            if not re.match(conf.EXPRESION_CLAVE_USUARIO, request.form['password']):
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_PTRN_CLVE},400)



        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(lc_tkn,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #Validar los campos requeridos.
        u = ActualizarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({labels.lbl_stts_error:u.errors},400)
        if val :
            '''
                INSERTAR DATOS
            '''
            la_clmns_actlzr={}
            la_clmns_actlzr_ge={}
            #Actualizo tabla ge
            la_clmns_actlzr_ge['id']=request.form['id_login_ge']
            la_clmns_actlzr_ge['fcha_mdfccn']=str(ld_fcha_actl)
            la_clmns_actlzr_ge['id_grpo_emprsrl']=request.form['id_grpo_emprsrl']
            la_clmns_actlzr_ge['estdo'] = lc_estdo
            la_clmns_actlzr['lgn']=request.form['login']

            la_clmns_actlzr['nmbre_usro']=request.form['nombre_usuario']

            if request.form['password']:
                md5 = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
                la_clmns_actlzr['cntrsna']=md5

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

            if request.files:
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

    def UsuarioActualizaRegistro(self,objectValues,table_name,lc_where='' ):
        if lc_where:
            lc_where = str(lc_where)
        else:
            lc_where = 'id='+str(objectValues['id'])

        return lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str(table_name), objectValues, lc_where)

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


    ### debe generar el id_lgns_ssn asociado al correo electronico
    ### no debe enviar msj texto y correo electronico
    def claveTemporal(self):
        lc_crro_crprtvo = request.form['crro_crprtvo']
        lc_query_clv_tmp = "select id from ( "\
                                    " select "\
                                    " case when emplds_une.id is not null then "\
                                    " emplds.crro_elctrnco "\
                                    " else "\
                                    " prstdr.crro_elctrnco "\
                                    " end as crro_elctrnco, "\
                                    " lgn_ge.id "\
                                    " from "+dbConf.DB_SHMA+".tblogins_ge lgn_ge "\
                                    " left join "+dbConf.DB_SHMA+".tblogins lgn on lgn.id = lgn_ge.id_lgn "\
                                    " left join "+dbConf.DB_SHMA+".tbempleados_une emplds_une on emplds_une.id_lgn_accso_ge = lgn_ge.id "\
                                    " left join "+dbConf.DB_SHMA+".tbempleados emplds on emplds.id = emplds_une.id_empldo "\
                                    " left join "+dbConf.DB_SHMA+".tbprestadores prstdr on prstdr.id_lgn_accso_ge = lgn_ge.id "\
                                    " left join "+dbConf.DB_SHMA+".tbcargos_une crgo_une on crgo_une.id = emplds_une.id_crgo_une "\
                                    " left join "+dbConf.DB_SHMA+".tbcargos crgo on crgo.id = crgo_une.id_crgo "\
                                    " left join "+dbConf.DB_SHMA+".tbunidades_negocio undd_ngco on undd_ngco.id = emplds_une.id_undd_ngco "\
                                    " inner join "+dbConf.DB_SHMA+".tblogins_perfiles_sucursales as prfl_scrsls on prfl_scrsls.id_lgn_ge = lgn_ge.id and prfl_scrsls.mrca_scrsl_dfcto is true "\
                                    " inner join "+dbConf.DB_SHMA+".tbperfiles_une as prfl_une on prfl_une.id = prfl_scrsls.id_prfl_une "\
                                    " where id_mtvo_rtro_une is null) as test "\
                                    " where crro_elctrnco ='"+lc_crro_crprtvo+"'"
        Cursor_clv_tmp = lc_cnctn.queryFree(lc_query_clv_tmp)
        if Cursor_clv_tmp :
            data = json.loads(json.dumps(Cursor_clv_tmp[0], indent=2))
            #se inserta en la tabla para posterior validacion
            arrayValues = {}
            #Se genera la keyword
            key = str(data['id'])+str(random.randint(1, 100000))
            key = hashlib.md5(key.encode('utf-8')).hexdigest()
            ld_fcha_actl = time.ctime()
            clave_tmp = Utils.aleatoria_n_digitos(8)
            arrayValues['cntrsna'] = str(clave_tmp)
            IpUsuario = IP(socket.gethostbyname(socket.gethostname()))
            arrayValues['ip'] = str(IpUsuario)
            device = Utils.DetectarDispositivo(request.headers.get('User-Agent'))
            arrayValues['dspstvo_accso'] = str(device)
            arrayValues['crreo_slctnte'] = str(lc_crro_crprtvo)
            arrayValues['fcha_mdfccn '] = str(ld_fcha_actl)
            arrayValues['id_lgn_ge '] = str(data['id'])
            arrayValues['token'] = str(key)
            arrayValues['estdo'] = str('true')
            lc_cnctn.queryInsert(dbConf.DB_SHMA + ".tbclaves_tmp", arrayValues)
            return Utils.nice_json({labels.lbl_stts_success:'Redireccionando Espera un Momento...',"tkn":key},200)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CRRO_SSTMA},400)

    def preguntasSeguridad(self):
        lc_token = request.form['lc_token']
        ## Debe existir en la base de datos el token generado, me rotorna el id del login del usuario y si no existe, retorna error
        ## Consulto 3 preguntas aleatorias de las que se encuentran parametrizadas de acuerdo al id_lgns_ssn si tiene menos de 3
        ## si existen, retorno las preguntas con su id preguntas, devuelve un error

        Cursor = lc_cnctn.queryFree("select "\
                     " id_lgn_ge "\
                     "from "\
                     ""+dbConf.DB_SHMA+".tbclaves_tmp "\
                     "where "\
                     "token = '"+lc_token+"' "\
                     "and estdo = true LIMIT 1 ")
        if Cursor :
            data = json.loads(json.dumps(Cursor[0], indent=2))

            ##Se valida que existan 6 preguntas parametrizadas
            lc_query_cnt = " select count(a.id) as ttl from "+dbConf.DB_SHMA+".tbrespuestas_preguntas_seguridad a "\
                                " inner join "+dbConf.DB_SHMA+".tbpreguntas_seguridad_ge b on a.id_prgnt_sgrdd_ge = b.id "\
                                " inner join "+dbConf.DB_SHMA+".tbpreguntas_seguridad c on b.id_prgnta_sgrdd = c.id "\
                                " where a.id_lgn_accso_ge = "+str(data['id_lgn_ge'])+" and a.estdo = true LIMIT 1 "
            Cursor3 = lc_cnctn.queryFree(lc_query_cnt)
            if Cursor3:
                data3 = json.loads(json.dumps(Cursor3[0], indent=2))
                ln_ttl = data3['ttl']
            else:
                ln_ttl = 0

            if  (ln_ttl<6):
                print("error, no se han definido las preguntas")
                return Utils.nice_json({labels.lbl_stts_error:"No se han definido las 6 preguntas de seguridad, comuníquese  con el administrador del sistema."},400)

            lc_query_rndm = " select a.id, c.dscrpcn from "+dbConf.DB_SHMA+".tbrespuestas_preguntas_seguridad a "\
                                " inner join "+dbConf.DB_SHMA+".tbpreguntas_seguridad_ge b on a.id_prgnt_sgrdd_ge = b.id "\
                                " inner join "+dbConf.DB_SHMA+".tbpreguntas_seguridad c on b.id_prgnta_sgrdd = c.id "\
                                " where a.id_lgn_accso_ge = "+str(data['id_lgn_ge'])+" and a.estdo = true "\
                                " order by random() limit 3 "
            Cursor2 = lc_cnctn.queryFree(lc_query_rndm)
            if Cursor2 :
                data2 = json.loads(json.dumps(Cursor2, indent=2))

                    ##return Utils.nice_json({labels.lbl_stts_success:'TODO ESTA OK',"preguntas":data2},200)
                return Utils.nice_json(data2,200)

        else:
            return Utils.nice_json({labels.lbl_stts_error:"La cadena Token no es valida."},400)

    def reponderPreguntasSeguridad(self):
        lc_token = request.form['token']
        ln_prgnta_0 = request.form['txt_idpr0']
        ln_prgnta_1 = request.form['txt_idpr1']
        ln_prgnta_2 = request.form['txt_idpr2']
        lc_rspsta_0 = request.form['txt_pregunta0']
        lc_rspsta_0 = hashlib.md5(lc_rspsta_0.encode('utf-8')).hexdigest()
        lc_rspsta_1 = request.form['txt_pregunta1']
        lc_rspsta_1 = hashlib.md5(lc_rspsta_1.encode('utf-8')).hexdigest()
        lc_rspsta_2 = request.form['txt_pregunta2']
        lc_rspsta_2 = hashlib.md5(lc_rspsta_2.encode('utf-8')).hexdigest()


        ## Obtengo el id delusuario de acuerdo al token
        lc_query_clve_tmp = " select id, id_lgn_ge, crreo_slctnte, cntrsna from "+dbConf.DB_SHMA+".tbclaves_tmp where token = '"+lc_token+"' and estdo = true limit 1;"
        Cursor_clve_tmp = lc_cnctn.queryFree(lc_query_clve_tmp)
        if Cursor_clve_tmp:
            data_tkn = json.loads(json.dumps(Cursor_clve_tmp[0], indent=2))
            id_lgn_ge = data_tkn['id_lgn_ge']
            id_claves_tmp = data_tkn['id']
            lc_crro_slctnte = data_tkn['crreo_slctnte']
            lc_cntrsna = data_tkn['cntrsna']
        else:
            return Utils.nice_json({labels.lbl_stts_error:"La cadena Token no es valida."},400)


        ## Validar la cantidad de intentos
        #validamos que no tenga una clave temporal ya generada al menos 3 intentos en 30 min
        lc_query = "select "\
                     "count(estdo) as count "\
                     "from "\
                     ""+dbConf.DB_SHMA+".tbclaves_tmp "\
                     "where "\
                     "current_timestamp - fcha_crcn < INTERVAL '30' minute "\
                     "and estdo = true "\
                     "and crreo_slctnte ='"+lc_crro_slctnte+"'"
        Cursor = lc_cnctn.queryFree(lc_query)
        print('aqui consulta')
        print(lc_query)
        if Cursor:
            data_vlda = json.loads(json.dumps(Cursor[0], indent=2))
            if data_vlda['count'] >= 3:
                return Utils.nice_json({labels.lbl_stts_error:'Ya se encuentra una Clave Generada para el ingreso Revisa tu correo o mensajes de texto intentalo más tarde'},400)


        ## Valido que la respuesta sea la misma que tiene parametrizada en la tabla de respuestas
        ## Las 3 respuestas exitosas, retornan un True
        if self.validaPreguntaSeguridad(id_lgn_ge, ln_prgnta_0, lc_rspsta_0) == True and self.validaPreguntaSeguridad(id_lgn_ge, ln_prgnta_1, lc_rspsta_1) == True and self.validaPreguntaSeguridad(id_lgn_ge, ln_prgnta_2, lc_rspsta_2) == True :

            ## Activo el registro de la clave temporal de acuerdo al tocken si las 3 preguntas son exitosas
            ld_fcha_actl = time.ctime()
            la_clmns_actlzr_rps = {}
            la_clmns_actlzr_rps['id']=str(id_claves_tmp)
            la_clmns_actlzr_rps['estdo']='true'
            la_clmns_actlzr_rps['fcha_mdfccn']=str(ld_fcha_actl)
            self.UsuarioActualizaRegistro(la_clmns_actlzr_rps,'tbclaves_tmp')


            ##consultar login y numero de cel para los mensajes
            lc_query_lgn = " select lgn, tlfno_cllr, id from ( "\
                                " select "\
                                " case when emplds_une.id is not null then "\
                                " trim(emplds.tlfno_cllr) "\
                                " else "\
                                " trim(prstdr.tlfno_cllr) "\
                                " end as tlfno_cllr, "\
                                " lgn.lgn, lgn_ge.id "\
                                " from "+dbConf.DB_SHMA+".tblogins_ge lgn_ge "\
                                " left join "+dbConf.DB_SHMA+".tblogins lgn on lgn.id = lgn_ge.id_lgn "\
                                " left join "+dbConf.DB_SHMA+".tbempleados_une emplds_une on emplds_une.id_lgn_accso_ge = lgn_ge.id "\
                                " left join "+dbConf.DB_SHMA+".tbempleados emplds on emplds.id = emplds_une.id_empldo "\
                                " left join "+dbConf.DB_SHMA+".tbprestadores prstdr on prstdr.id_lgn_accso_ge = lgn_ge.id "\
                                " left join "+dbConf.DB_SHMA+".tbcargos_une crgo_une on crgo_une.id = emplds_une.id_crgo_une "\
                                " left join "+dbConf.DB_SHMA+".tbcargos crgo on crgo.id = crgo_une.id_crgo "\
                                " left join "+dbConf.DB_SHMA+".tbunidades_negocio undd_ngco on undd_ngco.id = emplds_une.id_undd_ngco "\
                                " inner join "+dbConf.DB_SHMA+".tblogins_perfiles_sucursales as prfl_scrsls on prfl_scrsls.id_lgn_ge = lgn_ge.id and prfl_scrsls.mrca_scrsl_dfcto is true "\
                                " inner join "+dbConf.DB_SHMA+".tbperfiles_une as prfl_une on prfl_une.id = prfl_scrsls.id_prfl_une "\
                                " where id_mtvo_rtro_une is null) as test "\
                                " where id = "+str(id_lgn_ge)+" LIMIT 1 "
            Cursor_lgn = lc_cnctn.queryFree(lc_query_lgn)
            if Cursor_lgn:
                data_lgn = json.loads(json.dumps(Cursor_lgn[0], indent=2))
                lc_lgn = data_lgn['lgn']
                ln_cllr = data_lgn['tlfno_cllr']

                ## Cuando retorne 200, entonces se genera el proceso que habia anteriormente, que envia por sms y correo electronico y redireccoina a ingresar codigo de seguridad
                asunto = "Clave Temporal de Acceso Higia SSI"
                mensaje =   "Cordial saludo "+lc_lgn+","\
                            "<p>La clave temporal auto generada por el sistema estará vigente por 30 minutos</p>"\
                            "<br>"\
                            "<b>Clave Generada:</b>"+str(lc_cntrsna)

                correo.enviarCorreo(lc_crro_slctnte,asunto,mensaje)

                #ENVIO DEL CODIGO POR MENSAJE DE TEXTO
                lc_sms = "La clave temporal generada por el sistema estará vigente por 30 minutos. Clave Generada:"+str(lc_cntrsna)
                #lc_sms = lc_sms.replace(" ", "+")

                print(lc_crro_slctnte)
                print(asunto)
                print(mensaje)
                print(lc_sms)
                print(ln_cllr)

                lc_stts_web_srvcs_SMS = Utils.webServiceSMS(conf.URL_WS_SMS,ln_cllr,lc_sms,conf.LGN_USRO_WS_SMS,conf.CNTRSNA_USRO_WS_SMS)

                return Utils.nice_json({labels.lbl_stts_success:'Clave Temporal Generada con Exito! Redireccionando Espera un Momento...'},200)




        else:
            return Utils.nice_json({labels.lbl_stts_error:"Error en una respuesta de las preguntas de seguridad"},400)

    def validaPreguntaSeguridad(self,id_lgn_ge,id_rspsta_prgnta_sgrdd, rspsta_prgnta):
        lc_query = " select "\
                   "     	id "\
                   "     from "\
                   "     	"+dbConf.DB_SHMA+".tbrespuestas_preguntas_seguridad "\
                   "     where "\
                   "     	id = "+str(id_rspsta_prgnta_sgrdd)+" "\
                   "     	and id_lgn_accso_ge = "+str(id_lgn_ge)+" "\
                   "     	and rspsta = '"+str(rspsta_prgnta)+"' "\
                   "     	and estdo = true LIMIT 1 ";
        Cursor = lc_cnctn.queryFree(lc_query)
        if Cursor:
            return True
        else:
            return False

    def responderPreguntaSeguridadCopiaTemporal(self):

        lc_crro_crprtvo = request.form['crro_crprtvo']
        lc_query_clv_tmp = "select lgn, tlfno_cllr from ( "\
                                    " select "\
                                    " case when emplds_une.id is not null then "\
                                    " emplds.crro_elctrnco "\
                                    " else "\
                                    " prstdr.crro_elctrnco "\
                                    " end as crro_elctrnco,lgn.lgn, emplds.tlfno_cllr "\
                                    " from "+dbConf.DB_SHMA+".tblogins_ge lgn_ge "\
                                    " left join "+dbConf.DB_SHMA+".tblogins lgn on lgn.id = lgn_ge.id_lgn "\
                                    " left join "+dbConf.DB_SHMA+".tbempleados_une emplds_une on emplds_une.id_lgn_accso_ge = lgn_ge.id "\
                                    " left join "+dbConf.DB_SHMA+".tbempleados emplds on emplds.id = emplds_une.id_empldo "\
                                    " left join "+dbConf.DB_SHMA+".tbprestadores prstdr on prstdr.id_lgn_accso_ge = lgn_ge.id "\
                                    " left join "+dbConf.DB_SHMA+".tbcargos_une crgo_une on crgo_une.id = emplds_une.id_crgo_une "\
                                    " left join "+dbConf.DB_SHMA+".tbcargos crgo on crgo.id = crgo_une.id_crgo "\
                                    " left join "+dbConf.DB_SHMA+".tbunidades_negocio undd_ngco on undd_ngco.id = emplds_une.id_undd_ngco "\
                                    " inner join "+dbConf.DB_SHMA+".tblogins_perfiles_sucursales as prfl_scrsls on prfl_scrsls.id_lgn_ge = lgn_ge.id and prfl_scrsls.mrca_scrsl_dfcto is true "\
                                    " inner join "+dbConf.DB_SHMA+".tbperfiles_une as prfl_une on prfl_une.id = prfl_scrsls.id_prfl_une "\
                                    " where id_mtvo_rtro_une is null) as test "\
                                    " where crro_elctrnco ='"+lc_crro_crprtvo+"'"
        Cursor_clv_tmp = lc_cnctn.queryFree(lc_query_clv_tmp)
        if Cursor_clv_tmp :
            #validamos que no tenga una clave temporal ya generada al menos 3 intentos en 30 min
            lc_query = "select "\
                         "count(estdo) as count "\
                         "from "\
                         ""+dbConf.DB_SHMA+".tbclaves_tmp "\
                         "where "\
                         "current_timestamp - fcha_crcn < INTERVAL '30' minute "\
                         "and estdo = true "\
                         "and crreo_slctnte ='"+lc_crro_crprtvo+"'"
            Cursor = lc_cnctn.queryFree(lc_query)
            if Cursor:
                data_vlda = json.loads(json.dumps(Cursor[0], indent=2))
                if data_vlda['count'] <=3:
                    #try:
                        #se inserta en la tabla para posterior validacion
                        arrayValues = {}
                        ld_fcha_actl = time.ctime()
                        clave_tmp = Utils.aleatoria_n_digitos(8)
                        arrayValues['cntrsna'] = str(clave_tmp)
                        IpUsuario = IP(socket.gethostbyname(socket.gethostname()))
                        arrayValues['ip'] = str(IpUsuario)
                        device = Utils.DetectarDispositivo(request.headers.get('User-Agent'))
                        arrayValues['dspstvo_accso'] = str(device)
                        arrayValues['crreo_slctnte'] = str(lc_crro_crprtvo)
                        arrayValues['fcha_mdfccn '] = str(ld_fcha_actl)
                        lc_cnctn.queryInsert(dbConf.DB_SHMA + ".tbclaves_tmp", arrayValues)
                        data = json.loads(json.dumps(Cursor_clv_tmp[0], indent=2))
                        asunto = "Clave Temporal de Acceso Higia SSI"

                        mensaje =   "Hola "+data['lgn']+" "\
                                    "<p>La clave temporal auto generada por el sistema estará vigente por 30 minutos</p>"\
                                    "<br>"\
                                    "<b>Clave Generada:</b>"+str(clave_tmp)
                        correo.enviarCorreo(lc_crro_crprtvo,asunto,mensaje)

                        #ENVIO DEL CODIGO POR MENSAJE DE TEXTO
                        ln_cllr = data['tlfno_cllr']
                        lc_sms = "La clave temporal generada por el sistema estará vigente por 30 minutos. Clave Generada:"+str(clave_tmp)
                        #lc_sms = lc_sms.replace(" ", "+")
                        lc_stts_web_srvcs_SMS = Utils.webServiceSMS(conf.URL_WS_SMS,ln_cllr,lc_sms,conf.LGN_USRO_WS_SMS,conf.CNTRSNA_USRO_WS_SMS)

                        return Utils.nice_json({labels.lbl_stts_success:'Clave Temporal Generada con Exito! Redireccionando Espera un Momento...'},200)
                    #except Exception:
                    #    return Utils.nice_json({labels.lbl_stts_error:'No es posible enviar los datos'},400)
                else:
                    return Utils.nice_json({labels.lbl_stts_error:'Ya se encuentra una Clave Generada para el ingreso Revisa tu correo o mensajes de texto intentalo mas tarde'},400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CRRO_SSTMA},400)

    def validaclaveTemporal(self):
        lc_clve_tmprl = request.form['clve_tmprl']
        lc_query = "select "\
        "estdo, "\
        "crreo_slctnte "\
        "from "\
        ""+dbConf.DB_SHMA+".tbclaves_tmp "\
        "where "\
        "current_timestamp - fcha_crcn < INTERVAL '30' minute "\
        "and estdo = true "\
        "and cntrsna ='"+lc_clve_tmprl+"'"
        Cursor = lc_cnctn.queryFree(lc_query)
        if Cursor:
            data_vlda = json.loads(json.dumps(Cursor[0], indent=2))
            if data_vlda['estdo']:
                return Utils.nice_json({labels.lbl_stts_success:True},200)
            else:
                return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CLVE_TMP},400)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CLVE_TMP},400)

    def actualizarContrenaInterna(self):
        lc_clve_actl = request.form['clve_tmprl']
        lc_nva_cntrsna = request.form['nva_cntrsna']
        lc_rnva_cntrsna = request.form['rnva_cntrsna']
        ld_fcha_actl = time.ctime()

        ####lc_clve_actl = hashlib.md5(lc_clve_actl.encode('utf-8')).hexdigest()
        lc_id_lgn_ge = request.form['id_lgn_ge']

        '''
            Validaa nueva contrasena y la clave temporal tiene que ser iguales
        '''
        if lc_nva_cntrsna != lc_rnva_cntrsna:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CNCD_CNTSNA},400)

        '''
            Validar que la contrasena cumpla con el Patron de contraseas
        '''
        if not re.match(conf.EXPRESION_CLAVE_USUARIO, lc_nva_cntrsna):
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_PTRN_CLVE},400)

        lc_nva_cntrsna = hashlib.md5(lc_nva_cntrsna.encode('utf-8')).hexdigest()
        lc_clve_actl = hashlib.md5(lc_clve_actl.encode('utf-8')).hexdigest()

        '''
            Actualizar el usuario si coincide con la contraseña actual que ingreso
        '''
        lc_query_usro = " select "\
                            	" b.id as id_lgn_ge, "\
                            	" a.id as id_lgn "\
                            " from "\
                            	" "+dbConf.DB_SHMA+".tblogins a "\
                            " inner join "+dbConf.DB_SHMA+".tblogins_ge b on "\
                            	" a.id = b.id_lgn "\
                            " where "\
                            	" b.id = "+lc_id_lgn_ge+" "\
                            	" and cntrsna = '"+lc_clve_actl+"' LIMIT 1 ";
        Cursor_clv_tmp2 = lc_cnctn.queryFree(lc_query_usro)

        if Cursor_clv_tmp2 :
            data_usro = json.loads(json.dumps(Cursor_clv_tmp2[0], indent=2))

            #Actualiza login
            la_clmns_actlzr_lgn = {}
            la_clmns_actlzr_lgn['id']=str(data_usro['id_lgn'])
            la_clmns_actlzr_lgn['cntrsna']=str(lc_nva_cntrsna)
            self.UsuarioActualizaRegistro(la_clmns_actlzr_lgn,'tblogins')

            la_clmns_actlzr_lgn_ge = {}
            la_clmns_actlzr_lgn_ge['id']=str(data_usro['id_lgn_ge'])
            la_clmns_actlzr_lgn_ge['fcha_mdfccn']=str(ld_fcha_actl)
            self.UsuarioActualizaRegistro(la_clmns_actlzr_lgn_ge,'tblogins_ge')

            return Utils.nice_json({labels.lbl_stts_success:True},200)
        else:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CNTRSNA_INVLDA},400)



        #return Utils.nice_json({"error":"contraseña prueba"},400)

    def actualizarContrasena(self):

        lc_clve_tmprl = request.form['clve_tmprl']
        lc_nva_cntrsna = request.form['nva_cntrsna']
        lc_rnva_cntrsna = request.form['rnva_cntrsna']
        responsed = self.validaclaveTemporal()
        ld_fcha_actl = time.ctime()
        lc_cntrsna = hashlib.md5(lc_nva_cntrsna.encode('utf-8')).hexdigest()


        '''
            Validaa nueva contrasena y la clave temporal tiene que ser iguales
        '''
        if lc_nva_cntrsna != lc_rnva_cntrsna:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CNCD_CNTSNA},400)

        '''
            Validar que la cadena que se recibe de codigo, se encuentre en la base de datos y vigente por los 30 minutos
        '''
        if responsed.status_code != 200:
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_CLVE_TMP},400)

        '''
            Validar que la contrasena cumpla con el Patron de contraseas
        '''
        if not re.match(conf.EXPRESION_CLAVE_USUARIO, lc_nva_cntrsna):
            return Utils.nice_json({labels.lbl_stts_error:errors.ERR_NO_PTRN_CLVE},400)

        '''
            Actualizar el usuario que coincida con el codigo registrado
        '''
        lc_query_usro = "select lgn, id_lgn, id_lgn_ge from ( "\
                                    " select "\
                                    " case when emplds_une.id is not null then "\
                                    " emplds.crro_elctrnco "\
                                    " else "\
                                    " prstdr.crro_elctrnco "\
                                    " end as crro_elctrnco,lgn.lgn, lgn.id id_lgn, lgn_ge.id id_lgn_ge "\
                                    " from "+dbConf.DB_SHMA+".tblogins_ge lgn_ge "\
                                    " left join "+dbConf.DB_SHMA+".tblogins lgn on lgn.id = lgn_ge.id_lgn "\
                                    " left join "+dbConf.DB_SHMA+".tbempleados_une emplds_une on emplds_une.id_lgn_accso_ge = lgn_ge.id "\
                                    " left join "+dbConf.DB_SHMA+".tbempleados emplds on emplds.id = emplds_une.id_empldo "\
                                    " left join "+dbConf.DB_SHMA+".tbprestadores prstdr on prstdr.id_lgn_accso_ge = lgn_ge.id "\
                                    " left join "+dbConf.DB_SHMA+".tbcargos_une crgo_une on crgo_une.id = emplds_une.id_crgo_une "\
                                    " left join "+dbConf.DB_SHMA+".tbcargos crgo on crgo.id = crgo_une.id_crgo "\
                                    " left join "+dbConf.DB_SHMA+".tbunidades_negocio undd_ngco on undd_ngco.id = emplds_une.id_undd_ngco "\
                                    " inner join "+dbConf.DB_SHMA+".tblogins_perfiles_sucursales as prfl_scrsls on prfl_scrsls.id_lgn_ge = lgn_ge.id and prfl_scrsls.mrca_scrsl_dfcto is true "\
                                    " inner join "+dbConf.DB_SHMA+".tbperfiles_une as prfl_une on prfl_une.id = prfl_scrsls.id_prfl_une "\
                                    " where id_mtvo_rtro_une is null) as test "\
                                    " where crro_elctrnco = (select "\
                                    " crreo_slctnte "\
                                    " from "\
                                    " "+dbConf.DB_SHMA+".tbclaves_tmp "\
                                    " where "\
                                    " current_timestamp - fcha_crcn < INTERVAL '30' minute "\
                                    " and estdo = true and cntrsna = '"+lc_clve_tmprl+"') "
        Cursor_clv_tmp = lc_cnctn.queryFree(lc_query_usro)
        if Cursor_clv_tmp :
            data_usro = json.loads(json.dumps(Cursor_clv_tmp[0], indent=2))

            #Actualiza login
            la_clmns_actlzr_lgn = {}
            la_clmns_actlzr_lgn['id']=str(data_usro['id_lgn'])
            la_clmns_actlzr_lgn['cntrsna']=str(lc_cntrsna)
            self.UsuarioActualizaRegistro(la_clmns_actlzr_lgn,'tblogins')

            la_clmns_actlzr_lgn_ge = {}
            la_clmns_actlzr_lgn_ge['id']=str(data_usro['id_lgn_ge'])
            la_clmns_actlzr_lgn_ge['fcha_mdfccn']=str(ld_fcha_actl)
            self.UsuarioActualizaRegistro(la_clmns_actlzr_lgn_ge,'tblogins_ge')

            return Utils.nice_json({labels.lbl_stts_success:True},200)

        '''
            Validar que solo lo permita hacer con usuarios que no estan con LDAP
        '''
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
