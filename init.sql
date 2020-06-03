create table luogo
(
    ID         int(11) unsigned auto_increment primary key,
    Indirizzo  varchar(255) null,
    Lat        double       null,
    Lon        double       null,
    NomeLocale varchar(50)  null,
    DataInizio timestamp    null,
    DataFine   timestamp    null
);