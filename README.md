# AgentKataster 🗺️

Polish Land Registry Data Scraper - Automated tool for collecting land parcel data and spatial development plans from Polish Geoportal.

## Opis / Description

AgentKataster to zaawansowane narzędzie do automatycznego zbierania danych o działkach gruntu oraz planach zagospodarowania przestrzennego z polskiego Geoportalu. Narzędzie działa w tle, przetwarzając gminy jedna po drugiej i zapisując dane do bazy PostgreSQL z rozszerzeniem PostGIS.

AgentKataster is an advanced tool for automatically collecting land parcel data and spatial development plans from the Polish Geoportal. The tool works in the background, processing municipalities one by one and saving data to a PostgreSQL database with PostGIS extension.

## Funkcjonalności / Features

- ✅ **Automatyczne zbieranie danych o działkach** z usługi ULDK (Usługi Lokalizacji Działek Katastralnych)
- ✅ **Pobieranie planów zagospodarowania przestrzennego** (MPZP i SUiKZP)
- ✅ **Przetwarzanie w tle** - asynchroniczne zbieranie danych gmina po gminie
- ✅ **Baza danych przestrzennych** - PostgreSQL + PostGIS do przechowywania geometrii
- ✅ **System kolejkowania zadań** - Celery + Redis dla wydajnego przetwarzania
- ✅ **CLI** - wygodny interfejs linii komend do zarządzania
- ✅ **Logowanie i monitoring** - śledzenie postępu i błędów

## Architektura / Architecture

```
agentkataster/
├── src/
│   ├── models.py              # Database models (SQLAlchemy + GeoAlchemy2)
│   ├── database.py            # Database connection and session management
│   ├── config.py              # Configuration management
│   ├── worker.py              # Celery background worker
│   ├── main.py                # CLI application
│   └── scrapers/
│       ├── base_scraper.py    # Base scraper class
│       ├── uldk_scraper.py    # ULDK cadastral data scraper
│       └── spatial_plans_scraper.py  # Spatial plans scraper
├── docker-compose.yml         # Docker services (PostgreSQL, Redis)
├── Dockerfile                 # Application container
└── requirements.txt           # Python dependencies
```

## Instalacja / Installation

### Wymagania / Requirements

- Python 3.9+
- Docker & Docker Compose (recommended)
- PostgreSQL 15+ with PostGIS extension
- Redis

### Quick Start z Docker

1. **Sklonuj repozytorium / Clone repository:**
```bash
git clone https://github.com/yourusername/agentkataster.git
cd agentkataster
```

2. **Skonfiguruj zmienne środowiskowe / Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Uruchom usługi / Start services:**
```bash
docker-compose up -d
```

4. **Zainicjalizuj bazę danych / Initialize database:**
```bash
docker-compose exec worker python -m src.main init
```

### Instalacja lokalna / Local Installation

1. **Utwórz środowisko wirtualne / Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. **Zainstaluj zależności / Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Skonfiguruj PostgreSQL z PostGIS:**
```sql
CREATE DATABASE agentkataster;
\c agentkataster
CREATE EXTENSION postgis;
```

4. **Skonfiguruj zmienne środowiskowe:**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Zainicjalizuj bazę / Initialize database:**
```bash
python -m src.main init
```

## Użycie / Usage

### CLI Commands

#### 1. Inicjalizacja systemu
```bash
# Initialize database and fetch all municipalities
python -m src.main init
```

#### 2. Sprawdzenie statusu
```bash
# Show scraping status and statistics
python -m src.main status
```

#### 3. Uruchomienie scrapowania
```bash
# Start scraping all municipalities (background)
python -m src.main start

# Scrape only parcels
python -m src.main start --no-plans

# Scrape only spatial plans
python -m src.main start --no-parcels
```

#### 4. Scrapowanie konkretnej gminy
```bash
# Scrape specific municipality by TERYT code
python -m src.main scrape-municipality 146301

# Scrape only parcels for municipality
python -m src.main scrape-municipality 146301 --no-plans
```

#### 5. Lista gmin
```bash
# List municipalities
python -m src.main list-municipalities

# Show only pending municipalities
python -m src.main list-municipalities --pending-only

# Limit results
python -m src.main list-municipalities --limit 100
```

### Uruchomienie Celery Worker

```bash
# Start Celery worker
celery -A src.worker.celery_app worker --loglevel=info

# Start Celery beat (scheduler for periodic tasks)
celery -A src.worker.celery_app beat --loglevel=info
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f worker

# Stop services
docker-compose down
```

## Struktura bazy danych / Database Schema

### Główne tabele / Main Tables

1. **voivodeships** - Województwa
2. **counties** - Powiaty
3. **municipalities** - Gminy
4. **parcels** - Działki gruntu
   - `parcel_id` - Numer działki
   - `area_m2` - Powierzchnia w m²
   - `area_ha` - Powierzchnia w hektarach
   - `geometry` - Geometria (MULTIPOLYGON)
   - `land_use_code` - Kod użytkowania gruntu
5. **spatial_plans** - Plany zagospodarowania przestrzennego
   - `plan_type` - Typ planu (MPZP, SUiKZP)
   - `zoning_code` - Symbol przeznaczenia terenu
   - `geometry` - Geometria planu
6. **scraper_logs** - Logi operacji scrapowania

### Przykładowe zapytania SQL / Sample SQL Queries

```sql
-- Get all parcels for a municipality
SELECT p.parcel_id, p.area_m2, p.land_use_code, ST_AsGeoJSON(p.geometry)
FROM parcels p
JOIN municipalities m ON p.municipality_id = m.id
WHERE m.code = '146301';

-- Get spatial plans with zoning for investment
SELECT sp.name, sp.zoning_code, sp.zoning_description
FROM spatial_plans sp
JOIN municipalities m ON sp.municipality_id = m.id
WHERE m.code = '146301'
  AND sp.plan_type = 'mpzp'
  AND sp.is_valid = true;

-- Get municipalities with most parcels
SELECT m.name, m.total_parcels, m.total_area_m2 / 10000 as area_ha
FROM municipalities m
WHERE m.total_parcels > 0
ORDER BY m.total_parcels DESC
LIMIT 10;

-- Find parcels by minimum area
SELECT m.name, p.parcel_id, p.area_ha
FROM parcels p
JOIN municipalities m ON p.municipality_id = m.id
WHERE p.area_ha >= 1.0  -- Działki >= 1 ha
ORDER BY p.area_ha DESC;
```

## Źródła danych / Data Sources

1. **ULDK (Usługi Lokalizacji Działek Katastralnych)**
   - URL: https://uldk.gugik.gov.pl/
   - Dane: Granice działek, powierzchnie, użytkowanie gruntu
   - Format: WFS (Web Feature Service)

2. **Geoportal.gov.pl**
   - URL: https://mapy.geoportal.gov.pl/
   - Dane: MPZP, SUiKZP, dokumenty planistyczne
   - Format: WFS, WMS

## Roadmap

- [ ] Export danych do GeoJSON/Shapefile
- [ ] API REST do wyszukiwania działek
- [ ] Dashboard webowy do monitorowania
- [ ] Integracja z dodatkowymi źródłami danych gminnych
- [ ] System rekomendacji dla inwestorów
- [ ] Analiza geospatialna (najbliższe drogi, media, etc.)
- [ ] Powiadomienia o nowych planach zagospodarowania

## Konfiguracja / Configuration

### Zmienne środowiskowe / Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agentkataster
DB_USER=postgres
DB_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Scraper settings
CONCURRENT_REQUESTS=5        # Number of concurrent requests
REQUEST_DELAY=1.0            # Delay between requests (seconds)
MAX_RETRIES=3                # Max retry attempts

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log
```

## Monitoring

### Celery Flower (Web UI)

```bash
# Install Flower
pip install flower

# Start Flower
celery -A src.worker.celery_app flower --port=5555
```

Access at http://localhost:5555

## Rozwiązywanie problemów / Troubleshooting

### Problem: Brak danych dla gminy
- Sprawdź czy gmina istnieje w ULDK
- Sprawdź logi w `logs/scraper.log`
- Niektóre gminy mogą nie mieć danych w systemie

### Problem: Błędy połączenia z bazą danych
- Sprawdź czy PostgreSQL działa: `docker-compose ps`
- Sprawdź credentials w `.env`
- Upewnij się że PostGIS jest zainstalowany

### Problem: Celery worker nie przetwarza zadań
- Sprawdź czy Redis działa
- Sprawdź logi worker: `docker-compose logs worker`
- Restart worker: `docker-compose restart worker`

## Licencja / License

MIT License - see LICENSE file

## Kontakt / Contact

Jeśli masz pytania lub sugestie, otwórz issue na GitHubie.

## Uwagi prawne / Legal Notice

Narzędzie jest przeznaczone do legalnego pobierania danych publicznych z Geoportalu.
Przestrzegaj zasad korzystania z usług GUGiK i limitów requestów.

This tool is intended for legal collection of public data from Geoportal.
Please respect GUGiK service terms and request rate limits.