# Population Service

A Docker-based microservice that fetches, stores, and displays population data by country and region.

## Project Overview

This service scrapes population data from either Wikipedia or Statistics Times, stores it in a PostgreSQL database, and provides a tool to display aggregated statistics by region.

### Features:
- Asynchronous data fetching and processing
- PostgreSQL database for data storage
- Docker-compose setup for easy deployment
- Multiple data sources (configurable via environment variable)
- Two separate services: 
  - `get_data`: Retrieves, parses, and stores data
  - `print_data`: Reads and displays aggregated statistics

## Requirements

- Docker and Docker Compose
- Git

## How to Run

1. Clone the repository:
```
git clone https://github.com/yourusername/test_task_population.git
```

2. Navigate to the project directory:
```
cd test_task_population
```

3. Fetch and store the data:
```
docker-compose up get_data
```

4. Display the region statistics:
```
docker-compose up print_data
```

## Configuring Data Source

You can choose between two data sources by modifying the `DATA_SOURCE` environment variable in the Dockerfile for the `get_data` service:

- `wikipedia`: Uses data from the Wikipedia page on countries by population (default)
- `statisticstimes`: Uses data from the Statistics Times website

To change the data source, edit the `get_data/Dockerfile`:

```dockerfile
ENV DATA_SOURCE=statisticstimes  # or "wikipedia"
```

## Output Format

The `print_data` service displays statistics for each region in the following format:
- Region name
- Total region population
- Name of the largest country in the region
- Population of the largest country
- Name of the smallest country in the region
- Population of the smallest country

## Project Structure

```
test_task_population/
├── docker-compose.yml       # Docker Compose configuration
├── models.py                # Database models (SQLAlchemy)
├── get_data/
│   ├── Dockerfile           # Dockerfile for get_data service
│   └── get_data.py          # Data retrieval and storage script
├── print_data/
│   ├── Dockerfile           # Dockerfile for print_data service
│   └── print_data.py        # Data aggregation and display script
└── requirements.txt         # Python dependencies
```

## Technical Implementation

- **Asynchronous Processing**: Uses `asyncio` and `aiohttp` for efficient data fetching and processing
- **Database**: PostgreSQL with SQLAlchemy ORM (async implementation)
- **Web Scraping**: Uses BeautifulSoup to parse website data
- **Containerization**: Docker and Docker Compose for consistent deployment
- **Data Source Flexibility**: Environment variable-based configuration for different data sources

## Database Schema

The application stores country data in a single table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | BigInteger | Primary key |
| name | String | Country name |
| population_2022 | BigInteger | Population in 2022 (or 2023 for Statistics Times) |
| population_2023 | BigInteger | Population in 2023 (or 2024 for Statistics Times) |
| population_change | Float | Percentage change |
| continent | String | Continent name |
| subregion | String | Region/subregion name |

## Data Sources

The application can fetch data from two sources:

1. **Wikipedia**:  
   United Nations population data from Wikipedia:  
   https://en.wikipedia.org/w/index.php?title=List_of_countries_by_population_(United_Nations)&oldid=1215058959

2. **Statistics Times**:  
   Population statistics from Statistics Times:  
   https://statisticstimes.com/demographics/countries-by-population.php