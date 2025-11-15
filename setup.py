"""Setup configuration for AgentKataster."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentkataster",
    version="0.1.0",
    author="AgentKataster Team",
    description="Polish Land Registry Data Scraper - Collect parcel and spatial plan data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agentkataster",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "asyncio>=3.4.3",
        "aiohttp>=3.9.1",
        "requests>=2.31.0",
        "geopandas>=0.14.1",
        "shapely>=2.0.2",
        "pyproj>=3.6.1",
        "owslib>=0.29.3",
        "fiona>=1.9.5",
        "psycopg2-binary>=2.9.9",
        "sqlalchemy>=2.0.23",
        "geoalchemy2>=0.14.2",
        "alembic>=1.13.0",
        "celery>=5.3.4",
        "redis>=5.0.1",
        "pandas>=2.1.4",
        "numpy>=1.26.2",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
        "loguru>=0.7.2",
        "tqdm>=4.66.1",
        "typer>=0.9.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "agentkataster=src.main:app",
        ],
    },
)
