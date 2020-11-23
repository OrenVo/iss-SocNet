-- noinspection NonAsciiCharactersForFile

/*****************************************
 * @file Initialize sql database for iis project
 * @author Roman Fulla  <xfulla00>
 * @author Vojtěch Ulej <xulejv00>
 *****************************************/
DROP DATABASE IF EXISTS iis_soc_net;
CREATE DATABASE IF NOT EXISTS iis_soc_net;
USE iis_soc_net;
/**     DROP     **/
DROP TABLE IF EXISTS Uživatel;
DROP TABLE IF EXISTS Skupina;
DROP TABLE IF EXISTS Vlákno;
DROP TABLE IF EXISTS Zpráva;
DROP TABLE IF EXISTS Moderuje;
DROP TABLE IF EXISTS Je_členem;
DROP TABLE IF EXISTS Žádosti;
DROP TABLE IF EXISTS Hodnocení;

/**     CREATE TABLES     **/
CREATE TABLE IF NOT EXISTS Uživatel (
    ID                  INT PRIMARY KEY AUTO_INCREMENT,

    Jméno               NVARCHAR (20),
    Příjmení            NVARCHAR (20),
    Práva               TINYINT DEFAULT 0,
    Heslo               CHAR (64) NOT NULL,               -- Hash hesla (sha256)
    Profilová_fotka     MEDIUMBLOB,
    Login               VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Skupina (
    ID                  INT PRIMARY KEY AUTO_INCREMENT,
    Název               NVARCHAR(30) NOT NULL,
    Práva_čtení         TINYINT DEFAULT 0,
    Popis               NVARCHAR(2000),
    Ikona               MEDIUMBLOB,

    Uživatel_ID         INT NOT NULL,
    CONSTRAINT CK_uživatel FOREIGN KEY (Uživatel_ID) REFERENCES Uživatel (ID) ON DELETE CASCADE     -- vlastní

);

CREATE TABLE IF NOT EXISTS Moderuje (   -- Vazba <uživatel moderuje skupinu>
    Uživatel    INT NOT NULL,
    Skupina     INT NOT NULL,
    CONSTRAINT PK_moderuje PRIMARY KEY (Uživatel,Skupina),
    CONSTRAINT CK_uživatel_moderuje FOREIGN KEY (Uživatel) REFERENCES Uživatel (ID) ON DELETE CASCADE,
    CONSTRAINT CK_skupina_moderuje FOREIGN KEY (Skupina) REFERENCES Skupina (ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Je_členem(   -- Vazba <uživatel je členem skupinu>
    Uživatel    INT NOT NULL,
    Skupina     INT NOT NULL,
    CONSTRAINT PK_je_členem PRIMARY KEY (Uživatel, Skupina),
    CONSTRAINT CK_uživatel_je_členem FOREIGN KEY (Uživatel) REFERENCES Uživatel (ID) ON DELETE CASCADE,
    CONSTRAINT CK_skupina_je_členem FOREIGN KEY (Skupina) REFERENCES Skupina (ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Žádosti(     -- Vazby <uživatel žádá o členství/ práva moderátora>
    Uživatel    INT NOT NULL,
    Skupina     INT NOT NULL,
    Datum_čas   TIMESTAMP,
    Členství    BOOL DEFAULT TRUE,
    CONSTRAINT PK_žádosti PRIMARY KEY (Uživatel, Skupina,Členství),
    CONSTRAINT CK_uživatel_žádosti FOREIGN KEY (Uživatel) REFERENCES Uživatel (ID) ON DELETE CASCADE,
    CONSTRAINT CK_skupina_žádosti FOREIGN KEY (Skupina) REFERENCES Skupina (ID) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Vlákno (
    Název               NVARCHAR(30) NOT NULL,
    Popis               NVARCHAR(2000),

    Skupina_ID          INT NOT NULL,   -- CK
    CONSTRAINT PK_vlákno PRIMARY KEY (Skupina_ID, Název),
    CONSTRAINT CK_skupina_vlákno FOREIGN KEY (Skupina_ID) REFERENCES Skupina (ID) ON DELETE CASCADE    -- má
);

CREATE TABLE IF NOT EXISTS Zpráva (
    ID              INT NOT NULL UNIQUE AUTO_INCREMENT,
    Obsah           NVARCHAR(2000),
    `Rank`          INT DEFAULT 0,
    Datum_čas       TIMESTAMP DEFAULT NOW(),

    Uživatel_ID     INT,  -- ck
    Název_vlákna    NVARCHAR(30) NOT NULL,
    ID_skupiny      INT NOT NULL,
    CONSTRAINT Pk_zpráva PRIMARY KEY (ID, Název_vlákna, ID_skupiny),
    CONSTRAINT CK_uživatel_zpráva FOREIGN KEY (Uživatel_ID) REFERENCES Uživatel (ID) ON DELETE SET NULL,
    CONSTRAINT CK_vlákno_zpráva FOREIGN KEY (ID_skupiny, Název_vlákna) REFERENCES Vlákno (Skupina_ID, Název) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Hodnocení (
    Uživatel     INT NOT NULL,
    Zpráva       INT NOT NULL,
    Autor_zprávy INT NOT NULL,
    Název_vlákna    NVARCHAR(30) NOT NULL,
    ID_skupiny      INT NOT NULL,
    CONSTRAINT PK_je_členem PRIMARY KEY (Uživatel, Zpráva, Název_vlákna,ID_skupiny),
    CONSTRAINT CK_uživatel_hodnocení FOREIGN KEY (Uživatel) REFERENCES Uživatel (ID) ON DELETE CASCADE,
    CONSTRAINT CK_vlákno_hodnocení FOREIGN KEY (Zpráva, Název_vlákna, ID_skupiny) REFERENCES Zpráva (ID, Název_vlákna, ID_skupiny) ON DELETE CASCADE
);
