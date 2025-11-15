# AgentKataster - Workflow i Architektura

## Przepływ danych / Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ŹRÓDŁA DANYCH / DATA SOURCES                  │
├─────────────────────────────────────────────────────────────────┤
│  ULDK (Działki)          │  Geoportal (Plany)                   │
│  uldk.gugik.gov.pl       │  mapy.geoportal.gov.pl               │
│  WFS Service             │  WFS/WMS Services                     │
└──────────────┬───────────┴────────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SCRAPERS                                  │
├─────────────────────────────────────────────────────────────────┤
│  ULDKScraper             │  SpatialPlansScraper                 │
│  - Pobiera granice       │  - Pobiera MPZP                      │
│  - Powierzchnie          │  - Pobiera SUiKZP                    │
│  - Użytkowanie gruntu    │  - Dokumenty                         │
└──────────────┬───────────┴────────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CELERY WORKERS                                │
├─────────────────────────────────────────────────────────────────┤
│  scrape_municipality_parcels  │  scrape_municipality_plans      │
│  - Przetwarza 1 gminę         │  - Przetwarza 1 gminę           │
│  - Zapisuje do bazy           │  - Zapisuje do bazy             │
│  - Loguje operacje            │  - Loguje operacje              │
└──────────────┬───────────┴────────────────┬─────────────────────┘
               │                            │
               ▼                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               POSTGRESQL + POSTGIS DATABASE                      │
├─────────────────────────────────────────────────────────────────┤
│  municipalities  │  parcels  │  spatial_plans  │  scraper_logs  │
└──────────────┬───────────────────────────────┬─────────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UŻYCIE DANYCH / DATA USAGE                  │
├─────────────────────────────────────────────────────────────────┤
│  CLI                 │  Export           │  API (Future)         │
│  - Status            │  - GeoJSON        │  - REST endpoints     │
│  - Zarządzanie       │  - Shapefile      │  - Search             │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow krok po kroku / Step-by-step Workflow

### 1. Inicjalizacja (Jednorazowo)

```
User uruchamia: python -m src.main init
    │
    ├─> Tworzy tabele w bazie (models.py)
    │
    ├─> ULDKScraper.get_municipalities()
    │   └─> Pobiera listę wszystkich gmin z ULDK
    │
    └─> Zapisuje ~2500 gmin do tabeli municipalities
        Status: parcels_status = PENDING
                plans_status = PENDING
```

### 2. Uruchomienie scrapowania

```
User uruchamia: python -m src.main start
    │
    ├─> Wywołuje: process_all_municipalities()
    │
    ├─> Query: SELECT * FROM municipalities
    │          WHERE parcels_status IN ('pending', 'failed')
    │
    └─> Dla każdej gminy:
        └─> scrape_municipality_parcels.delay(municipality_id)
            (Task dodany do kolejki Celery/Redis)
```

### 3. Worker przetwarza zadanie

```
Celery Worker odbiera task: scrape_municipality_parcels(municipality_id)
    │
    ├─> Update: municipality.parcels_status = IN_PROGRESS
    │
    ├─> ULDKScraper.scrape(municipality_code, municipality_name, db)
    │   │
    │   ├─> get_parcels_for_municipality(teryt_code)
    │   │   └─> HTTP Request do ULDK WFS
    │   │       └─> Otrzymuje XML/GML z geometriami
    │   │
    │   ├─> Parsuje XML → GeoDataFrame
    │   │
    │   └─> Zapisuje parcele do bazy (batches po 100)
    │       INSERT INTO parcels (parcel_id, geometry, area_m2, ...)
    │
    ├─> Update: municipality.parcels_status = COMPLETED
    │           municipality.total_parcels = count
    │
    └─> Tworzy ScraperLog z wynikami
```

### 4. Podobnie dla planów zagospodarowania

```
scrape_municipality_plans(municipality_id)
    │
    ├─> SpatialPlansScraper.scrape()
    │   │
    │   ├─> get_plans_for_municipality() → MPZP
    │   ├─> get_plans_for_municipality() → SUiKZP
    │   │
    │   └─> INSERT INTO spatial_plans (...)
    │
    └─> Update: municipality.plans_status = COMPLETED
```

## Architektura komponentów / Component Architecture

### Base Scraper (base_scraper.py)

```python
BaseScraper
├─ __aenter__ / __aexit__  # Async context manager
├─ _rate_limit()            # Opóźnienie między requestami
├─ _make_request()          # HTTP request z retry logic
└─ scrape() [abstract]      # Implementowane przez subklasy
```

### ULDK Scraper (uldk_scraper.py)

```python
ULDKScraper(BaseScraper)
├─ get_municipalities()              # Lista gmin z ULDK
├─ get_parcels_for_municipality()    # Działki dla gminy
├─ _parse_parcels()                  # XML → GeoDataFrame
└─ scrape()                          # Main: pobierz + zapisz
```

### Spatial Plans Scraper (spatial_plans_scraper.py)

```python
SpatialPlansScraper(BaseScraper)
├─ get_plans_for_municipality()      # Plany dla gminy
├─ _fetch_from_geoportal()           # WFS request
├─ _fetch_from_local_geoportal()     # Lokalne geoportale
├─ _parse_geojson_plans()            # JSON → plan objects
└─ scrape()                          # Main: pobierz + zapisz
```

### Celery Worker (worker.py)

```python
Tasks:
├─ scrape_municipality_parcels       # Jednorazowe: scrapuj działki
├─ scrape_municipality_plans         # Jednorazowe: scrapuj plany
├─ process_all_municipalities        # Hurtowe: kolejkuj wszystkie
└─ init_municipalities               # Setup: pobierz listę gmin

Beat Schedule (periodic):
└─ process-municipalities-daily      # Codziennie o 2:00
```

## Model danych / Data Model

### Hierarchia administracyjna

```
Voivodeship (Województwo)
    │
    └─> County (Powiat)
            │
            └─> Municipality (Gmina)
                    │
                    ├─> Parcel (Działka)
                    └─> SpatialPlan (Plan zagospodarowania)
```

### Status Processing

```
PENDING → IN_PROGRESS → COMPLETED
              │
              └─> FAILED
```

## Przykładowy timeline przetwarzania

```
T+0s    User: python -m src.main start
T+0.1s  Redis: Dodano 2479 tasks do kolejki
T+0.2s  Worker: Rozpoczęto scrape_municipality_parcels(1)
T+5s    Worker: ULDK request dla gminy 1
T+8s    Worker: Parsowanie 523 działek
T+12s   Worker: Zapisano 523 działek do bazy
T+12.5s Worker: Status gminy 1 → COMPLETED
T+13s   Worker: Rozpoczęto scrape_municipality_parcels(2)
...
T+50h   Worker: Wszystkie gminy przetworzone!
```

## Optymalizacje

### Rate Limiting
- Delay między requestami: 1s (konfigurowalny)
- Max retry: 3 próby z exponential backoff

### Database Batching
- Commit co 100 działek
- Commit co 50 planów
- Zmniejsza I/O, zwiększa wydajność

### Concurrent Processing
- Wiele worker-ów może działać równolegle
- Każdy worker przetwarza inną gminę
- Redis zapewnia synchronizację

### Geometry Storage
- Używamy EPSG:2180 (Polski układ współrzędnych)
- PostGIS indeksy GIST dla szybkich zapytań przestrzennych
- Konwersja do WGS84 (EPSG:4326) przy eksporcie

## Monitoring i Logging

### Logi aplikacji (Loguru)
```
logs/scraper.log - wszystkie operacje
stderr - komunikaty INFO i wyższe
```

### Logi operacji (ScraperLog table)
```sql
SELECT
    operation_type,
    status,
    AVG(duration_seconds) as avg_duration,
    SUM(records_processed) as total_records
FROM scraper_logs
GROUP BY operation_type, status;
```

### Celery Flower
```
http://localhost:5555
- Active tasks
- Worker status
- Task history
- Performance metrics
```

## Rozszerzalność / Extensibility

### Dodawanie nowego scrapera

1. Utwórz klasę dziedziczącą po `BaseScraper`
2. Zaimplementuj metodę `scrape()`
3. Dodaj task w `worker.py`
4. Dodaj model danych w `models.py` (jeśli potrzebny)

### Dodawanie nowego źródła danych

```python
class NewDataSourceScraper(BaseScraper):
    async def scrape(self, municipality_code, municipality_name, db_session):
        # Your implementation
        pass
```

### Dodawanie analizy danych

```python
# Przykład: znajdź działki nadające się pod inwestycję
def find_investment_parcels(min_area_ha, zoning_codes):
    query = """
    SELECT p.*
    FROM parcels p
    JOIN spatial_plans sp ON ST_Intersects(p.geometry, sp.geometry)
    WHERE p.area_ha >= :min_area
      AND sp.zoning_code IN :zoning_codes
      AND sp.is_valid = true
    """
    # ...
```

## Bezpieczeństwo i etyka

### Respektowanie limitów
- Rate limiting: 1 request/second
- Retry z backoff
- User-Agent: identyfikacja jako AgentKataster

### Dane publiczne
- Wszystkie dane z ULDK i Geoportalu są publiczne
- Narzędzie nie obchodzi żadnych zabezpieczeń
- Dane dostępne są legalnie przez API

### Przechowywanie danych
- Baza lokalna
- Backup regularny (user's responsibility)
- GDPR: dane publiczne, nie osobowe

---

**Autor:** AgentKataster Team
**Wersja:** 0.1.0
**Data:** 2024
