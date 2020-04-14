import logging
import threading
import time
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-2s) %(message)s')

class Taller(object):
    def __init__(self, start=0):
        self.condicionMangasMAX = threading.Condition()
        self.condicionMangasMIN = threading.Condition()
        self.mangas = 0
        self.cuerpos = 0
        #prenda

def incrementarManga(self):
    with self.condicionMangasMAX:
        if self.mangas >= 10:
            logging.debug("No hay espacio para mangas")
            self.condicionMangasMAX.wait()
        else:
            self.mangas += 1
            logging.debug("Manga creada, mangas=%s",self.mangas)
        with self.condicionMangasMIN:
            if self.mangas >= 2:
                logging.debug("Existen suficientes mangas")
                self.condicionMangasMIN.notify()

def decrementarManga(self):
    with self.condicionMangasMIN:
        while not self.mangas>=2:
            logging.debug("Esperando mangas")
            self.condicionMangasMIN.wait()
            self.mangas -= 2
            logging.debug("Mangas tomadas, mangas=%s",self.mangas)
        with self.condicionMangasMAX:
            logging.debug("Hay espacio para mangas")
            self.condicionMangasMAX.notify()

def getMangas(self):
    return (self.mangas)

def incrementarCuerpo(self):
    #verificar que la cesta de cuerpos no esté llena
    with self.condicionCuerposMAX:
        while not self.cuerpos >= 5:
            logging.debug("No hay espacio para cuerpos")
            self.condicionCuerposMAX.wait()
        else:
            self.cuerpos += 1
            logging.debug("Cuerpo creado, cuerpos=%s",self.cuerpos)
    #notificar que hay cuerpos disponibles
        with self.condicionMangasMAX:
            if self.mangas >= 10:
                logging.debug("Hay cuerpos disponibles")
                self.condicionMangasMAX.notify()

def crearManga(Taller):
    while (Taller.getMangas() <= 10):
        Taller.incrementarManga()
        time.sleep(5)

def crearCuerpo(Taller):
    while (Taller.getMangas() >= 0):
        # incrementarCuerpo (antes de decrementar
        # manga se debe validar que haya cupo en
        # la canasta de cuerpos)
        Taller.incrementarCuerpo()
        Taller.decrementarManga()
        time.sleep(1)

def ensamblaPrenda(Taller):
    logging.debug('Ensamblando todo')
    taller = Taller()
    Lupita = threading.Thread(name='Lupita(mangas)', target=crearManga, args=(taller,))
    Sofia = threading.Thread(name='Sofía(cuerpos)', target=crearCuerpo, args=(taller,))
    persona3 = threading.Thread(name='persona(ensamble)', target=ensamblaPrenda,args=(taller,))
    Lupita.start()
    Sofia.start()
    Lupita.join()
    Sofia.join()
    persona3.join()
    persona3.start()