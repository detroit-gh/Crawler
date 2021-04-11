import csv
from urllib.parse import urljoin

import click
import requests
from bs4 import BeautifulSoup
from requests import PreparedRequest

BASE_URL = 'https://www.work.ua'
QUERY = 'junior+python+developer'


def get_soup(response):
    return BeautifulSoup(response.text, 'lxml')


def get_links_on_page(page_link):
    response = requests.get(page_link)
    soup = get_soup(response)
    offers = soup.find_all('div', class_='job-link')
    links = []
    for offer in offers:
        details_tag1 = offer.find('h2')
        details_tag = details_tag1.find('a')
        details_link = details_tag.attrs['href']
        links.append(urljoin(BASE_URL, details_link))
    return links


def write_to_csv_file(filename, links):
    with open(filename, mode='w') as f:
        header = ['Title', 'Company', 'Address', 'Date', 'URL']
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        with click.progressbar(links, label='Process offers') as bar:
            for link in bar:
                process_offer(writer, link)


def process_offer(writer, offer_link):
    response = requests.get(offer_link)
    soup = get_soup(response)

    title_tag = soup.find('h1')
    title = title_tag.text.strip()

    date_tag = soup.find('span', class_='text-muted')
    date = date_tag.text.strip()

    company_tags = soup.find_all('p', class_='text-indent text-muted add-top-sm')
    for tag in company_tags:
        if tag.find('span').attrs['title'] == 'Дані про компанію':
            company_tag = tag.find('a')
            company = company_tag.find('b').text

    address_tags = soup.find_all('p', class_='text-indent add-top-sm')
    for tag in address_tags:
        if tag.find('span').attrs['title'] == 'Адреса роботи':
            j = tag.text.strip()
            i1 = ''
            if tag.find('span', class_='add-top-xs') is not None:
                i = tag.find('span', class_='add-top-xs')
                i1 = i.text.strip()
            address = j.replace(i1, '').strip()

    writer.writerow({
        'Title': title,
        'Company': company,
        'Address': address,
        'Date': date,
        'URL': offer_link
    })


@click.command()
@click.argument('pages', type=int)
@click.option('-city', type=str, default='kyiv')
def main(pages, city):
    url = urljoin(BASE_URL, f'jobs-{city}' + f'-{QUERY}')

    links = []
    req = PreparedRequest()

    for page_number in range(pages):
        req.prepare_url(url, params={'page': page_number + 1})
        page_links = get_links_on_page(req.url)
        links.extend(page_links)

    filename = f'{QUERY}.csv'
    write_to_csv_file(filename, links)


if __name__ == '__main__':
    main()
