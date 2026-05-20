# Sportal MVP (Django + JavaScript)

## Run locally

```bash
cd "/mnt/c/Users/ana_c/Desktop/fac/anul3/sem2/ip/backend"
PYTHONPATH=python_packages python3 manage.py migrate
PYTHONPATH=python_packages python3 manage.py seed_demo
PYTHONPATH=python_packages python3 manage.py runserver

kill port: fuser -k 8000/tcp
```

## Demo users

- `admin` / `admin1234`
- `client_demo` / `client1234`
- `employee_demo` / `employee1234`
- `anaciurea644@gmail.com` / `ana1234` (can log in with email)

## Real email delivery (Gmail SMTP)

By default, emails are printed in terminal (console backend). To send real emails:

```bash
cp .env.example .env
# edit .env and put your real Gmail App Password in EMAIL_HOST_PASSWORD
PYTHONPATH=python_packages python3 manage.py runserver
```

For Gmail, use an App Password (16 chars), not your normal account password.

## Main URLs

- Login: `http://127.0.0.1:8000/login/`
- Register client: `http://127.0.0.1:8000/register/`
- Admin: `http://127.0.0.1:8000/admin/`

## Email confirmations/rejections

- On employee confirm/reject, the client receives an email notification.
- In local development, emails are printed in the terminal running `runserver` (console backend).
- For real email delivery, configure SMTP in `sportal/settings.py`.

## Test suite

```bash
PYTHONPATH=python_packages python3 manage.py test core
```
