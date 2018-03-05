'''
Created on 23/01/2018

@author: EDISON.BEJARANO
'''

from SSI7X.Static.ConnectDB import ConnectDB  # @UnresolvedImport
from SSI7X.Static.Utils import Utils  # @UnresolvedImport
from flask_restful import request, Resource
from wtforms import Form, validators, StringField , IntegerField
from SSI7X.ValidacionSeguridad import ValidacionSeguridad  # @UnresolvedImport
import SSI7X.Static.labels as labels # @UnresolvedImport
import SSI7X.Static.errors as errors  # @UnresolvedImport
import SSI7X.Static.opciones_higia as optns  # @UnresolvedImport
import SSI7X.Static.config_DB as dbConf # @UnresolvedImport
import SSI7X.Static.config as conf  # @UnresolvedImport
import time,json,jwt


#Declaracion de variables globales
Utils = Utils()
lc_cnctn = ConnectDB()
fecha_act = time.ctime()
validacionSeguridad = ValidacionSeguridad()

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
    
    def crear(self):
        key = request.headers['Authorization']
        ln_opcn_mnu = request.form["id_mnu_ge"]
        ln_id_undd_ngco = request.form["id_undd_ngco"]
        if key:
            validacionSeguridad.ValidacionToken(key)
            if validacionSeguridad :
                token =lc_cnctn.querySelect(dbConf.DB_SHMA+'.tbgestion_accesos', "token", "key='"+key+"' and estdo is true")[0]
                DatosUsuarioToken = jwt.decode(token["token"], conf.SS_TKN_SCRET_KEY+key, 'utf-8')
                if validacionSeguridad.Principal(key,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
                    datosUsuario = validacionSeguridad.ObtenerDatosUsuario(DatosUsuarioToken['lgn'])[0]
                    arrayValues={}
                    arrayValues['cdgo'] = request.form["cdgo"]
                    arrayValues['dscrpcn'] = request.form["dscrpcn"]
                    ##validacion de datos repetidos
                    Cursor = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tbperfiles', 'cdgo', "cdgo='"+str(arrayValues['cdgo'])+"' or dscrpcn like '%"+str(arrayValues['dscrpcn'])+"%' ")
                    if Cursor :
                        return Utils.nice_json({"error":errors.ERR_RGSTRO_RPTDO},400)
                       
                    ln_id_prfl =  lc_cnctn.queryInsert(dbConf.DB_SHMA+".tbperfiles", arrayValues,'id')
                    if ln_id_prfl:
                        arrayValuesDetalle={}
                        arrayValuesDetalle['id_prfl'] = str(ln_id_prfl)
                        arrayValuesDetalle['id_undd_ngco'] = str(ln_id_undd_ngco)
                        arrayValuesDetalle['id_lgn_crcn_ge'] = str(datosUsuario['id_lgn_ge'])
                        arrayValuesDetalle['id_lgn_mdfccn_ge'] = str(datosUsuario['id_lgn_ge'])  
                        arrayValuesDetalle['fcha_mdfccn'] = str(fecha_act)
                        ln_id_prfl_une = lc_cnctn.queryInsert(dbConf.DB_SHMA+".tbperfiles_une", arrayValuesDetalle,'id')
                        return Utils.nice_json({"success":labels.SCCSS_RGSTRO_EXTSO,"id":str(ln_id_prfl_une)},200)
                    else:    
                        return Utils.nice_json({"error":errors.ERR_PRBLMS_GRDR},400) 
                else:
                    return Utils.nice_json({"error":errors.ERR_NO_ATRZCN},400)
            else:
                return Utils.nice_json({"error":errors.ERR_NO_SN_SSN}, 400)
            
        else:
            return Utils.nice_json({"error":errors.ERR_NO_SN_PRMTRS}, 400)

        
    def listar(self):
        
        ln_opcn_mnu = request.form["id_mnu_ge"]
        token = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()
        
        if validacionSeguridad.Principal(token,ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
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
                return Utils.nice_json({"success":labels.INFO_NO_DTS},200)
        else:
            return Utils.nice_json({"error":errors.ERR_NO_ATRZCN},400)       
        
    def actualizar(self):
        
        lob_rspsta = DatosUpdate(request.form)
        if not lob_rspsta.validate(): 
            return self.Utils.nice_json({"error":lob_rspsta.errors},400)
        
        ln_opcn_mnu = request.form["id_mnu_ge"]
        token = request.headers['Authorization']
        validacionSeguridad = ValidacionSeguridad()
        
        if validacionSeguridad.Principal(token, ln_opcn_mnu,optns.OPCNS_MNU['Perfiles']):
            DatosUsuarioToken = jwt.decode(token, conf.SS_TKN_SCRET_KEY, 'utf-8')
            datosUsuario = validacionSeguridad.ObtenerDatosUsuario(DatosUsuarioToken['lgn'])[0]    
                            
            lc_cdgo     = request.form["cdgo"]
            lc_dscrpcn  = request.form["dscrpcn"]  
            ln_id_prfl_une = request.form["id_prfl_une"]
            lb_estdo    = request.form["estdo"]   
            
            CursorValidar = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tbperfiles', 'id'," cdgo = '"+str(lc_cdgo)+"' or dscrpcn like '%"+str(lc_dscrpcn)+"%'")
            print(CursorValidar)                    
            if CursorValidar:
                print('dupicado')
                return Utils.nice_json({"error":errors.ERR_RGSTRO_RPTDO},400)       
                        
            arrayValues={}
            arrayValuesDetalle={}
            #Actualizo tabla une
            arrayValuesDetalle['id_lgn_mdfccn_ge']  =  str(datosUsuario['id_lgn_ge'])  
            arrayValuesDetalle['estdo']             =  lb_estdo            
            arrayValuesDetalle['fcha_mdfccn']       =  str(self.fecha_act)               
            lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str('tbperfiles_une'), arrayValuesDetalle,'id='+str(ln_id_prfl_une))
            #obtengo id_lgn a partir del id_lgn_ge
            Cursor = lc_cnctn.querySelect(dbConf.DB_SHMA +'.tbperfiles_une', 'id_prfl', "id="+ln_id_prfl_une)
            if Cursor :
                data        = json.loads(json.dumps(Cursor[0], indent=2))
                ln_id_prfl  = data['id_prfl']
                #Actualizo tabla principal
                arrayValues['id']     = ln_id_prfl
                arrayValues['cdgo']   = str(lc_cdgo)
                arrayValues['dscrpcn']= lc_dscrpcn
                arrayValues['estdo']  = lb_estdo
                lc_cnctn.queryUpdate(dbConf.DB_SHMA+"."+str('tbperfiles'), arrayValues,'id='+str(ln_id_prfl))
                return Utils.nice_json({"success":labels.SCCSS_ACTLZCN_EXTSA},200) 
            else:    
                return Utils.nice_json({"error":errors.ERR_PRBLMS_GRDR},400)
        else:
            return Utils.nice_json({"error":errors.ERR_NO_ATRZCN},400)       