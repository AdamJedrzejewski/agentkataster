# Quick Start Guide - AgentKataster

Szybki start dla narzędzia AgentKataster do zbierania danych o działkach gruntu.

## 1. Wymagania wstępne

- Docker i Docker Compose zainstalowane
- Co najmniej 5GB wolnego miejsca na dysku
- Połączenie z internetem

## 2. Krok po kroku

### Krok 1: Sklonuj repozytorium

```bash
git clone <your-repo-url>
cd agentkataster
```

### Krok 2: Konfiguracja

```bash
# Skopiuj przykładowy plik konfiguracyjny
cp .env.example .env

# (Opcjonalnie) Edytuj .env jeśli chcesz zmienić hasła
nano .env
```

### Krok 3: Uruchom Docker Compose

```bash
# Uruchom wszystkie serwisy (PostgreSQL, Redis, Worker)
docker-compose up -d

# Sprawdź czy serwisy działają
docker-compose ps
```

Powinieneś zobaczyć:
- agentkataster_postgres
- agentkataster_redis
- agentkataster_worker
- agentkataster_scheduler

### Krok 4: Inicjalizacja bazy danych

```bash
# Zainicjalizuj bazę i pobierz listę gmin
docker-compose exec worker python -m src.main init
```

To może potrwać kilka minut - narzędzie pobiera listę wszystkich ~2500 gmin w Polsce.

### Krok 5: Sprawdź status

```bash
docker-compose exec worker python -m src.main status
```

Zobaczysz statystyki:
- Ile gmin jest w bazie
- Ile gmin oczekuje na przetworzenie
- Ile działek zostało już zebranych

### Krok 6: Uruchom zbieranie danych

Możesz wybrać jedną z opcji:

**Opcja A: Zbieranie dla jednej gminy (do testów)**

```bash
# Przykład dla Warszawy (TERYT: 146501)
docker-compose exec worker python -m src.main scrape-municipality 146501
```

**Opcja B: Uruchom zbieranie dla wszystkich gmin**

```bash
docker-compose exec worker python -m src.main start
```

**Opcja C: Tylko działki (bez planów zagospodarowania)**

```bash
docker-compose exec worker python -m src.main start --no-plans
```

### Krok 7: Monitoruj postęp

```bash
# Zobacz logi worker-a
docker-compose logs -f worker

# Lub sprawdź status co jakiś czas
watch -n 60 'docker-compose exec worker python -m src.main status'
```

### Krok 8: Lista gmin

```bash
# Zobacz listę gmin
docker-compose exec worker python -m src.main list-municipalities --limit 20

# Zobacz tylko gminy oczekujące na przetworzenie
docker-compose exec worker python -m src.main list-municipalities --pending-only
```

## 3. Kody TERYT dla wybranych miast

Jeśli chcesz przetestować na konkretnym mieście:

- Warszawa: 146501
- Kraków: 126301
- Wrocław: 026301
- Poznań: 306301
- Gdańsk: 226101

Przykład:
```bash
docker-compose exec worker python -m src.main scrape-municipality 126301
```

## 4. Dostęp do bazy danych

Możesz połączyć się z bazą PostgreSQL:

```bash
docker-compose exec postgres psql -U postgres -d agentkataster
```

Przykładowe zapytania:

```sql
-- Ile gmin jest w bazie?
SELECT COUNT(*) FROM municipalities;

-- Ile działek zebrano?
SELECT COUNT(*) FROM parcels;

-- Top 10 gmin z największą liczbą działek
SELECT name, total_parcels
FROM municipalities
WHERE total_parcels > 0
ORDER BY total_parcels DESC
LIMIT 10;

-- Działki dla konkretnej gminy
SELECT parcel_id, area_ha, land_use_code
FROM parcels p
JOIN municipalities m ON p.municipality_id = m.id
WHERE m.code = '146501'
LIMIT 10;
```

## 5. Monitoring z Flower

Flower to webowy interfejs do monitorowania Celery.

```bash
# Uruchom Flower
docker-compose exec worker celery -A src.worker.celery_app flower --port=5555 --address=0.0.0.0
```

Następnie otwórz w przeglądarce: http://localhost:5555

## 6. Zatrzymywanie i wznawianie

```bash
# Zatrzymaj wszystkie serwisy
docker-compose down

# Wznów
docker-compose up -d

# Wznów z czyszczeniem logów
docker-compose down && docker-compose up -d
```

## 7. Eksport danych

```bash
# Export działek do GeoJSON
docker-compose exec worker python scripts/export_data.py --type parcels

# Export planów zagospodarowania
docker-compose exec worker python scripts/export_data.py --type plans

# Export dla konkretnej gminy
docker-compose exec worker python scripts/export_data.py --municipality 146501
```

Pliki będą w katalogu `exports/`.

## 8. Troubleshooting

### Problem: Worker nie działa

```bash
# Sprawdź logi
docker-compose logs worker

# Restart worker
docker-compose restart worker
```

### Problem: Baza danych nie odpowiada

```bash
# Sprawdź status PostgreSQL
docker-compose logs postgres

# Restart bazy
docker-compose restart postgres
```

### Problem: Brak miejsca na dysku

```bash
# Sprawdź rozmiar bazy
docker-compose exec postgres psql -U postgres -d agentkataster -c "SELECT pg_size_pretty(pg_database_size('agentkataster'));"

# Wyczyść stare logi
docker-compose exec postgres psql -U postgres -d agentkataster -c "DELETE FROM scraper_logs WHERE created_at < NOW() - INTERVAL '30 days';"
```

## 9. Następne kroki

Po zebraniu danych możesz:

1. **Zbudować API** do wyszukiwania działek
2. **Stworzyć dashboard** do wizualizacji danych
3. **Dodać analizy** - np. wyszukiwanie działek spełniających kryteria inwestycyjne
4. **Zintegrować z mapami** - np. Leaflet, Mapbox
5. **Dodać powiadomienia** - o nowych planach zagospodarowania

## 10. Wsparcie

Jeśli masz problemy:

1. Sprawdź logi: `docker-compose logs -f`
2. Sprawdź status: `docker-compose exec worker python -m src.main status`
3. Otwórz issue na GitHubie

---

**Powodzenia w zbieraniu danych! 🗺️**
