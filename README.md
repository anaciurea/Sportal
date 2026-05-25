# Sportal MVP

Sistem de rezervari de resurse sportive construit cu Django (backend + templates) si JavaScript nativ pe frontend.

## Rulare locala

```bash
cd backend
PYTHONPATH=python_packages python3 manage.py migrate
PYTHONPATH=python_packages python3 manage.py seed_demo
PYTHONPATH=python_packages python3 manage.py runserver
```

Pentru a opri portul: `fuser -k 8000/tcp`

## URL-uri principale

| URL | Descriere |
|-----|-----------|
| `http://127.0.0.1:8000/` | Dashboard (client sau angajat) |
| `http://127.0.0.1:8000/login/` | Autentificare |
| `http://127.0.0.1:8000/register/` | Inregistrare cont client |
| `http://127.0.0.1:8000/stats/` | Statistici (doar angajat) |
| `http://127.0.0.1:8000/admin/` | Panou admin Django |

## Utilizatori demo

| Username | Parola | Rol |
|----------|--------|-----|
| `admin` | `admin1234` | Superuser |
| `employee_demo` | `employee1234` | Angajat |
| `client_demo` | `client1234` | Client |
| `anaciurea644@gmail.com` | `ana1234` | Client (login cu email) |

## Teste automate

```bash
PYTHONPATH=python_packages python3 manage.py test core
```

## Arhitectura

**Stack:** Python 3 + Django 5, Django Templates, JavaScript nativ, SQLite (ORM Django)

**Modele principale:**
- `Company` / `Location` — structura organizationala
- `SportResource` — teren (tip sport + pret/ora)
- `EmployeeProfile` — leaga un user de o locatie ca angajat
- `BookingRequest` — cerere de rezervare cu statusuri: `pending`, `confirmed`, `rejected`, `cancelled`
- `Review` — recenzie post-rezervare (1–5 stele)

**Siguranta concurenta:** `transaction.atomic` + `select_for_update` in `core/services/booking_service.py`

## Notificari email

Implicit, emailurile se afiseaza in terminal (console backend). Pentru trimitere reala prin Gmail:

```bash
cp .env.example .env
# Editeaza .env si completeaza EMAIL_HOST_PASSWORD cu un App Password Gmail (16 caractere)
PYTHONPATH=python_packages python3 manage.py runserver
```
