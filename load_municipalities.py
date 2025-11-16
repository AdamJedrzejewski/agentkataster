"""Load municipalities from static list into database."""
from src.database import SessionLocal
from src.models import Municipality, ProcessingStatus

# Top 100 largest Polish municipalities by population
# Format: (name, TERYT code, type)
MUNICIPALITIES = [
    # Województwo mazowieckie
    ("Warszawa", "146501", "miejska"),
    ("Radom", "146201", "miejska"),
    ("Płock", "146101", "miejska"),
    ("Siedlce", "146301", "miejska"),
    ("Pruszków", "142901", "miejska"),
    ("Legionowo", "142401", "miejska"),
    ("Otwock", "142701", "miejska"),
    ("Piaseczno", "142802", "miejsko-wiejska"),
    ("Mińsk Mazowiecki", "142601", "miejska"),
    ("Żyrardów", "146801", "miejska"),

    # Województwo małopolskie
    ("Kraków", "126301", "miejska"),
    ("Tarnów", "126601", "miejska"),
    ("Nowy Sącz", "126401", "miejska"),
    ("Oświęcim", "121901", "miejska"),
    ("Wieliczka", "123002", "miejsko-wiejska"),

    # Województwo śląskie
    ("Katowice", "246301", "miejska"),
    ("Częstochowa", "246101", "miejska"),
    ("Sosnowiec", "246901", "miejska"),
    ("Gliwice", "246201", "miejska"),
    ("Zabrze", "247101", "miejska"),
    ("Bielsko-Biała", "246001", "miejska"),
    ("Bytom", "246601", "miejska"),
    ("Rybnik", "246801", "miejska"),
    ("Ruda Śląska", "247001", "miejska"),
    ("Tychy", "246401", "miejska"),
    ("Dąbrowa Górnicza", "246501", "miejska"),
    ("Chorzów", "246701", "miejska"),
    ("Jaworzno", "240701", "miejska"),
    ("Mysłowice", "247201", "miejska"),
    ("Będzin", "240301", "miejska"),

    # Województwo dolnośląskie
    ("Wrocław", "026301", "miejska"),
    ("Wałbrzych", "026401", "miejska"),
    ("Legnica", "026101", "miejska"),
    ("Jelenia Góra", "026201", "miejska"),

    # Województwo wielkopolskie
    ("Poznań", "306301", "miejska"),
    ("Kalisz", "306101", "miejska"),
    ("Konin", "306201", "miejska"),
    ("Piła", "306401", "miejska"),
    ("Ostrów Wielkopolski", "306601", "miejska"),
    ("Gniezno", "305901", "miejska"),

    # Województwo pomorskie
    ("Gdańsk", "226101", "miejska"),
    ("Gdynia", "226201", "miejska"),
    ("Słupsk", "226301", "miejska"),
    ("Sopot", "226401", "miejska"),
    ("Wejherowo", "220801", "miejska"),

    # Województwo łódzkie
    ("Łódź", "106301", "miejska"),
    ("Piotrków Trybunalski", "106201", "miejska"),
    ("Tomaszów Mazowiecki", "106101", "miejska"),
    ("Skierniewice", "106401", "miejska"),
    ("Pabianice", "101701", "miejska"),

    # Województwo zachodniopomorskie
    ("Szczecin", "326301", "miejska"),
    ("Koszalin", "326101", "miejska"),
    ("Stargard", "327001", "miejska"),
    ("Świnoujście", "326401", "miejska"),

    # Województwo lubelskie
    ("Lublin", "066301", "miejska"),
    ("Chełm", "066101", "miejska"),
    ("Zamość", "066401", "miejska"),
    ("Biała Podlaska", "066201", "miejska"),
    ("Puławy", "061901", "miejska"),

    # Województwo podkarpackie
    ("Rzeszów", "186301", "miejska"),
    ("Przemyśl", "186201", "miejska"),
    ("Stalowa Wola", "181801", "miejska"),
    ("Mielec", "181301", "miejska"),
    ("Tarnobrzeg", "186401", "miejska"),
    ("Krosno", "186101", "miejska"),

    # Województwo kujawsko-pomorskie
    ("Bydgoszcz", "046101", "miejska"),
    ("Toruń", "046301", "miejska"),
    ("Włocławek", "046401", "miejska"),
    ("Grudziądz", "046201", "miejska"),

    # Województwo warmińsko-mazurskie
    ("Olsztyn", "286301", "miejska"),
    ("Elbląg", "286101", "miejska"),
    ("Ełk", "286201", "miejska"),

    # Województwo podlaskie
    ("Białystok", "206301", "miejska"),
    ("Suwałki", "206401", "miejska"),
    ("Łomża", "206201", "miejska"),
    ("Augustów", "201701", "miejska"),

    # Województwo opolskie
    ("Opole", "166301", "miejska"),
    ("Kędzierzyn-Koźle", "166201", "miejska"),
    ("Nysa", "166101", "miejska"),

    # Województwo lubuskie
    ("Gorzów Wielkopolski", "086101", "miejska"),
    ("Zielona Góra", "086301", "miejska"),

    # Województwo świętokrzyskie
    ("Kielce", "266301", "miejska"),
    ("Ostrowiec Świętokrzyski", "266201", "miejska"),
    ("Starachowice", "261801", "miejska"),
]


def load_municipalities():
    """Load municipalities into database."""
    db = SessionLocal()

    try:
        print(f"Loading {len(MUNICIPALITIES)} municipalities...")

        added = 0
        skipped = 0

        for name, code, muni_type in MUNICIPALITIES:
            # Check if already exists
            existing = db.query(Municipality).filter_by(code=code).first()

            if existing:
                print(f"  ⏭️  Skipping {name} ({code}) - already exists")
                skipped += 1
                continue

            # Create new municipality
            municipality = Municipality(
                name=name,
                code=code,
                type=muni_type,
                parcels_status=ProcessingStatus.PENDING,
                plans_status=ProcessingStatus.PENDING,
                county_id=None,  # We can add this later
            )

            db.add(municipality)
            added += 1

            if added % 10 == 0:
                db.commit()
                print(f"  ✓ Added {added} municipalities...")

        # Final commit
        db.commit()

        print(f"\n✅ Success!")
        print(f"   Added: {added}")
        print(f"   Skipped: {skipped}")
        print(f"   Total in DB: {db.query(Municipality).count()}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    load_municipalities()
