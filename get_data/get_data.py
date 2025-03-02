from bs4 import BeautifulSoup
import aiohttp
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import time
import sys
import os

sys.path.append('/app')
from models import Country, Base, init_db

class AsyncDataFetcher:
    def __init__(self, database_url=None):
        self.database_url = database_url or "postgresql+asyncpg://postgres:qwerty123@postgres/population_service"
        self.engine = None
        self.session = None

        self.data_source = os.environ.get('DATA_SOURCE', 'wikipedia').lower()
        print(f"Data source set to: {self.data_source}")
    
    async def connect_to_database(self):
        print(f"Connecting to database: {self.database_url}")
        self.engine = create_async_engine(self.database_url)
        
        async with self.engine.begin() as conn:
            await conn.run_sync(init_db)
        
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.session = async_session()
    
    async def fetch_data(self):
        if self.data_source == 'wikipedia':
            print("Fetching data from Wikipedia...")
            url = "https://en.wikipedia.org/w/index.php?title=List_of_countries_by_population_(United_Nations)&oldid=1215058959"
        elif self.data_source == 'statisticstimes':
            print("Fetching data from Statistics Times...")
            url = "https://statisticstimes.com/demographics/countries-by-population.php"
        else:
            raise ValueError(f"Unknown data source: {self.data_source}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html_content = await response.text()
        
        return BeautifulSoup(html_content, 'html.parser')
    
    def parse_table(self, soup):
        if self.data_source == 'wikipedia':
            tables = soup.find_all('table', {'class': 'wikitable'})
            print(f"Found {len(tables)} tables with class 'wikitable'")
            
            if len(tables) > 0:
                table = tables[0]
                headers = table.find_all('th')
                header_texts = [h.get_text(strip=True) for h in headers]
                print(f"Using table with headers: {header_texts[:5]}")
                return table
            else:
                print("Could not find any tables with class 'wikitable'")
                return None
        elif self.data_source == 'statisticstimes':
            table = soup.find('table', {'id': 'table_id'})
            if table:

                headers = []
                for th in table.find_all('th'):
                    headers.append(th.get_text(strip=True))
                print(f"Using table with headers: {headers[:5]}")
                return table
            else:
                print("Could not find table with id 'table_id'")
                return None
    
    async def process_data(self, table):
        print("Clearing existing data...")
        await self.session.execute(Country.__table__.delete())
        
        rows = table.find('tbody').find_all('tr')
        print(f"Found {len(rows)} rows in the table")
        
        countries_added = 0
        
        batch_size = 50
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            tasks = [self._process_row(row) for row in batch]
            results = await asyncio.gather(*tasks)
            
            for country in results:
                if country:
                    self.session.add(country)
                    countries_added += 1
            
            await self.session.commit()
            print(f"Committed batch of {len(batch)} rows")
        
        print(f"Total of {countries_added} countries added to database")
        return countries_added
    
    async def _process_row(self, row):
        if self.data_source == 'wikipedia':
            return self._process_wikipedia_row(row)
        elif self.data_source == 'statisticstimes':
            return self._process_statisticstimes_row(row)
    
    def _process_wikipedia_row(self, row):
        columns = row.find_all('td')
        
        if len(columns) >= 5:
            return self._create_country_from_wikipedia_row(columns)
        return None
    
    def _process_statisticstimes_row(self, row):
        try:

            cells = row.find_all('td')
            

            if len(cells) < 8:
                return None
            

            country_cell = cells[0]
            if country_cell.find('a'):

                country_name = country_cell.find('a').get_text(strip=True)
            else:
                country_name = country_cell.get_text(strip=True)
            

            population_2023_text = cells[1].get_text(strip=True).replace(',', '')
            population_2024_text = cells[3].get_text(strip=True).replace(',', '')
            
            try:
                population_2022 = int(population_2023_text) 
            except ValueError:
                print(f"Could not convert 2023 population for {country_name}: {population_2023_text}")
                population_2022 = 0
                
            try:
                population_2023 = int(population_2024_text)  
            except ValueError:
                print(f"Could not convert 2024 population for {country_name}: {population_2024_text}")
                population_2023 = 0
            
        
            change_percent = None
            if population_2022 > 0:
                change_percent = (population_2023 - population_2022) / population_2022 * 100
            
        
            continent = cells[8].get_text(strip=True)
            
            return Country(
                name=country_name,
                population_2022=population_2022,
                population_2023=population_2023,
                population_change=change_percent,
                continent=continent,
                subregion=continent 
            )
        except Exception as e:
            print(f"Error processing row for statisticstimes: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_country_from_wikipedia_row(self, columns):
        name = columns[0].get_text(strip=True)
        
        try:
            population_2022_text = columns[1].get_text(strip=True).replace(",", "")
            population_2023_text = columns[2].get_text(strip=True).replace(",", "")
            
            try:
                population_2022 = int(population_2022_text)
            except ValueError:
                print(f"Could not convert 2022 population for {name}: {population_2022_text}")
                population_2022 = 0
                
            try:
                population_2023 = int(population_2023_text)
            except ValueError:
                print(f"Could not convert 2023 population for {name}: {population_2023_text}")
                population_2023 = 0
            
            change_percent = None
            if population_2022 > 0:
                change_percent = (population_2023 - population_2022) / population_2022 * 100
        except (ValueError, IndexError) as e:
            print(f"Error processing population data for {name}: {e}")
            return None
        
        try:
            continent = columns[4].get_text(strip=True)
            subregion = ""
            if len(columns) > 5:
                subregion = columns[5].get_text(strip=True)
            else:
                subregion = continent
        except IndexError as e:
            print(f"Error processing region data for {name}: {e}")
            return None

        return Country(
            name=name,
            population_2022=population_2022,
            population_2023=population_2023,
            population_change=change_percent,
            continent=continent,
            subregion=subregion
        )
    
    async def close(self):
        if self.session:
            await self.session.close()
        if self.engine:
            await self.engine.dispose()
    
    async def run(self):
        try:
            print("Waiting for PostgreSQL to be ready...")
            await asyncio.sleep(3)
            
            await self.connect_to_database()
            soup = await self.fetch_data()
            table = self.parse_table(soup)
            
            if table:
                countries_added = await self.process_data(table)
                print(f"Data successfully inserted into the database. Added {countries_added} countries.")
            else:
                print("Failed to find or parse the data table.")
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()

if __name__ == "__main__":
    fetcher = AsyncDataFetcher()
    asyncio.run(fetcher.run())