import os
import sys
from datetime import datetime, date
import subprocess
import platform
from importlib import reload, import_module
import site
from PyQt5.QtWidgets import QMessageBox


def nearest_table_date(user_date, db_table_dates):
    """
    Détermine la date la plus proche de la date fournie par l'utilisateur dans une liste des dates de mise à jour de la base de données

    Args:
        user_date (date): La date fournie par l'utilisateur.
        db_table_dates (list): Liste des dates des tables de la base de données au format "YYYY-MM-DD".

    Returns:
        str or None: La date la plus proche de la date fournie par l'utilisateur dans la liste des dates
                     des tables de la base de données, au format "YYYY-MM-DD". Renvoie None si la liste est vide.
    """
    # Initialisation de l'index de la date la plus proche
    nearest_date_index = -1

    # Parcourir la liste des dates des tables de la base de données
    for i, table_date in enumerate(db_table_dates):

        # Vérifier si la date de la table est antérieure à la date fournie par l'utilisateur
        if table_date < user_date:
            
            # Calculer la différence de jours entre les deux dates
            if i == 0:
                old_diff = abs((table_date - user_date).days)
            else:
                new_diff = abs((table_date - user_date).days)

                # Comparer avec la différence précédente pour déterminer la date la plus proche
                if new_diff < old_diff:
                    old_diff = new_diff
                    nearest_date_index = i

    # Si aucune date n'est trouvée avant la date fournie par l'utilisateur
    if nearest_date_index == -1:
        return None
    else:
        # Renvoyer la date la plus proche de la date fournie par l'utilisateur
        return db_table_dates[nearest_date_index].strftime("%Y_%m_%d")

def msg_box(title, text, icon, parent=None):
    """Open a QMessageBox with title, text and icon

    Parameters
    ----------
    title : str
        Title name for the message box
    text : str
        Text to be displayed inside message box
    icon : `QMessageBox.Icon`
        Icon for the message box
    parent : `QWidget`, optional
        Parent window

    Examples
    --------
    >>> msg_box("Animeteo : paramètre manquant", "Sélectionner une couche météo", QMessageBox.Warning, mainWindow)
    """
    msg = QMessageBox(parent=parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.exec_()


def import_pkg_mod(module=None, version=None):
    """Test package import and install package if missing

    Parameters
    ----------
    module : str
        Module or package name
    version : str or int
        Package version
    """
    if module:
        try:
            import_module(module)
        except (ModuleNotFoundError, ImportError) as e:
            pip_pkg_version = "{}{}".format(module, "=={}".format(version) if version else "")
            if platform.system() == 'Windows':
                # sys.executable = 'C:\\Program Files\\QGIS 3.22.7\\bin\\qgs-ltr-bin.exe'
                # os.path.dirname(os.path.dirname(sys.executable)) -> 'C:\\Program Files\\QGIS 3.22.7'
                OSGeo4W_bat = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "OSGeo4W.bat")
                subprocess.check_call([OSGeo4W_bat, 'pip', 'install', pip_pkg_version])
            elif platform.system() == 'Darwin':
                # sys.executable = '/Applications/QGIS-LTR.app/Contents/MacOS/QGIS'
                # os.path.dirname(sys.executable) -> '/Applications/QGIS-LTR.app/Contents/MacOS'
                python3 = os.path.join(os.path.dirname(sys.executable), "bin", "python3")
                subprocess.check_call([python3, '-m', 'pip', 'install', pip_pkg_version])
            elif platform.system() == 'Linux':
                # sys.executable = '/usr/bin/python3'
                # if apt_package is not None:
                #     subprocess.check_call(['apt-get', 'install', '-y', apt_package],
                #                           stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT)
                # else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_pkg_version])
            # mod = import_module(module)
    reload(site)
