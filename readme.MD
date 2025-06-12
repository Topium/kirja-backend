# Kirja-backend

Projektin tarkoitus on luoda REST-backend kirjatietokannalle, joka säilöö listan omistamistani kirjoista.

Ominaisuudet:
- Kirjan lisääminen kantaan ISBN:n perusteella
    - Lisämisen yhteydessä haetaan kirjan ja kirjoittajan nimi ja muita olennaisia tietoja julkisista ISBN-tietokannoista
- Kirjan poistaminen kannasta ISBN:n perusteella
- Kirjan tietojen muokkaaminen
- Kansikuvan lisääminen kirjalle
- Kirjojen tietojen hakeminen nimen, kirjoittajan ja ISBN:n perusteella

## Docker-komento
docker run --name uwsgi-books-container -p 8080:8080 -p 3307:3306 <image id>                                  
