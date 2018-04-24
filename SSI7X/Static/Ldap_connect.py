'''
Created on 10/01/2018

@author: LUIS:ARAGON
'''
import ldap3
import ssl
import Static.config as conf  # @UnresolvedImport

class Conexion_ldap():
    def Conexion_ldap(self,user_ldap,password_ldap):
        tls_configuration = ldap3.Tls(validate=ssl.CERT_NONE,
                                      version=ssl.PROTOCOL_TLSv1_2)
        server = ldap3.Server(host=conf.LDAP_HOST, port=conf.LDAP_PORT,
                              use_ssl=False, tls=tls_configuration,
                              get_info=ldap3.ALL)
        c = ldap3.Connection(server, version=3,
                               auto_bind=False,
                               raise_exceptions=False,
                               user=conf.LDAP_HOST+'\\'+user_ldap,
                               password=password_ldap,
                               authentication=ldap3.NTLM)
        if  c.bind():
            return True
        else:
            return False
