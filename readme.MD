# Kirja-backend

Projektin tarkoitus on luoda REST-backend kirjatietokannalle, joka säilöö listan omistamistani kirjoista.

## Ominaisuudet:
- Kirjan lisääminen kantaan ISBN:n perusteella
    - Lisämisen yhteydessä haetaan kirjan ja kirjoittajan nimi ja muita olennaisia tietoja julkisista ISBN-tietokannoista
- Kirjojen tietojen hakeminen kannasta ISBN:n perusteella

## TODO
- Kirjan poistaminen kannasta ISBN:n perusteella
- Kirjan tietojen muokkaaminen
- Kansikuvan lisääminen kirjalle
- Kirjojen tietojen hakeminen kannasta nimen ja kirjoittajan perusteella

## Docker-komennot kehitystä varten
`docker build -t uwsgi-books .`

`docker run --name uwsgi-books-container -p 8080:8080 -p 3307:3306 uwsgi-books`                                  
