# CarePath API
API Rest in Flask per lo strumento comunale di segnalazione contagi Covid-19

## Installazione

## Account Sviluppatore ARCGIS
* Creare un account al seguente indirizzo: https://developers.arcgis.com/sign-up/
* Effettuare l'accesso e creare una nuova app
* Recuperare il proprio ```client id``` e ```client secret``` dalla Overview della propria app

### Inizializzazione database
* Effettuare l'accesso al database che verrà utilizzato dalla nostra app
* Caricare il file ```init.sql```

### Variabili d'ambiente
* Creare un file chiamato ```.env``` all'interno della root del progetto, dove si trova ```app.py```
### Configurare API ARCGIS
* Creare una riga all'interno del file ```.env```: ```CLIENT_ID="{il_suo_client_id}"```
* Creare una riga all'interno del file ```.env```: ```CLIENT_SECRET="{il_suo_client_secret}"```
### Configurare Database
* Creare una riga all'interno del file ```.env```: ```DATABASE_HOST="{il_suo_host_database}"```
* Creare una riga all'interno del file ```.env```: ```DATABASE_USER="{il_suo_utente_database}"```
* Creare una riga all'interno del file ```.env```: ```DATABASE_PASSWORD="{la_sua_password_database}"```
* Creare una riga all'interno del file ```.env```: ```DATABASE_DB="{il_suo_nome_del_database}"```
