from flask_restful import  Resource,request
from Static.Utils import Utils  # @UnresolvedImport
from Static.ConnectDB import ConnectDB  # @UnresolvedImport
import time,json
import requests 
import Static.labels as labels # @UnresolvedImport



Utils = Utils()
pc_cnnctDB = ConnectDB()
pd_fcha_act = time.ctime()

class Contratos(Resource):

    def post(self,**kwargs):

        if kwargs['page']=='crear':
            return self.crear()
        if kwargs['page']=='listar':
            return self.listar()
        if kwargs['page']=='actualizar':
            return self.actualizar()
     

    def crear(self):
            
        #ln_opcn_mnu = request.form["id_mnu_ge"]
        #ln_id_undd_ngco = request.form["id_undd_ngco"]
        #key = request.headers['Authorization']
        #validacionSeguridad = ValidacionSeguridad()
        print('crear')
   
    def actualizar(self):   
        
        #ln_opcn_mnu = request.form["id_mnu_ge"]
        #key = request.headers['Authorization']
        #validacionSeguridad = ValidacionSeguridad() 
        print('actualizar')
    
    def listar(self):   
        
       
        #key = request.headers['Authorization']
        #validacionSeguridad = ValidacionSeguridad()
                      
        lc_rsltdo =  requests.post('http://127.0.0.1:5001/api/contratos/listar', data=request.form)
        return  Utils.nice_json(lc_rsltdo.json(),200)
        
                