# Rezumat implementare - Sportal MVP

## Descriere generala

Aplicatia este un MVP pentru gestionarea rezervarilor de resurse sportive, construit cu Django (backend + template rendering) si JavaScript simplu pe frontend pentru apeluri API.

Sunt doua tipuri de utilizatori:
- **Client**: creeaza si urmareste cereri de rezervare.
- **Angajat**: confirma sau respinge cererile primite pentru locatia lui.

## Functionalitati implementate

### 1) Autentificare si conturi
- Login/Logout standard Django.
- Inregistrare cont client prin pagina dedicata.
- Rolul de angajat este modelat prin `EmployeeProfile` asociat utilizatorului.

### 2) Model de date
- `Company` - companie/sala/club.
- `Location` - locatie asociata unei companii.
- `SportResource` - teren/resursa sportiva (tip sport + pret/ora).
- `EmployeeProfile` - leaga un user de o locatie ca angajat.
- `BookingRequest` - cerere de rezervare cu status:
  - `pending`
  - `confirmed`
  - `rejected`
  - `cancelled`

### 3) Flux client
- Clientul vede dashboard-ul cu resursele disponibile.
- Poate verifica ocuparea intervalelor prin endpoint-ul de disponibilitate.
- Poate trimite cerere noua pentru un interval.
- Poate vedea istoricul cererilor proprii.

### 4) Flux angajat
- Angajatul vede cererile `pending` pentru locatia sa.
- Poate:
  - confirma o cerere;
  - respinge o cerere (optionala motivare).

### 5) Reguli de business
- Nu se permit cereri suprapuse pe acelasi teren, in acelasi interval.
- La confirmare se verifica din nou conflictul de interval (siguranta concurenta).
- Operatiile critice sunt facute in tranzactii (`transaction.atomic`) cu lock (`select_for_update`).

### 6) Notificari email
- Dupa confirmare/respingere, clientul primeste email.
- In mediu local, emailurile se afiseaza in terminal (console backend).

### 7) Testare
- Exista teste pentru serviciul de booking:
  - creare cerere cu succes;
  - blocare overlap;
  - confirmare cerere.

## Cum rulezi proiectul local

Ruleaza comenzile de mai jos din folderul `backend`:

```bash
cd "/mnt/c/Users/ana_c/Desktop/fac/anul3/sem2/ip/backend"
PYTHONPATH=python_packages python3 manage.py migrate
PYTHONPATH=python_packages python3 manage.py seed_demo
PYTHONPATH=python_packages python3 manage.py runserver
```

## URL-uri principale

- Login: `http://127.0.0.1:8000/login/`
- Register client: `http://127.0.0.1:8000/register/`
- Admin: `http://127.0.0.1:8000/admin/`

## Utilizatori si parole demo

Comanda `seed_demo` creeaza automat:

- `admin` / `admin1234`
- `client_demo` / `client1234`
- `employee_demo` / `employee1234`

## Comenzi utile

### Ruleaza testele

```bash
PYTHONPATH=python_packages python3 manage.py test core
```

