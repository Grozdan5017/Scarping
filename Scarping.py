import requests
from bs4 import BeautifulSoup
import json
from time import sleep
import fake_headers

headers = {
    'accept': 'application/json',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=1, i',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/126.0.0.0 Safari/537.36',
    'x-hhtmfrom': 'vacancy_search_list',
    'x-requested-with': 'XMLHttpRequest',
    'x-static-version': '24.24.5',
}


def headers_HTML():
    headers_gen = fake_headers.Headers(os='win', browser='chrome')
    return headers_gen.generate()


def get_search_page_vacancy(text):
    """Получение json поисковой страницы"""

    params = {
        'text': text,
        'area': [
            '1',  # Москва
            '2',  # Питер
        ],
        'page': '0',
        'disableBrowserCache': 'true',
    }

    try:
        response = requests.get('https://hh.ru/search/vacancy', params=params, headers=headers)
        response.raise_for_status()

        return response.json()
    except Exception as ex:
        print(ex)


def scrap_page_vacancy(data_json):
    """Получение ID объявлений"""

    result_vacancies = []

    try:
        vacancies = data_json['vacancySearchResult']['vacancies']

        for vacancy in vacancies:
            vacancy_id = vacancy['vacancyId']
            result_vacancies.append(vacancy_id)

        return result_vacancies
    except Exception as ex:
        print(ex)


def get_html_vacancy(vacancy_id):
    try:
        response = requests.get(f'https://spb.hh.ru/vacancy/{vacancy_id}', headers=headers_HTML())
        response.raise_for_status()

        return response.text
    except Exception as ex:
        print(ex)


def scrap_html_vacancy(html, search_keywords):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        template = soup.find('template', id='HH-Lux-InitialState').text
        data_json = json.loads(template)
        vacancy_info = data_json['vacancyView']
    except Exception as ex:
        print(ex)
        return

    try:
        vacancy_id = str(vacancy_info['vacancyId'])
        desc = vacancy_info['description']

        for key in search_keywords:
            if key.lower() not in desc.lower():
                print(f'Объявление {vacancy_id} не подходит')
                return

        link = 'https://hh.ru/vacancy/' + vacancy_id
        price_from = vacancy_info['compensation'].get('from')
        price_to = vacancy_info['compensation'].get('to')
        company_name = vacancy_info['company']['name']
        city = vacancy_info['area']['name']

        print(f'Объявление {vacancy_id} собрано')

        return dict(
            link=link,
            price_from=price_from,
            price_to=price_to,
            company_name=company_name,
            city=city
        )

    except Exception as ex:
        print(vacancy_info['vacancyId'], ex, sep='\n')


def main():
    results = []
    keywords = ['Django', 'Flask']

    search_page_json = get_search_page_vacancy(text='python')
    vacancies_id = scrap_page_vacancy(data_json=search_page_json)
    if not vacancies_id:
        return

    for vacancy_id in vacancies_id:
        page_html = get_html_vacancy(vacancy_id=vacancy_id)
        if not page_html:
            continue

        vacancy = scrap_html_vacancy(html=page_html, search_keywords=keywords)
        if not vacancy:
            continue

        results.append(vacancy)
        sleep(0.33)

    with open('vacancies.json', 'w', encoding='utf-8') as file:
        json.dump(results, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
