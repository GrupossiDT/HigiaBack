import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename
import Static.config as conf  # @UnresolvedImport 

class correo:
    def enviarCorreo(para,asunto,data,files=None):
        mensaje = MIMEMultipart()
        mensaje['from'] = conf.SMTP_USER
        mensaje['to'] = para
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(data,'html'))
        
        for f in files or []:
            with open(f, "rb") as fil:
                part = MIMEApplication(fil.read(),Name=basename(f))
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
                mensaje.attach(part)
        server = smtplib.SMTP("correo.grupossi.com",587)
        server.starttls()
        server.login(mensaje['from'], conf.SMTP_USER_PSWD)
        server.sendmail(mensaje['from'], mensaje['to'],mensaje.as_string())
        server.quit()