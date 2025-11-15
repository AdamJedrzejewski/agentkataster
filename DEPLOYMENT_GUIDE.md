# Przewodnik wdrożenia AgentKataster na VPS

## 🎯 Co będziemy robić?

Uruchomimy AgentKataster na serwerze VPS (Virtual Private Server), który będzie zbierał dane 24/7 przez kilka dni/tygodni, aż zbierze wszystkie działki z Polski.

---

## Krok 1: Założenie konta na Hetzner Cloud

1. Wejdź na https://www.hetzner.com/cloud
2. Kliknij **"Sign Up"** (Zarejestruj się)
3. Wypełnij formularz (email, hasło)
4. Potwierdź email
5. Dodaj metodę płatności (karta/PayPal)

---

## Krok 2: Utworzenie serwera (Cloud Server)

1. **Zaloguj się** do Hetzner Cloud Console: https://console.hetzner.cloud/
2. Kliknij **"New Project"** → Nazwij "AgentKataster"
3. Kliknij **"Add Server"**

### Konfiguracja serwera:

**Location (Lokalizacja):**
- Wybierz: **Falkenstein** lub **Helsinki** (najbliższe Polsce)

**Image (System operacyjny):**
- Wybierz: **Ubuntu 22.04**

**Type (Typ):**
- Wybierz: **CX21** (2 vCPU, 4 GB RAM) - 4.51 EUR/miesiąc
- Lub **CPX11** (2 vCPU, 2 GB RAM) - 4.15 EUR/miesiąc (dla oszczędności)

**SSH Key:**
- Kliknij **"Add SSH Key"**
- Na Windows: Otwórz PowerShell i wpisz:
  ```powershell
  ssh-keygen -t rsa -b 4096
  # Naciśnij Enter 3 razy (domyślne ustawienia)
  cat ~/.ssh/id_rsa.pub
  # Skopiuj cały output i wklej do Hetzner
  ```

**Volume, Network, Firewalls:**
- Zostaw puste (domyślne)

**Name:**
- Wpisz: `agentkataster-vps`

4. Kliknij **"Create & Buy now"**
5. Poczekaj ~30 sekund aż serwer się utworzy
6. **ZAPISZ ADRES IP** serwera (np. `95.217.123.456`)

---

## Krok 3: Połączenie z serwerem przez SSH

### Na Windows:

Otwórz **PowerShell** i wpisz:

```powershell
ssh root@TWOJ_ADRES_IP
# Przykład: ssh root@95.217.123.456

# Przy pierwszym połączeniu wpisz: yes
```

### Na Mac/Linux:

Otwórz **Terminal** i wpisz:

```bash
ssh root@TWOJ_ADRES_IP
```

**✅ Jesteś teraz zalogowany na swoim serwerze!**

---

## Krok 4: Instalacja Docker na serwerze

Skopiuj i wklej **po kolei** te komendy do terminala SSH:

```bash
# 1. Aktualizacja systemu
apt update && apt upgrade -y

# 2. Instalacja Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Instalacja Docker Compose
apt install docker-compose -y

# 4. Sprawdzenie czy działa
docker --version
docker-compose --version

# Powinno pokazać wersje (np. Docker version 24.0.7)
```

---

## Krok 5: Pobranie i konfiguracja AgentKataster

```bash
# 1. Klonowanie repozytorium
git clone https://github.com/AdamJedrzejewski/agentkataster.git
cd agentkataster

# 2. Skopiowanie konfiguracji
cp .env.example .env

# 3. (Opcjonalnie) Edycja konfiguracji
nano .env
# Możesz zmienić hasła do bazy danych
# Naciśnij Ctrl+X, potem Y, potem Enter aby zapisać
```

---

## Krok 6: Uruchomienie AgentKataster

```bash
# 1. Uruchom wszystkie serwisy (PostgreSQL, Redis, Worker)
docker-compose up -d

# 2. Sprawdź czy wszystko działa
docker-compose ps
# Powinno pokazać 4 serwisy: postgres, redis, worker, scheduler

# 3. Zobacz logi (czy nie ma błędów)
docker-compose logs

# 4. Poczekaj 10 sekund na uruchomienie bazy danych
sleep 10
```

---

## Krok 7: Inicjalizacja bazy danych

```bash
# To pobierze listę wszystkich ~2500 gmin w Polsce
docker-compose exec worker python -m src.main init

# Poczekaj 2-5 minut
# Zobaczysz logi typu:
# "Fetching municipalities from ULDK..."
# "Found 2479 municipalities"
# "Successfully initialized 2479 municipalities"
```

---

## Krok 8: Sprawdzenie statusu

```bash
docker-compose exec worker python -m src.main status
```

Zobaczysz tabelę z:
- Total Municipalities: 2479
- Parcels Scraping - Pending: 2479
- Plans Scraping - Pending: 2479

---

## Krok 9: Uruchomienie zbierania danych! 🚀

### Opcja A: Zbieranie wszystkiego (działki + plany)

```bash
docker-compose exec worker python -m src.main start
```

### Opcja B: Tylko działki (szybciej, mniej danych)

```bash
docker-compose exec worker python -m src.main start --no-plans
```

### Opcja C: Test na jednej gminie (Warszawa)

```bash
docker-compose exec worker python -m src.main scrape-municipality 146501
```

---

## Krok 10: Monitorowanie postępu

### Sposób 1: Status co 5 minut

```bash
watch -n 300 'docker-compose exec worker python -m src.main status'
# Naciśnij Ctrl+C aby wyjść
```

### Sposób 2: Logi na żywo

```bash
docker-compose logs -f worker
# Naciśnij Ctrl+C aby wyjść
```

### Sposób 3: Celery Flower (web interface)

```bash
# Uruchom Flower
docker-compose exec -d worker celery -A src.worker.celery_app flower --port=5555 --address=0.0.0.0

# Potem otwórz w przeglądarce:
# http://TWOJ_ADRES_IP:5555
```

**UWAGA:** Musisz otworzyć port 5555 w firewall Hetzner (Cloud Console → Firewalls)

---

## Krok 11: Odłączenie się (serwer będzie działał dalej)

```bash
# Po prostu zamknij terminal SSH
exit

# Serwer będzie dalej zbierał dane w tle 24/7!
```

---

## Krok 12: Sprawdzanie postępu zdalnie

Możesz się połączyć w dowolnym momencie:

```bash
ssh root@TWOJ_ADRES_IP
cd agentkataster
docker-compose exec worker python -m src.main status
```

---

## 📊 Ile to potrwa?

**Szacunki czasowe:**

- **1 gmina** ≈ 10-30 sekund (zależy od liczby działek)
- **100 gmin** ≈ 30 minut - 1 godzina
- **2500 gmin (cała Polska)** ≈ **2-5 dni** (przy 1 worker)

**Możesz przyspieszyć** uruchamiając więcej worker-ów:

```bash
# Edytuj docker-compose.yml
nano docker-compose.yml

# Dodaj więcej worker-ów (zmień scale)
docker-compose up -d --scale worker=3

# Teraz 3 worker-y będą przetwarzać równolegle!
```

---

## 💾 Rozmiar danych

**Szacunki:**

- **Metadane gmin:** ~1 MB
- **Działki (geometrie):** ~50-100 GB (dla całej Polski)
- **Plany zagospodarowania:** ~10-20 GB

**Razem: ~60-120 GB** (dlatego zamówiliśmy serwer z min. 40GB)

---

## 🔍 Dostęp do bazy danych

### Z poziomu serwera:

```bash
docker-compose exec postgres psql -U postgres -d agentkataster

# Przykładowe zapytania:
\dt                    # Lista tabel
SELECT COUNT(*) FROM municipalities;
SELECT COUNT(*) FROM parcels;

\q                     # Wyjście
```

### Zdalne połączenie (np. z QGIS, DBeaver):

1. **Edytuj docker-compose.yml** - dodaj mapowanie portu:
```yaml
postgres:
  ports:
    - "5432:5432"  # <-- odkryj tę linię
```

2. **Restart:**
```bash
docker-compose down
docker-compose up -d
```

3. **Połącz się z:**
- Host: `TWOJ_ADRES_IP`
- Port: `5432`
- Database: `agentkataster`
- User: `postgres`
- Password: `postgres` (lub co ustawiłeś w .env)

---

## 🛑 Zatrzymanie i wznawianie

### Zatrzymanie:
```bash
docker-compose down
```

### Wznowienie:
```bash
docker-compose up -d
```

### Sprawdzenie co działa:
```bash
docker-compose ps
```

---

## 💰 Koszty

**Hetzner CX21:**
- **4.51 EUR/miesiąc** (≈20 PLN)
- Można usunąć serwer po zebraniu danych i zapłacić tylko proporcjonalnie (np. 5 dni = ~3 PLN)

**Transfer danych:**
- Hetzner daje 20 TB transfer/miesiąc za darmo
- AgentKataster użyje ~10-50 GB (spokojnie w limicie)

**RAZEM na 5 dni:** ~3-4 PLN

---

## 📤 Eksport zebranych danych

Po zebraniu danych możesz je wyeksportować:

```bash
# Export do GeoJSON
docker-compose exec worker python scripts/export_data.py --type parcels

# Export plików z serwera do komputera
scp root@TWOJ_ADRES_IP:/home/user/agentkataster/exports/* ./
```

Albo podłącz się do bazy przez QGIS/DBeaver i eksportuj co chcesz.

---

## 🆘 Rozwiązywanie problemów

### Problem: Worker nie działa

```bash
docker-compose logs worker
docker-compose restart worker
```

### Problem: Brak miejsca na dysku

```bash
df -h                  # Sprawdź miejsce
docker system prune    # Wyczyść nieużywane obrazy
```

### Problem: Błędy połączenia z ULDK

```bash
# Sprawdź logi
docker-compose logs worker | grep ERROR

# Czasem ULDK jest przeciążony, poczekaj i spróbuj ponownie
```

---

## ✅ Checklist - Co zrobiłeś?

- [ ] Założyłeś konto na Hetzner Cloud
- [ ] Utworzyłeś serwer VPS (CX21, Ubuntu 22.04)
- [ ] Połączyłeś się przez SSH
- [ ] Zainstalowałeś Docker i Docker Compose
- [ ] Sklonowałeś repozytorium AgentKataster
- [ ] Uruchomiłeś `docker-compose up -d`
- [ ] Zainicjalizowałeś bazę (`init`)
- [ ] Uruchomiłeś zbieranie (`start`)
- [ ] Sprawdzasz postęp (`status`)

---

## 🎓 Następne kroki po zebraniu danych

1. **Zbuduj API** - endpoint do wyszukiwania działek
2. **Dodaj frontend** - mapa interaktywna (Leaflet/Mapbox)
3. **Filtry dla inwestorów:**
   - Min/max powierzchnia
   - Przeznaczenie (mieszkaniowe, usługowe, przemysłowe)
   - Odległość od miasta
4. **Dodaj analizy:**
   - Ceny m² w okolicy (integracja z ofertami)
   - Dostępność mediów
   - Najbliższa infrastruktura

---

**Powodzenia! 🚀**

W razie pytań - sprawdź główny README.md lub otwórz issue na GitHubie.
