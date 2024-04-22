from bs4 import BeautifulSoup
from urllib.parse import urljoin

class CssSelectorParser:
    """
    Далее приведен упрощенный алгоритм парсинга сайта.
    Будет происходить парсинг двух страниц:
    страница с витриной книг и страница с определенной книгой
    При обработке страницы с определенной книгой мы берем всю полезную инфу и не 
    рассматриваем доп. Urls.
    Дополнительные Urls с ссылками на книги и ссылками на другие топики
    будем брать со страницы с витриной
    """

    def _parse_book(self, root):
        """
        Достанем title и цену книжки
        """
        result = {}
        title_elem = root.select_one("title")
        if title_elem is not None:
            title_text = title_elem.text
            title_text = title_text[:title_text.find('|')].strip()
            result['title'] = title_text

        # пытаемся найти тег `meta` с аттрибутом `description`
        description = root.select_one("meta[description]")
        if description is not None:
            description_text = description.attrs['content']
            result['description'] = description_text

        price = root.select_one(".product_main p.price_color")
        if price is not None:
            result["price"] = price.text

        return result

    def _parse_next(self, root, base_url):
        # ссылки лежат в теге a, которые
        # являются предками тега article с классом product_pod
        links = root.select(".product_pod a")
        # для каждой ссылки нужно достать значение аттрибута href
        # и привести к абсолютному url
        to_return = []
        for link in links:
            url = link.attrs["href"]
            to_return.append(urljoin(base_url, url))

        next_page = root.select_one("li.next a")
        if next_page is not None:
            url = next_page.attrs['href']
            to_return.append(url)
        return to_return

    def parse(self, content, base_url):
        soup = BeautifulSoup(content)
        element = soup.select_one('article.product_page')
        if element is not None:
            result = self._parse_book(soup)
            # 
            return result, []
        next_links = self._parse_next(soup, base_url)
        return None, next_links