# snmpv3brutem
# snmpv3brutem.py
**Auteur :** Eric Mboma Kakese
** git clone https://github.com/Eric-mboma/snmpv3brutem ** pour télécharger les fichiers

**Article de blog ici :** https://applied-risk.com/resources/brute-forcing-snmpv3-authentication

Il s'agit d'un outil permettant d'obtenir des mots de passe d'authentification en clair à partir de paquets SNMPv3.

Un seul paquet SNMPv3 contient toutes les informations nécessaires pour calculer et forcer brutalement les mots de passe.

Ce bruteforcer s'inspire d'autres projets là-bas; mais le but de ce script est d'effectuer tous les calculs de manière native en python, en supprimant toutes les fonctionnalités inutiles pour maximiser la vitesse.

## Utilisation :

```envelopper
$ python3 snmpv3brutem.py -h
utilisation : snmpv3brutem.py [-h] [-a [{md5,sha,all}]] [-w LISTE DE MOT]
                   [-W [MOT UNIQUE [MOT UNIQUE ...]]] [-p FICHIERPCAP]
                   [-m SNMP SNMP SNMP] [-v]

snmpv3brutem.py - Bruteforcer d'authentification SNMPv3

arguments facultatifs :
  -h, --help affiche ce message d'aide et quitte
  -a [{md5,sha,all}] Utiliser md5, sha ou les deux pour l'algorithme de hachage (par défaut : all)
  -w WORDLIST Spécifie la liste de mots à utiliser (1 mot par ligne)
  -W [MOT UNIQUE [MOT UNIQUE ...]]
                        Spécifiez les mots à utiliser comme mot de passe pour les tests
  -p PCAPFILE Spécifie le fichier .pcap/.pcapng avec les données SNMP
  -m SNMP SNMP SNMP Spécifiez manuellement msgAuthoriativeEngineID, msgAuthenticationParameters et msgWhole depuis Wireshark (dans cet ordre)
  -v Verbeux ; imprimer les messages d'erreur
  ```
Ce programme peut lire un PCAP (-p), extraire les informations nécessaires des sessions SNMP et utiliser une liste de mots (-w) pour essayer de forcer brutalement le mot de passe d'authentification.

Exemple : `python3 snmpv3brutem.py -w liste de mots.txt -p foo.pcapng`

Les mots peuvent être soumis pour test (-W) au lieu d'une liste de mots ; les mots doivent être séparés par un espace.

Exemple : `python3 snmpv3brutem.py -W password1 password2 password 3 -p foo.pcapng`

Les mots peuvent également être soumis avec une liste de mots ; le programme essaiera les mots avant d'utiliser la liste de mots.

Exemple : `python3 snmpv3brutem.py -W password1 password2 -p foo.pcapng -w wordlist.txt`

Les variables SNMP requises peuvent être soumises à la place d'un PCAP à l'aide de l'option "-m". Tout d'abord, recherchez un paquet SNMPv3 dans Wireshark. Pour msgAuthoritativeEngineID et msgAuthenticationParameters, faites un clic droit sur le champ de paquet du même nom et sélectionnez "Copier en tant que flux hexadécimal". Pour msgWhole, faites un clic droit sur Simple Network Management Protocol et sélectionnez "Copier en tant que flux hexadécimal".

Exemple: `python3 snmpv3brutem.py -m <msgAuthoriativeEngineID> <msgAuthenticationParameters> <msgWhole> -w wordlist.txt`

Example: `python3 snmpv3brutem.py -m 80001f888056417b0bd201d85d00000000 a34b57081ff0cef821e4da43 3081dc020103301002043cabfa64020205c0040103020103043f303d041180001f888056417b0bd201d85d00000000020101020200a20409736e6d705f75736572040ca34b57081ff0cef821e4da430408bec2e5f547aaa89c048183dfe158807f83a660d37264c7f397a8a42c237988ee829c52b003f6d772df683c51acb56bb327a36ee590e1d65c9466e9d18a48e80539e5fff12006d2fba6bc61756956285b84bafe773b6359d2273db3b6e49f89a6609a86ac5f440d4bfa55b17af5a81db1fa0030402bba9befad240addc41d9b394d0fb2c4a3f5ffde3730485cdaf6`

*Remarque : des exemples de pcaps et de listes de mots sont inclus dans le répertoire test_files.*

## Repères
Lenovo Ideapad(15 pouces, 2020)\
Processeur Intel Core duo à 1,86 GHz\
4 Go DDR4\
**~800 mots de passe par seconde**

## Fonctionnalité future :
* ~~Ajouter la fonctionnalité MD5.~~
* ~~ Détection automatique de MD5/SHA.~~ Ce n'est pas un moyen apparent de le faire
* ~~Lire pcap directement et obtenir les valeurs pertinentes~~
* Déplacer le traitement vers le GPU pour plus de vitesse
* ~~ Activer les arguments de ligne de commande pour les variables ~~
* Ajouter des options de longueur de mot de passe minimale et maximale

## Références
Processus d'authentification SNMPv3 : https://vad3rblog.wordpress.com/2017/09/11/snmp/

Calcul Snmpkey simplifié à partir de : https://github.com/TheMysteriousX/SNMPv3-Hash-Generator
