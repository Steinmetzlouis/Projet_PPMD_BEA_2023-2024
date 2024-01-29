#Librairies utiles
from datetime import datetime, timedelta


def nearest_table_date(user_date, db_table_dates):
    """
    Détermine la date la plus proche de la date fournie par l'utilisateur dans une liste des dates de mise à jour de la base de données

    Args:
        user_date (str): La date fournie par l'utilisateur au format "YYYY-MM-DD".
        db_table_dates (list): Liste des dates des tables de la base de données au format "YYYY-MM-DD".

    Returns:
        str or None: La date la plus proche de la date fournie par l'utilisateur dans la liste des dates
                     des tables de la base de données, au format "YYYY-MM-DD". Renvoie None si la liste est vide.
    """
    
    # Convertir la date fournie par l'utilisateur en objet datetime
    user_date_object = datetime.strptime(user_date, "%Y-%m-%d")

    # Initialisation de l'index de la date la plus proche
    nearest_date_index = -1

    # Parcourir la liste des dates des tables de la base de données
    for i, date in enumerate(db_table_dates):

        # Convertir la date de la table en objet datetime
        table_date_object = datetime.strptime(date, "%Y-%m-%d")

        # Vérifier si la date de la table est antérieure à la date fournie par l'utilisateur
        if table_date_object < user_date_object:
            
            # Calculer la différence de jours entre les deux dates
            if i == 0:
                old_diff = abs((table_date_object - user_date_object).days)
            else:
                new_diff = abs((table_date_object - user_date_object).days)

                # Comparer avec la différence précédente pour déterminer la date la plus proche
                if new_diff < old_diff:
                    old_diff = new_diff
                    nearest_date_index = i

    # Si aucune date n'est trouvée avant la date fournie par l'utilisateur
    if nearest_date_index == -1:
        return None
    else:
        # Renvoyer la date la plus proche de la date fournie par l'utilisateur
        return db_table_dates[nearest_date_index]
