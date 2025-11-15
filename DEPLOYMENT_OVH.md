# Uruchomienie AgentKataster na OVH VPS - Instrukcja krok po kroku

## 🎯 Co będziemy robić?

Uruchomimy AgentKataster na serwerze VPS w OVH, który będzie zbierał dane o działkach z całej Polski 24/7 przez kilka dni.

**Koszt:** ~25-40 PLN/miesiąc (możesz usunąć po zebraniu danych i zapłacisz proporcjonalnie)

---

## Krok 1: Zaloguj się do OVH

1. Wejdź na: https://www.ovh.pl/
2. Kliknij **"Zaloguj się"** (prawy górny róg)
3. Zaloguj się swoim kontem OVH

Jesteś teraz w **Panelu klienta OVH**

---

## Krok 2: Zamówienie VPS

1. W menu po lewej stronie kliknij **"Zamów"** → **"VPS"**

   Lub wejdź bezpośrednio: https://www.ovhcloud.com/pl/vps/

2. **Wybierz model VPS:**

### Polecane opcje:

**OPCJA 1 - Starter (zalecane do testów):**
- **VPS Starter** - 25,00 PLN/miesiąc
- 2 vCore
- 2 GB RAM
- 40 GB SSD NVMe
- 250 Mbit/s

**OPCJA 2 - Comfort (zalecane do pełnego zbierania):**
- **VPS Comfort** - 40,00 PLN/miesiąc
- 2 vCore
- 4 GB RAM
- 80 GB SSD NVMe
- 500 Mbit/s

3. **Kliknij "Zamów"** przy wybranym modelu

---

## Krok 3: Konfiguracja VPS

### Krok 3.1: Wybór lokalizacji

- **Wybierz:** Polska (Warsaw) - najszybszy dostęp
- Lub: Niemcy (Frankfurt/Strasbourg) - też blisko

### Krok 3.2: Wybór systemu operacyjnego

- **System:** Ubuntu 22.04
- **Kliknij:** "Ubuntu 22.04"

### Krok 3.3: Okres fakturowania

- **Wybierz:** Miesięcznie (możesz anulować w każdej chwili)
- Lub: Roczny (oszczędzasz ~15%)

### Krok 3.4: Podsumowanie

1. Sprawdź podsumowanie zamówienia
2. Zaakceptuj regulamin
3. Kliknij **"Zapłać"**
4. Wybierz metodę płatności (karta/PayPal/przelew)
5. **Zapłać**

---

## Krok 4: Czekanie na aktywację VPS

**Czas oczekiwania:** 5-15 minut

1. **Sprawdzaj email** - otrzymasz:
   - Potwierdzenie zamówienia
   - **Email z dostępem do VPS** (login + hasło root)

2. **Lub sprawdź w panelu OVH:**
   - Menu → **"Bare Metal Cloud"** → **"VPS"**
   - Kliknij na swój VPS
   - Zobaczysz **adres IP** i status

**Zapisz:**
- ✅ Adres IP VPS (np. `51.83.123.45`)
- ✅ Hasło root (dostaniesz w emailu)

---

## Krok 5: Połączenie z VPS przez SSH

### Windows:

1. **Otwórz PowerShell** (Win+X → Windows PowerShell)

2. **Połącz się:**
```powershell
ssh root@TWOJ_ADRES_IP
# Przykład: ssh root@51.83.123.45
```

3. **Wpisz "yes"** gdy zapyta o fingerprint

4. **Wpisz hasło** które dostałeś w emailu
   - UWAGA: przy wpisywaniu hasła nic się nie pokazuje - to normalne!
   - Wklej hasło (prawy klik myszy) i naciśnij Enter

### Mac / Linux:

1. **Otwórz Terminal**

2. **Połącz się:**
```bash
ssh root@TWOJ_ADRES_IP
```

3. **Wpisz "yes"** i **hasło**

---

**✅ GRATULACJE! Jesteś teraz zalogowany na swoim VPS w OVH!**

Zobaczysz coś takiego:
```
root@vpsXXXXX:~#
```

---

## Krok 6: Zmiana hasła root (opcjonalnie, ale zalecane)

```bash
passwd

# Wpisz nowe hasło 2 razy
# Zapisz je w bezpiecznym miejscu!
```

---

## Krok 7: Aktualizacja systemu

```bash
# Skopiuj i wklej całą komendę (prawy klik myszy w PowerShell/Terminal)
apt update && apt upgrade -y
```

To potrwa 1-3 minuty. Poczekaj aż się zakończy.

---

## Krok 8: Instalacja Docker

```bash
# Instalacja Docker (skopiuj całość!)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalacja Docker Compose
apt install docker-compose -y

# Sprawdzenie czy działa
docker --version
docker-compose --version
```

Powinno pokazać:
```
Docker version 24.0.7, build...
docker-compose version 1.29.2, build...
```

✅ Docker zainstalowany!

---

## Krok 9: Pobranie AgentKataster

```bash
# Instalacja Git (jeśli nie ma)
apt install git -y

# Klonowanie repozytorium
git clone https://github.com/AdamJedrzejewski/agentkataster.git

# Wejście do folderu
cd agentkataster

# Sprawdzenie zawartości
ls -la
```

Zobaczysz pliki projektu.

---

## Krok 10: Konfiguracja

```bash
# Skopiowanie konfiguracji
cp .env.example .env

# (Opcjonalnie) Możesz zmienić hasła
nano .env

# Jeśli edytujesz, użyj strzałek do nawigacji
# Ctrl+X → Y → Enter - aby zapisać i wyjść
```

**Możesz zostawić domyślne ustawienia** - hasła są już tam.

---

## Krok 11: Uruchomienie AgentKataster! 🚀

```bash
# Uruchom wszystkie serwisy
docker-compose up -d

# Sprawdź czy wszystko działa
docker-compose ps
```

Powinno pokazać:
```
NAME                          STATUS
agentkataster_postgres_1      Up
agentkataster_redis_1         Up
agentkataster_worker_1        Up
agentkataster_scheduler_1     Up
```

✅ Wszystko działa!

---

## Krok 12: Inicjalizacja - pobierz listę gmin

```bash
# Poczekaj 10 sekund na uruchomienie bazy
sleep 10

# Zainicjalizuj bazę danych i pobierz gminy
docker-compose exec worker python -m src.main init
```

**To potrwa 2-5 minut.**

Zobaczysz logi:
```
Initializing database...
Database initialized successfully
Fetching municipalities from ULDK...
Found 2479 municipalities
Successfully initialized 2479 municipalities
✓ Initialization complete!
```

---

## Krok 13: Sprawdź status

```bash
docker-compose exec worker python -m src.main status
```

Zobaczysz ładną tabelkę:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Metric                     ┃ Value   ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━┫
┃ Total Municipalities       ┃ 2479    ┃
┃                            ┃         ┃
┃ Parcels Scraping           ┃         ┃
┃   Completed                ┃ 0 (0%)  ┃
┃   Pending                  ┃ 2479    ┃
┃   Failed                   ┃ 0       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━┛
```

---

## Krok 14: URUCHOM ZBIERANIE DANYCH! 🎯

### Opcja A: Wszystkie gminy (działki + plany) - PEŁNY ZBIÓR

```bash
docker-compose exec worker python -m src.main start
```

### Opcja B: Tylko działki (bez planów zagospodarowania) - SZYBCIEJ

```bash
docker-compose exec worker python -m src.main start --no-plans
```

### Opcja C: Test na jednej gminie (Warszawa)

```bash
# Najpierw przetestuj na 1 gminie
docker-compose exec worker python -m src.main scrape-municipality 146501

# Jeśli działa, uruchom dla wszystkich
docker-compose exec worker python -m src.main start
```

**URUCHOMIONE!** 🚀 Serwer będzie teraz zbierał dane 24/7.

---

## Krok 15: Monitorowanie postępu

### Sposób 1: Status (aktualizuj ręcznie)

```bash
docker-compose exec worker python -m src.main status
```

### Sposób 2: Logi na żywo

```bash
docker-compose logs -f worker

# Zobaczysz na żywo co się dzieje:
# "Fetching parcels for Warszawa (146501)"
# "Found 15234 parcels for Warszawa"
# "Successfully scraped 15234 parcels for Warszawa"

# Ctrl+C aby wyjść
```

### Sposób 3: Auto-refresh statusu co 5 minut

```bash
watch -n 300 'docker-compose exec worker python -m src.main status'

# Ctrl+C aby wyjść
```

### Sposób 4: Celery Flower - WEB INTERFACE 🌐

```bash
# Zainstaluj Flower
docker-compose exec worker pip install flower

# Uruchom Flower
docker-compose exec worker celery -A src.worker.celery_app flower --port=5555 --address=0.0.0.0 &
```

**Otwarcie w przeglądarce:**

1. W panelu OVH → Twój VPS → **Firewall**
2. Dodaj regułę:
   - Port: 5555
   - Protokół: TCP
   - Źródło: Anywhere
3. Otwórz w przeglądarce: `http://TWOJ_ADRES_IP:5555`

Zobaczysz piękny dashboard z:
- Aktywne zadania
- Postęp
- Statystyki
- Wykresy

---

## Krok 16: Odłączenie się (serwer będzie działał dalej!)

```bash
# Po prostu zamknij terminal
exit

# Lub Ctrl+D
```

**Serwer będzie dalej zbierał dane w tle!** Możesz wyłączyć komputer, pójść spać - VPS pracuje 24/7.

---

## Krok 17: Ponowne łączenie (sprawdzanie postępu)

**Możesz się połączyć w każdej chwili:**

```bash
# Z dowolnego komputera
ssh root@TWOJ_ADRES_IP

# Wejdź do folderu
cd agentkataster

# Sprawdź status
docker-compose exec worker python -m src.main status

# Zobacz ostatnie logi
docker-compose logs --tail 50 worker
```

---

## 📊 Ile to potrwa?

### Szacunki czasowe:

**VPS Starter (2GB RAM):**
- 1 gmina ≈ 15-30 sekund
- 100 gmin ≈ 30-60 minut
- **Cała Polska (2479 gmin) ≈ 3-5 dni**

**VPS Comfort (4GB RAM) - z 3 workerami:**
- **Cała Polska ≈ 1-2 dni**

### Przyspieszenie - uruchom więcej worker-ów:

```bash
# Edytuj docker-compose.yml
nano docker-compose.yml

# Znajdź sekcję worker i dodaj scale
# LUB po prostu uruchom:
docker-compose up -d --scale worker=3

# Teraz 3 worker-y przetwarzają równolegle!
```

---

## 💾 Rozmiar danych

**Dla całej Polski:**
- Metadane gmin: ~1 MB
- Działki (geometrie): ~50-80 GB
- Plany zagospodarowania: ~10-20 GB
- **Razem: ~60-100 GB**

**VPS Starter (40GB):** Za mało dla całej Polski z planami
→ **Rozwiązanie:** Zbieraj tylko działki (`--no-plans`) lub wybierz VPS Comfort (80GB)

**VPS Comfort (80GB):** ✅ Wystarczy na wszystko

---

## 💰 Koszty

### VPS Starter (25 PLN/mc):
- **5 dni:** ~4 PLN (płatność proporcjonalna)
- **Miesiąc:** 25 PLN
- **Transfer:** bez limitu (w cenę wliczone)

### VPS Comfort (40 PLN/mc):
- **5 dni:** ~7 PLN
- **Miesiąc:** 40 PLN

**RAZEM na zbieranie danych:** ~4-7 PLN (jeśli usuniesz VPS po 5 dniach)

---

## 🔍 Dostęp do bazy danych

### Z poziomu VPS:

```bash
docker-compose exec postgres psql -U postgres -d agentkataster
```

```sql
-- Ile gmin przetworzyliśmy?
SELECT
    parcels_status,
    COUNT(*)
FROM municipalities
GROUP BY parcels_status;

-- Ile działek mamy?
SELECT COUNT(*) FROM parcels;

-- Top 10 gmin z największą liczbą działek
SELECT name, total_parcels
FROM municipalities
WHERE total_parcels > 0
ORDER BY total_parcels DESC
LIMIT 10;

-- Wyjście
\q
```

### Zdalny dostęp (z komputera):

**Krok 1: Otwórz port w firewall OVH**

1. Panel OVH → Twój VPS → **Network** → **Firewall**
2. **Dodaj regułę:**
   - Nazwa: PostgreSQL
   - Port: 5432
   - Protokół: TCP
   - Źródło: Twoje IP (lub Anywhere - mniej bezpieczne)
3. Zapisz

**Krok 2: Edytuj docker-compose.yml**

```bash
nano docker-compose.yml

# Znajdź sekcję postgres, odkomentuj ports:
  postgres:
    ports:
      - "5432:5432"  # <-- usuń # przed tą linią

# Ctrl+X → Y → Enter

# Restart
docker-compose down
docker-compose up -d
```

**Krok 3: Połącz się z QGIS/DBeaver/pgAdmin:**

- Host: `TWOJ_ADRES_IP_VPS`
- Port: `5432`
- Database: `agentkataster`
- User: `postgres`
- Password: `postgres` (lub co ustawiłeś w .env)

Teraz możesz przeglądać dane, eksportować mapy, robić analizy!

---

## 📤 Eksport danych

### Export do GeoJSON:

```bash
# Export wszystkich działek
docker-compose exec worker python scripts/export_data.py --type parcels

# Export planów
docker-compose exec worker python scripts/export_data.py --type plans

# Export dla konkretnej gminy
docker-compose exec worker python scripts/export_data.py --municipality 146501
```

Pliki będą w `exports/`

### Pobranie plików z VPS na komputer:

```bash
# Z TWOJEGO komputera (nie z VPS!)
scp root@TWOJ_ADRES_IP:/root/agentkataster/exports/* ./

# Lub użyj WinSCP (Windows): https://winscp.net/
```

---

## 🛑 Zarządzanie VPS

### Zatrzymanie zbierania danych:

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

### Restart VPS (w panelu OVH):

1. Panel OVH → VPS → Twój VPS
2. Kliknij **"Restart"**
3. Po restarcie połącz się i uruchom:
```bash
cd agentkataster
docker-compose up -d
```

### Usunięcie VPS (po zebraniu danych):

1. Panel OVH → VPS → Twój VPS
2. **Najpierw pobierz dane!** (eksport + scp)
3. Kliknij **"Usuń"**
4. Potwierdź usunięcie
5. Dostaniesz zwrot środków proporcjonalnie

---

## 📋 Checklist - Co zrobiłeś?

- [ ] Zalogowałeś się do OVH
- [ ] Zamówiłeś VPS (Starter/Comfort)
- [ ] Dostałeś email z IP i hasłem root
- [ ] Połączyłeś się przez SSH
- [ ] Zmieniłeś hasło root (opcjonalnie)
- [ ] Zaktualizowałeś system (`apt update && apt upgrade`)
- [ ] Zainstalowałeś Docker i Docker Compose
- [ ] Sklonowałeś repozytorium
- [ ] Skopiowałeś `.env.example` → `.env`
- [ ] Uruchomiłeś `docker-compose up -d`
- [ ] Zainicjalizowałeś bazę (`init`)
- [ ] Uruchomiłeś zbieranie (`start`)
- [ ] Sprawdzasz postęp (`status` lub Flower)

---

## 🆘 Rozwiązywanie problemów

### Problem: "Permission denied" przy SSH

```bash
# Sprawdź czy używasz dobrego IP
# Sprawdź czy VPS jest aktywny w panelu OVH
# Spróbuj zresetować hasło w panelu OVH
```

### Problem: Docker nie działa

```bash
# Sprawdź status
systemctl status docker

# Uruchom jeśli zatrzymany
systemctl start docker
```

### Problem: Brak miejsca na dysku

```bash
# Sprawdź miejsce
df -h

# Jeśli mało:
docker system prune -a  # Usuń nieużywane obrazy
# LUB wybierz tylko działki: --no-plans
```

### Problem: Worker nie przetwarza zadań

```bash
# Zobacz logi
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Sprawdź czy Redis działa
docker-compose ps redis
```

### Problem: Brak połączenia z ULDK

```bash
# Czasem ULDK jest przeciążony
# Poczekaj 30 minut i spróbuj ponownie

# Sprawdź czy masz internet na VPS
ping google.com
```

---

## 🎓 Co dalej po zebraniu danych?

1. **Eksportuj dane** - GeoJSON/Shapefile
2. **Pobierz na komputer** - `scp` lub WinSCP
3. **Usuń VPS** - zwrot pieniędzy za niewykorzystany okres
4. **Zaimportuj do PostgreSQL lokalnie** lub zostaw na VPS
5. **Zbuduj API** - FastAPI endpoint do wyszukiwania
6. **Frontend** - mapa interaktywna z działkami
7. **Filtry inwestycyjne** - powierzchnia, przeznaczenie, lokalizacja

---

## 💡 Protip: Screen session (zaawansowane)

Jeśli chcesz zobaczyć logi na żywo, ale móc się odłączyć:

```bash
# Zainstaluj screen
apt install screen -y

# Uruchom screen
screen -S agentkataster

# Uruchom logi
docker-compose logs -f worker

# Odłącz się: Ctrl+A, potem D
# Połącz ponownie: screen -r agentkataster
```

---

**Gotowe! Uruchamiaj i zbieraj dane! 🚀🗺️**

W razie pytań - napisz issue na GitHubie lub sprawdź README.md

---

**Autor:** AgentKataster
**Data:** 2024
**Platforma:** OVH Cloud VPS
