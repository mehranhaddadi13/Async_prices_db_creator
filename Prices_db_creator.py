"""
In this personal exercise on using asynchronous libraries, we create a sqlite database of products
of the 'Mobile Phones' section of 'technolife.ir' online store.
"""

import asyncio
import aiosqlite
from bs4 import BeautifulSoup
import requests
import os

home_url = "http://technolife.ir"
# A valid user agent should be provided for our request to the website so our request won't be rejected
h = {"user-agent": ""}
db_path = "~/Personal projects/Prices_db_creator/Database/Phone_prices.db"
names = []  # Names of mobile phones
prices = []  # Prices of mobile phones


async def db_creator(data: tuple):
    """
    Creates a sqlite database of mobile phones' names and prices with aiosqlite library
    :param data: (name, price) tuple
    """
    # Make a connection to database. If it does not exist, it creates it first
    async with aiosqlite.connect(db_path) as db:
        # Make a connection to mobiles table. If it does not exist, it creates it
        sql_create_table = '''CREATE TABLE IF NOT EXISTS mobiles(name text PRIMARY KEY, price text)'''
        await db.execute(sql_create_table)
        # Our sql command
        sql = '''INSERT INTO mobiles(name, price)
                 VALUES(?,?)'''
        # Running sql command
        await db.execute(sql, data)
        # Register changes into database
        await db.commit()


def check_dir(path: str):
    """
    Checks whether the path exists. If not, creates it
    :param path: Desired path
    """
    if not os.path.exists(path):
        os.mkdir(path)


def get_html_sync(url: str) -> str:
    """
        Make a connection to the url and return its HTML content. Since we make just one connection
        at a time, there is no need to do it via aiohttp library.
        :param str url: Desired url
        :return: HTML context of url
        :rtype: str
        """
    res = requests.get(url, headers=h)  # Make connection with headers containing valid user-agent
    if res.status_code == 200:  # Returns the HTML context if the request is successful
        return res.text


def parse_html_sync(url: str, task_type: str) -> str:
    """
        HTML parser by which we obtain desired data.
        Since we use BeautifulSoup, which is a synchronous library, there is no point in using
        aiohttp library here.
        :param str url: The url we want to get data from
        :param str task_type: Our task type, either 'cat' or 'product'
        :return: If the task_type is 'cat', it returns url
        :rtype: str
        """
    text = get_html_sync(url)   # We get HTML context of url
    # Create a dom object with BeautifulSoup library to search through HTML context via tags
    dom = BeautifulSoup(text, 'html.parser')
    # Our first task to find out mobile phones category's url
    if task_type == "cat":
        # Based on my personal inspection, we can obtain mobile phones section's url through a link
        # whose string tag contains the mentioned text
        for link in dom.find_all('a'):
            if link.string == "قیمت گوشی":
                return url + link.get('href')
    # Second task to obtain products' names and prices
    elif task_type == "product":
        # Getting names. The method is based on my personal inspection
        for a_tag in dom.find_all('a'):
            if a_tag.get('class') and len(a_tag.get('class')) != 0 and a_tag.get('class')[0] == "line-clamp-3":
                names.append(a_tag.string)
        # Getting prices. The method is based on my personal inspection
        for p_tag in dom.find_all('p'):
            if p_tag.get('class') and len(p_tag.get('class')) != 0 and p_tag.get('class')[0] == "text-[22px]":
                prices.append(p_tag.contents[0])


async def main():
    cat_url = parse_html_sync(home_url, "cat")  # Obtaining desired(mobile phones) category's url
    parse_html_sync(cat_url, "product")  # Adds names and prices of products to their related lists
    # Some products' names contain \t, we omit it here
    for i in range(len(names)):
        if '\t' in names[i]:
            names[i] = names[i].replace('\t', '')
    # Create asynchronous tasks to save data to the database
    tasks = [db_creator(data) for data in zip(names, prices)]
    # Make sure that Database path exists
    check_dir(os.path.dirname(db_path))
    # Run tasks
    await asyncio.gather(*tasks)
    # This code fragment is for checking the authenticity of database's data
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute("SELECT * FROM mobiles") as cur:
            async for row in cur:
                print(row)


if __name__ == "__main__":
    asyncio.run(main())
