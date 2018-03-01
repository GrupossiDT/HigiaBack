'''
Created on 22/01/2018

@author: CRISTIAN.BOTINA
@
'''
from flask_restful import request, Resource
from wtforms import Form, validators, StringField
import SSI7X.Static.config as conf  # @UnresolvedImport
from SSI7X.Static.ConnectDB import ConnectDB  # @UnresolvedImport
from SSI7X.Static.Utils import Utils  # @UnresolvedImport
import SSI7X.Static.errors as errors  # @UnresolvedImport
import SSI7X.Static.labels as labels  # @UnresolvedImport
import SSI7X.Static.opciones_higia as optns  # @UnresolvedImport
import time,hashlib,json #@UnresolvedImport
from SSI7X.ValidacionSeguridad import ValidacionSeguridad # @UnresolvedImport
import SSI7X.Static.config_DB as dbConf # @UnresolvedImport
from SSI7X.Static.UploadFiles import UploadFiles  # @UnresolvedImport

lc_cnctn = ConnectDB()
Utils = Utils()
validacionSeguridad = ValidacionSeguridad()

class ActualizarAcceso(Form):
    id_login_ge = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_SN_PRMTRS)])
    login = StringField(labels.lbl_lgn,[validators.DataRequired(message=errors.ERR_NO_INGSA_USRO)]) 
    password = StringField(labels.lbl_cntrsna,[validators.DataRequired(message=errors.ERR_NO_INGRSA_CNTRSNA)])
    nombre_usuario = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_INGSA_NMBRE_USRO)])


class AcInsertarAcceso(Form):
    login = StringField(labels.lbl_lgn,[validators.DataRequired(message=errors.ERR_NO_INGSA_USRO)]) 
    password = StringField(labels.lbl_cntrsna,[validators.DataRequired(message=errors.ERR_NO_INGRSA_CNTRSNA)])
    nombre_usuario = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_INGSA_NMBRE_USRO)])



class Usuarios(Resource):
    
    def post(self, **kwargs):
        if kwargs['page'] == 'ListarUsuarios':
            return self.ObtenerUsuarios()
        elif kwargs['page'] == 'insertar_usuario':
            return self.InsertarUsuarios()
        elif kwargs['page'] == 'actualizar_usuario':
            return self.ActualizarUsuario()
    
    def ObtenerUsuarios(self):
        token = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(token,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        
        prmtrs=''
        
        
        
        try:
            id_lgn_ge = request.form['id_login_ge'] 
            prmtrs = prmtrs + "  and a.id = " + id_lgn_ge
        except Exception:
            pass
        try:
            lgn = request.form['login']
            prmtrs = prmtrs + "  and lgn like '%" + lgn + "%' "
        except Exception:
            pass
        try:
            id_grpo_emprsrl = request.form['id_grpo_emprsrl']
            prmtrs = prmtrs + "  and id_grpo_emprsrl = " + id_grpo_emprsrl + " "
        except Exception:
            pass        
        
        if val :
            Cursor = lc_cnctn.queryFree(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + prmtrs +
                                    " order by "\
                                    " b.lgn")
            print(" select "\
                                    " a.id, b.lgn, b.nmbre_usro, b.fto_usro, case when b.estdo = true then 'ACTIVO' else 'INACTIVO' end as estdo  "\
                                    " from "\
                                    " "+str(dbConf.DB_SHMA)+".tblogins_ge a inner join "+str(dbConf.DB_SHMA)+".tblogins b on "\
                                    " a.id_lgn = b.id "\
                                    " where "\
                                    " a.estdo = true "\
                                    + prmtrs +
                                    " order by "\
                                    " b.lgn")
            if Cursor :    
                data = json.loads(json.dumps(Cursor, indent=2))
                return Utils.nice_json(data,200)
            else:
                return Utils.nice_json({"error":errors.ERR_NO_RGSTRS},400)
        else:
            return Utils.nice_json({"error":errors.ERR_NO_ATRZCN},400)
        
    def InsertarUsuarios(self):
        token = request.headers['Authorization']
        fcha_actl = time.ctime()
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(token,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        lc_cntrsna = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
        #Validar los campos requeridos.
        u = AcInsertarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({"error":u.errors},400)
        
        if val :
            '''
                Aqui insertamos los datos del usuario
            '''
            arrayValues={}
            arrayValues3={}
            arrayValues['lgn']=request.form['login']
            arrayValues['cntrsna']=lc_cntrsna #pendiente encriptar la contraseña
            arrayValues['nmbre_usro']=request.form['nombre_usuario']
            arrayValues3['fcha_crcn']=str(fcha_actl)
            arrayValues3['fcha_mdfccn']=str(fcha_actl)
            arrayValues3['id_grpo_emprsrl']='2' #pendiente traer esta variable de una cookie
            
            '''
            Validar repetidos
            ''' 
            lc_tbls_query = dbConf.DB_SHMA+".tblogins_ge a INNER JOIN "+dbConf.DB_SHMA+".tblogins b on a.id_lgn=b.id "
            CursorValidar = lc_cnctn.querySelect(lc_tbls_query, ' b.id ', " b.lgn = '"+str(arrayValues['lgn'])+"' ")
            if CursorValidar:
                return Utils.nice_json({"error":labels.lbl_lgn+" "+errors.ERR_RGSTRO_RPTDO},400) 

            id_lgn = self.UsuarioInsertaRegistro(arrayValues,'tblogins')
            arrayValues3['id_lgn']=str(id_lgn)
            lc_nmbre_imgn = str(hashlib.md5(str(id_lgn).encode('utf-8')).hexdigest())+'.jpg'
            
            arrayGuardarArchivo = self.GuardarArchivo(request.files,'imge_pth',conf.SV_DIR_IMAGES,lc_nmbre_imgn,True)
            if arrayGuardarArchivo['status']=='error':
                return Utils.nice_json({"error":arrayGuardarArchivo['retorno']},400) 
            else:
                arrayValues['fto_usro'] = str(arrayGuardarArchivo["retorno"])
            
            '''
            Actualizo el registro con el nombre de la imagen
            ''' 
            arrayValues['id']=str(id_lgn)
            self.UsuarioActualizaRegistro(arrayValues,'tblogins')
            
            ##Inserto la relación en la tabla GE
            self.UsuarioInsertaRegistro(arrayValues3,'tblogins_ge')
            
            return Utils.nice_json({"error":labels.SCCSS_RGSTRO_EXTSO},200)
            '''
            Fin de la insercion de los datos
            '''
        else:
            return Utils.nice_json({"error":errors.ERR_NO_ATRZCN},400)
    
    def ActualizarUsuario(self):
        token = request.headers['Authorization']
        fcha_actl = time.ctime()
        ln_opcn_mnu = request.form["id_mnu_ge"]
        validacionSeguridad = ValidacionSeguridad()
        val = validacionSeguridad.Principal(token,ln_opcn_mnu,optns.OPCNS_MNU['Usuarios'])
        #Validar los campos requeridos.
        u = ActualizarAcceso(request.form)
        if not u.validate():
            return Utils.nice_json({"error":u.errors},400)
        if val :
            md5 = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
            
            '''
                INSERTAR DATOS
            '''
            arrayValues={}
            arrayValues2={}
            #Actualizo tabla ge
            arrayValues2['id']=request.form['id_login_ge']
            arrayValues2['fcha_mdfccn']=str(fcha_actl)
            arrayValues2['id_grpo_emprsrl']='2' #pendiente traer esta variable de una cookie
            arrayValues['lgn']=request.form['login']
            arrayValues['cntrsna']=md5 #pendiente encriptar la contraseña
            arrayValues['nmbre_usro']=request.form['nombre_usuario']
            '''
            Validar repetidos
            ''' 
            lc_tbls_query = dbConf.DB_SHMA+".tblogins_ge a INNER JOIN "+dbConf.DB_SHMA+".tblogins b on a.id_lgn=b.id "
            CursorValidar = lc_cnctn.querySelect(lc_tbls_query, ' b.id ', " a.id <> "+str(arrayValues2['id'])+" AND b.lgn = '"+str(arrayValues['lgn'])+"' ")
            if CursorValidar:
                return Utils.nice_json({"error":labels.lbl_lgn+" "+errors.ERR_RGSTRO_RPTDO},400) 
               
            '''
            Insertar en la tabla auxiliar y obtener id de creacion
            ''' 
            self.UsuarioActualizaRegistro(arrayValues2,'tblogins_ge')
            #obtengo id_lgn a partir del id_lgn_ge
            Cursor = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tblogins_ge', 'id_lgn', "id="+str(arrayValues2['id']))
            if Cursor :
                data = json.loads(json.dumps(Cursor[0], indent=2))
                id_lgn = data['id_lgn']
            #Actualizo tabla principal
            arrayValues['id']=id_lgn
            
            '''
            Guardar la imagen en la ruta especificada
            '''
            lc_nmbre_imgn = str(hashlib.md5(str(arrayValues['id']).encode('utf-8')).hexdigest())+'.jpg'
            arrayGuardarArchivo = self.GuardarArchivo(request.files,'imge_pth',conf.SV_DIR_IMAGES,lc_nmbre_imgn,True)
            if arrayGuardarArchivo['status']=='error':
                return Utils.nice_json({"error":arrayGuardarArchivo['retorno']},400) 
            else:
                arrayValues['fto_usro'] = str(arrayGuardarArchivo["retorno"]) 
            
            #ACTUALIZACION TABLA LOGINS OK
            self.UsuarioActualizaRegistro(arrayValues,'tblogins')
            return Utils.nice_json({"error":labels.SCCSS_ACTLZCN_EXTSA},200) 
            '''
                FIN INSERTAR DATOS
            '''
        else:
            return Utils.nice_json({"error":errors.ERR_NO_ATRZCN},400)
     
    def UsuarioInsertaRegistro(self,objectValues,table_name):
        return lc_cnctn.queryInsert(dbConf.DB_SHMA+"."+str(table_name), objectValues,'id') 
    
    def UsuarioActualizaRegistro(self,objectValues,table_name):
        return lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str(table_name), objectValues,'id='+str(objectValues['id']))
    
    def GuardarArchivo(self,file,cmpo, drccn_imgn,nmbre_archvo,crr_drccn):
        arrayRespuesta = {}
        '''
            CARGA DE IMAGEN
        '''
        #guardar la imagen
        resultImageUpload={}
        if cmpo in file:
            mFile = UploadFiles(drccn_imgn,nmbre_archvo,crr_drccn)
            resultImageUpload = mFile.upload(file[cmpo])
            
            
            #Check status uploadimage
            if resultImageUpload["status"] == "OK":
                arrayRespuesta['status']='OK'
                arrayRespuesta['retorno']=resultImageUpload["namefile"]
            else:
                arrayRespuesta['status']='error'
                arrayRespuesta['retorno']=errors.ERR_NO_IMGN_GRDDA
        else:
            arrayRespuesta['status']='error'
            arrayRespuesta['retorno']=errors.ERR_NO_ARCVO_DFNDO
            
        return arrayRespuesta