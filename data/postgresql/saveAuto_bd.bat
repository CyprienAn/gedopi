echo off
SET JOUR=%date:~-10,2%
SET ANNEE=%date:~-4%
SET MOIS=%date:~-7,2%
SET HEURE=%time:~0,2%
SET MINUTE=%time:~3,2%
SET SECOND=%time:~-5,2%

IF "%time:~0,1%"==" " SET HEURE=0%HEURE:~1,1%

REM SET REPERTOIR=C:\Users\Cyprien\.qgis2\python\plugins\gedopi\data\postgresql
SET REPERTOIR= %~dp0

REM SET FICHIER=%REPERTOIR%\Sauvegarde_du_%JOUR%_%MOIS%_%ANNEE%_A_%HEURE%_%MINUTE%.backup
SET FICHIER=%REPERTOIR%sauvegarde\Sauvegarde_du_%JOUR%_%MOIS%_%ANNEE%_A_%HEURE%_%MINUTE%.backup

REM IF NOT exist "%REPERTOIR%" md "%REPERTOIR%"

REM "C:\Program Files\PostgreSQL\9.5\bin\pg_dump.exe"  -h localhost -p 5432 -U postgres -Fc gedopi >%FICHIER%
"C:\Program Files\PostgreSQL\9.5\bin\pg_dump.exe"  --host localhost --port 5432 --username "postgres" --role "postgres" --format custom --blobs --encoding UTF8 --verbose --file %FICHIER% --schema "data" "gedopi"

msgbox Sauvegarde fini dans %FICHIER%


