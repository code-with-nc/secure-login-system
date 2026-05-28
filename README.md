# Secure University Login & Session Monitoring System

A Python Flask-based secure login simulator for a university student portal.

## Features

- Username format validation
- Password complexity validation
- Password hashing using SHA-256
- Failed login attempt tracking
- Account blocking after 3 failures
- Login activity logging
- Session timeout simulation
- User records using dictionaries
- External log file storage
- Suspicious activity report
- Visualization using Matplotlib
- Docker and Docker Compose support

## Run on Kali Linux

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

git clone https://github.com/YOUR_USERNAME/secure-login-system.git
cd secure-login-system

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python app.py
