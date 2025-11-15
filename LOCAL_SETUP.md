# Uruchomienie AgentKataster na swoim komputerze

## 🖥️ Dla kogo ten przewodnik?

Chcesz przetestować AgentKataster na swoim komputerze (Windows, Mac lub Linux) bez używania serwera.

**UWAGA:** To rozwiązanie jest dobre do:
- ✅ Testowania narzędzia
- ✅ Zbierania danych dla kilku/kilkunastu gmin
- ❌ **NIE** do zbierania danych dla całej Polski (zajmie to dni i komputer musi być włączony)

Jeśli chcesz zbierać dane dla całej Polski → zobacz **DEPLOYMENT_GUIDE.md** (VPS)

---

## Wymagania

- **System:** Windows 10/11, macOS 10.14+, lub Linux
- **RAM:** Minimum 8 GB (zalecane 16 GB)
- **Dysk:** 20 GB wolnego miejsca
- **Internet:** Stałe połączenie

---

## Krok 1: Instalacja Docker Desktop

### Windows / Mac:

1. **Pobierz Docker Desktop:**
   - Windows: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
   - Mac (Intel): https://desktop.docker.com/mac/main/amd64/Docker.dmg
   - Mac (Apple Silicon): https://desktop.docker.com/mac/main/arm64/Docker.dmg

2. **Zainstaluj:**
   - Uruchom instalator
   - Zaakceptuj wszystkie domyślne ustawienia
   - Po instalacji uruchom **Docker Desktop**

3. **Sprawdź czy działa:**
   - Otwórz **PowerShell** (Windows) lub **Terminal** (Mac)
   - Wpisz:
   ```bash
   docker --version
   ```
   - Powinno pokazać: `Docker version 24.x.x` (lub podobne)

### Linux (Ubuntu/Debian):

```bash
# Instalacja Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalacja Docker Compose
sudo apt install docker-compose -y

# Dodaj swojego użytkownika do grupy docker
sudo usermod -aG docker $USER

# Wyloguj się i zaloguj ponownie
```

---

## Krok 2: Instalacja Git (jeśli nie masz)

### Windows:

1. Pobierz: https://git-scm.com/download/win
2. Zainstaluj z domyślnymi ustawieniami

### Mac:

```bash
# Git jest zazwyczaj już zainstalowany
git --version

# Jeśli nie ma, zainstaluj Homebrew i Git:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git
```

### Linux:

```bash
sudo apt install git -y
```

---

## Krok 3: Pobranie AgentKataster

Otwórz **Terminal** (Mac/Linux) lub **PowerShell** (Windows):

```bash
# Przejdź do folderu gdzie chcesz mieć projekt (np. Dokumenty)
cd ~/Documents  # Mac/Linux
# lub
cd ~\Documents  # Windows PowerShell

# Sklonuj repozytorium
git clone https://github.com/AdamJedrzejewski/agentkataster.git

# Wejdź do folderu
cd agentkataster

# Sprawdź zawartość
ls  # Mac/Linux
dir # Windows
```

---

## Krok 4: Konfiguracja

```bash
# Skopiuj przykładową konfigurację
cp .env.example .env    # Mac/Linux
copy .env.example .env  # Windows

# (Opcjonalnie) Możesz edytować .env
# Windows: notepad .env
# Mac: open -e .env
# Linux: nano .env
```

**Możesz zostawić domyślne ustawienia** - hasła są już tam wpisane.

---

## Krok 5: Uruchomienie Docker

**WAŻNE:** Upewnij się, że **Docker Desktop jest uruchomiony**!

```bash
# Uruchom wszystkie serwisy
docker-compose up -d

# Sprawdź czy wszystko działa
docker-compose ps
```

Powinno pokazać 4 serwisy:
- ✅ agentkataster_postgres
- ✅ agentkataster_redis
- ✅ agentkataster_worker
- ✅ agentkataster_scheduler

---

## Krok 6: Inicjalizacja bazy danych

```bash
# Poczekaj 10 sekund na uruchomienie PostgreSQL
# Windows PowerShell:
Start-Sleep -Seconds 10

# Mac/Linux:
sleep 10

# Zainicjalizuj bazę i pobierz listę gmin
docker-compose exec worker python -m src.main init
```

**To potrwa 2-5 minut.** Zobaczysz:
```
Initializing database...
Database initialized successfully
Fetching municipalities from ULDK...
Found 2479 municipalities
Successfully initialized 2479 municipalities
```

---

## Krok 7: Sprawdzenie statusu

```bash
docker-compose exec worker python -m src.main status
```

Zobaczysz tabelkę z statystykami:

```
┏━━━━━━━━━━━━━━━━━━━━━━━┓
┃ AgentKataster Status  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Total Municipalities  ┃ 2479 ┃
┃ Parcels - Completed   ┃ 0    ┃
┃ Parcels - Pending     ┃ 2479 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Krok 8: Testowanie na jednej gminie

**Zamiast uruchamiać dla całej Polski, przetestuj na 1 gminie:**

```bash
# Przykład: Warszawa (kod TERYT: 146501)
docker-compose exec worker python -m src.main scrape-municipality 146501

# Inne przykłady:
# Kraków: 126301
# Wrocław: 026301
# Poznań: 306301
# Gdańsk: 226101
```

---

## Krok 9: Monitorowanie (dla jednej gminy)

```bash
# Zobacz logi na żywo
docker-compose logs -f worker

# Zobaczysz:
# "Fetching parcels for Warszawa (146501)"
# "Found 15234 parcels for Warszawa"
# "Successfully scraped 15234 parcels for Warszawa"
```

Naciśnij **Ctrl+C** aby wyjść z logów.

---

## Krok 10: Sprawdzenie wyników

```bash
# Status
docker-compose exec worker python -m src.main status

# Połącz się z bazą danych
docker-compose exec postgres psql -U postgres -d agentkataster

# W psql:
SELECT COUNT(*) FROM municipalities;
SELECT COUNT(*) FROM parcels;

# Wyjście z psql:
\q
```

---

## 🎯 Jeśli chcesz zbierać dla wielu gmin

### Wariant A: Lista konkretnych gmin

Stwórz plik `municipalities.txt` z kodami TERYT:

```
146501
126301
026301
```

Potem w pętli:

```bash
# Mac/Linux:
while read teryt; do
  docker-compose exec worker python -m src.main scrape-municipality "$teryt"
done < municipalities.txt

# Windows PowerShell:
Get-Content municipalities.txt | ForEach-Object {
  docker-compose exec worker python -m src.main scrape-municipality $_
}
```

### Wariant B: Wszystkie gminy (NIE ZALECANE lokalnie!)

```bash
docker-compose exec worker python -m src.main start

# To zajmie DNI i komputer musi być włączony!
# Lepiej użyj VPS (patrz DEPLOYMENT_GUIDE.md)
```

---

## 📊 Dostęp do danych

### Przez SQL:

```bash
docker-compose exec postgres psql -U postgres -d agentkataster
```

```sql
-- Przykładowe zapytania

-- Działki w Warszawie
SELECT parcel_id, area_ha, land_use_code
FROM parcels p
JOIN municipalities m ON p.municipality_id = m.id
WHERE m.code = '146501'
LIMIT 10;

-- Największe działki
SELECT m.name, p.parcel_id, p.area_ha
FROM parcels p
JOIN municipalities m ON p.municipality_id = m.id
ORDER BY p.area_ha DESC
LIMIT 10;
```

### Przez QGIS (wizualizacja na mapie):

1. **Pobierz QGIS:** https://qgis.org/
2. **Połącz się z bazą:**
   - Layer → Add Layer → Add PostGIS Layers
   - Host: `localhost`
   - Port: `5432`
   - Database: `agentkataster`
   - User: `postgres`
   - Password: `postgres`
3. **Dodaj warstwę `parcels`** i zobacz działki na mapie!

### Export do GeoJSON:

```bash
docker-compose exec worker python scripts/export_data.py --type parcels --municipality 146501
```

Plik będzie w `exports/parcels.geojson`

---

## 🛑 Zatrzymywanie i wznawianie

### Zatrzymanie:

```bash
docker-compose down
```

### Wznowienie:

```bash
docker-compose up -d
```

### Całkowite wyczyszczenie (USUWA DANE!):

```bash
docker-compose down -v
# To usunie wszystko włącznie z bazą danych!
```

---

## 💻 Ile zasobów to zajmuje?

**Podczas działania:**
- RAM: ~2-4 GB
- CPU: 20-50% (1-2 rdzenie)
- Dysk: +100 MB/gminę (dla działek)

**Dla 10 gmin:** ~1 GB
**Dla 100 gmin:** ~10 GB
**Dla całej Polski:** ~60-120 GB

---

## 🆘 Problemy?

### Docker nie uruchamia się

- **Windows:** Sprawdź czy Hyper-V jest włączony
- **Mac:** Sprawdź czy Docker Desktop jest uruchomiony
- **Linux:** `sudo systemctl start docker`

### "Cannot connect to Docker daemon"

```bash
# Upewnij się że Docker Desktop jest uruchomiony
# Windows/Mac: Otwórz aplikację Docker Desktop
```

### Port 5432 zajęty

Jeśli masz lokalnie zainstalowany PostgreSQL:

```bash
# Edytuj docker-compose.yml
# Zmień port:
#   - "5433:5432"  # zamiast 5432:5432
```

### Wolne działanie

```bash
# Zmniejsz concurrent requests w .env
CONCURRENT_REQUESTS=2  # zamiast 5
REQUEST_DELAY=2.0      # zamiast 1.0
```

---

## 🎓 Co dalej?

Po zebraniu danych dla kilku gmin możesz:

1. **Zwizualizować w QGIS** - zobacz działki na mapie
2. **Eksportować do GeoJSON** - użyj w webowej mapie
3. **Zbudować API** - endpoint do wyszukiwania
4. **Dodać frontend** - Leaflet/Mapbox + React/Vue

Jeśli chcesz zbierać dla całej Polski → **użyj VPS** (patrz DEPLOYMENT_GUIDE.md)

---

## ✅ Checklist

- [ ] Zainstalowałeś Docker Desktop
- [ ] Zainstalowałeś Git
- [ ] Sklonowałeś repozytorium
- [ ] Skopiowałeś .env.example → .env
- [ ] Uruchomiłeś `docker-compose up -d`
- [ ] Zainicjalizowałeś bazę (`init`)
- [ ] Przetestowałeś na 1 gminie
- [ ] Sprawdziłeś wyniki w bazie

---

**Powodzenia! 🚀**

W razie pytań → otwórz issue na GitHubie lub sprawdź README.md
