'''
Clase para la gestion de usuarios del sistema

'''
import hashlib,socket,json # @UnresolvedImport
from IPy import IP
from flask import make_response # @UnresolvedImpor
from flask_restful import request, Resource
from wtforms import Form, validators, StringField
from SSI7X.Static.ConnectDB import ConnectDB  # @UnresolvedImport
from SSI7X.Static.Utils import Utils  # @UnresolvedImport
from SSI7X.Static.Ldap_connect import Conexion_ldap # @UnresolvedImport
from urllib.parse import urlparse
import SSI7X.Static.errors as errors  # @UnresolvedImport
import SSI7X.Static.labels as labels  # @UnresolvedImport
import SSI7X.Static.config as conf  # @UnresolvedImport
import SSI7X.Static.config_DB as dbConf # @UnresolvedImport 
import jwt #@UnresolvedImport
from SSI7X.ValidacionSeguridad import ValidacionSeguridad # @UnresolvedImport

'''
Declaracion de variables globales.
'''
lc_cnctn = ConnectDB()
Utils = Utils()
validacionSeguridad = ValidacionSeguridad()

'''
clase para la validacion de datos provenientes del POST en el login
'''
class UsuarioAcceso(Form):
    username = StringField(labels.lbl_nmbr_usrs,[validators.DataRequired(message=errors.ERR_NO_INGSA_USRO)])
    password = StringField(labels.lbl_cntrsna_usrs,[validators.DataRequired(message=errors.ERR_NO_INGRSA_CNTRSNA)])

'''
clase para la validacion de datos del POST en el cambio de contrasenna
'''
class UsroCmbioCntrsna(Form):
    cntrsna = StringField(labels.lbl_cntrsna_usrs,[validators.DataRequired(message=errors.ERR_NO_INGRSA_CNTRSNA)])
    cntrsna_nva = StringField(labels.lbl_nva_cntrsna,[validators.DataRequired(message=errors.ERR_NO_DB_INGRSR_NVA_CNTRSNA),validators.Length(min=conf.PW_MN_SIZE,message=errors.ERR_NO_MNM_CRCTRS),validators.Regexp('(?=.*\d)',message=errors.ERR_NO_MNMO_NMRO),validators.Regexp('(?=.*[A-Z])',message=errors.ERR_NO_MNMO_MYSCLA)])
    tkn = StringField('el token', [validators.DataRequired(message='Falta el token'),validators.Length(min=conf.SS_TKN_SIZE,message=errors.ERR_NO_TKN_INVLDO)])
    
'''
Objeto de autenticacion recibe la solicitud  del metodo a ejecutar
llamado en el argument page
'''
class AutenticacionUsuarios(Resource):
    def post(self, **kwargs):
        if kwargs['page'] == 'login':
            return self.login()
        elif kwargs['page'] == 'menu':
            return self.MenuDefectoUsuario()
        elif kwargs['page'] == 'cambio_password':
            return self.CmboCntrsna()
        elif kwargs['page'] == 'imagen_usuario':
            return self.BusquedaImagenUsuario()
            
    def login(self):    
        ingreso=False
      
        u = UsuarioAcceso(request.form)
        
        if not u.validate():
            return Utils.nice_json({"error":u.errors},400)
        IpUsuario = IP(socket.gethostbyname(socket.gethostname()))
        if IpUsuario.iptype() == 'PUBLIC':
            md5= hashlib.md5(request.form['password'].encode('utf-8')).hexdigest() 
            Cursor = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tblogins', 'lgn,cntrsna', "lgn='"+ request.form['username']+ "' and  cntrsna='"+md5+"'")
            if Cursor :
                if type(validacionSeguridad.validaUsuario(request.form['username'])) is dict:
                    ingreso=True                  
                else:
                    return validacionSeguridad.validaUsuario(request.form['username'])
            else:
                ingreso               
        elif IpUsuario.iptype() == 'PRIVATE':
            Cldap = Conexion_ldap()
            VerificaConexion = Cldap.Conexion_ldap(request.form['username'], request.form['password'])
            if VerificaConexion :
                if type(validacionSeguridad.validaUsuario(request.form['username'])) is dict:
                    ingreso=True                  
                else:
                    error = str(validacionSeguridad.validaUsuario(request.form['username']))
                    return Utils.nice_json({"error":error},400)    
            else:
                ingreso                 
                
        if  ingreso:
            
            tmpData = validacionSeguridad.ObtenerDatosUsuario(request.form['username'])[0]
            data = json.loads(json.dumps(tmpData, indent=2))
            
            _cookie_data =json.dumps(tmpData, sort_keys = True, indent=4)
            
            token = jwt.encode(data, conf.SS_TKN_SCRET_KEY, algorithm=conf.ENCRYPT_ALGORITHM).decode('utf-8')
            
            arrayValues={}
            device=Utils.DetectarDispositivo(request.headers.get('User-Agent'))
            arrayValues['key']= str(token)
            arrayValues['ip']=str(IpUsuario)
            arrayValues['dspstvo_accso']=str(device)
            arrayValues['id_lgn_ge']=str(data['id_lgn_ge'])
            self.InsertGestionAcceso(arrayValues)
            response = make_response( '{"access_token":"'+str(token)+'","cookie_higia":'+ str(_cookie_data) +'}',200)
            response.headers['Content-type'] = "application/json"
            response.headers['charset']="utf-8"
            response.headers["Access-Control-Allow-Origin"]= "*"
            return response
        else:
            return Utils.nice_json({"error":errors.ERR_NO_USRO_CNTSN_INVLD},400)
    
   
    def MenuDefectoUsuario(self):
        token = request.headers['Authorization']
       
        if token:
            validacionSeguridad.ValidacionToken(token) 
            if validacionSeguridad :
                DatosUsuario = jwt.decode(token, conf.SS_TKN_SCRET_KEY, 'utf-8')
                id_lgn_prfl_scrsl = validacionSeguridad.validaUsuario(DatosUsuario['lgn'])
                
                if type(id_lgn_prfl_scrsl) is not dict:
                    return id_lgn_prfl_scrsl
                
                strQuery = 'SELECT a."text",a.id,a.parentid,a.lnk as enlace,(d.id is Not Null) favorito '\
                                'FROM (select  c.dscrpcn as text ,  b.id_mnu as id , c.id_mnu as parentid , c.lnk ,a.id Mid,c.ordn '\
                                'FROM ssi7x.tblogins_perfiles_menu a INNER JOIN '\
                                'ssi7x.tbmenu_ge b on a.id_mnu_ge=b.id INNER JOIN '\
                                'ssi7x.tbmenu c ON b.id_mnu = c.id '\
                                'where a.estdo=true  and b.estdo=true  and a.id_lgn_prfl_scrsl =' +str(id_lgn_prfl_scrsl['id_prfl_scrsl'])+ ' '\
                                ' )a LEFT JOIN ssi7x.tbfavoritosmenu d on d.id_lgn_prfl_mnu = a.Mid ORDER BY  cast(a.ordn as integer)'
                
                Cursor = lc_cnctn.queryFree(strQuery)
                if Cursor :    
                    data = json.loads(json.dumps(Cursor, indent=2))
                    return Utils.nice_json(data,200)
                else:
                    return Utils.nice_json({"error":errors.ERR_NO_USRO_SN_MNU},400)
            else:
                return Utils.nice_json({"error":errors.ERR_NO_SN_SSN},400)
            
        else:
            return Utils.nice_json({"error":errors.ERR_NO_SN_PRMTRS},400)
        
    def CmboCntrsna(self):
        u = UsroCmbioCntrsna(request.form)
        if not u.validate():
            return Utils.nice_json({"status":"Error","error":u.errors,"user":"null"},200)
    
    def BusquedaImagenUsuario(self):
        lc_url = request.url
        lc_prtcl = urlparse(lc_url)    
        Cursor = lc_cnctn.queryFree(" select "\
                                 " id ,"\
                                 " lgn ,"\
                                 " fto_usro,"\
                                 " nmbre_usro, "\
                                 " estdo "\
                                 " from ssi7x.tblogins where lgn = '"+str(request.form['username'])+"'")
        if Cursor :
            data = json.loads(json.dumps(Cursor[0], indent=2))
            if data['estdo']:
                if data['fto_usro']:
                    return Utils.nice_json({"fto_usro":lc_prtcl.scheme+'://'+conf.SV_HOST+':'+str(conf.SV_PORT)+'/static/img/'+data['fto_usro']},200)
                else:
                    return Utils.nice_json({"fto_usro":"null"},200)
            else:
                return Utils.nice_json({"error":errors.ERR_NO_TNE_PRFL,lc_prtcl.scheme+'://'+"fto_usro":conf.SV_HOST+':'+str(conf.SV_PORT)+'/static/img/'+data['fto_usro']},200)
        else:
            return Utils.nice_json({"error":errors.ERR_NO_TNE_PRMTDO_ACCDR},400)

        
    def InsertGestionAcceso(self,objectValues):
        lc_cnctn.queryInsert(dbConf.DB_SHMA+".tbgestion_accesos", objectValues)        
        
                