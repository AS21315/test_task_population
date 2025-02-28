from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.future import select
import asyncio
import sys
import os

sys.path.append('/app')
from models import Country

class AsyncDataPrinter:
    def __init__(self, database_url=None):
        self.database_url = database_url or "postgresql+asyncpg://postgres:qwerty123@postgres/population_service"
        self.engine = None
        self.session = None
    
    async def connect_to_database(self):
        print(f"Connecting to database: {self.database_url}")
        self.engine = create_async_engine(self.database_url)
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.session = async_session()
    
    async def get_region_stats_single_query(self):
        RegionStats = aliased(Country)
        LargestCountry = aliased(Country)
        SmallestCountry = aliased(Country)
        
        region_stats = select(
            RegionStats.subregion,
            func.sum(RegionStats.population_2023).label('total_population'),
            func.max(RegionStats.population_2023).label('max_population'),
            func.min(RegionStats.population_2023).label('min_population')
        ).filter(
            RegionStats.subregion != ''
        ).group_by(
            RegionStats.subregion
        ).subquery('region_stats')
        
        query = select(
            region_stats.c.subregion,
            region_stats.c.total_population,
            LargestCountry.name.label('largest_country'),
            LargestCountry.population_2023.label('largest_population'),
            SmallestCountry.name.label('smallest_country'),
            SmallestCountry.population_2023.label('smallest_population')
        ).join(
            LargestCountry,
            and_(
                LargestCountry.subregion == region_stats.c.subregion,
                LargestCountry.population_2023 == region_stats.c.max_population
            )
        ).join(
            SmallestCountry,
            and_(
                SmallestCountry.subregion == region_stats.c.subregion,
                SmallestCountry.population_2023 == region_stats.c.min_population
            )
        ).order_by(
            region_stats.c.subregion
        )
        
        result = await self.session.execute(query)
        return result.all()
    
    def print_results(self, results):
        for row in results:
            print(f"Region: {row.subregion}")
            print(f"Total Population: {row.total_population}")
            print(f"Largest Country: {row.largest_country} (Population: {row.largest_population})")
            print(f"Smallest Country: {row.smallest_country} (Population: {row.smallest_population})")
            print()
    
    async def close(self):
        if self.session:
            await self.session.close()
        if self.engine:
            await self.engine.dispose()
    
    async def run(self):
        try:
            print("Waiting for PostgreSQL to be ready...")
            await asyncio.sleep(2)
            
            await self.connect_to_database()
            
            results = await self.get_region_stats_single_query()
            self.print_results(results)
            
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()

if __name__ == "__main__":
    printer = AsyncDataPrinter()
    asyncio.run(printer.run())