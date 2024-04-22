from collections import deque
import requests
from runners.utils import Item

class SimpleRunner:
    def __init__(self, parser, sink, logger, seed_urls, rate=100, max_tries=5):
        self._parser = parser
        self._sink = sink            # то, куда мы сохраняем результат
        self._logger = logger        # для ошибок
        self._seed_urls = seed_urls  # урлы, с которых начнем разбор
        self._rate = rate            # ограничение числа хождений на сайт за определенное время
        self._max_tries = max_tries  # в случае возникновения ошибок(при парсинге) будет пробовать снова парсить
        self._seen = set()
        self._to_process = deque() 
        for url in self._seed_urls:
            self._to_process.append(Item(url))
            self._seen.add(url)

    def _process(self, item):
        self._logger.info(f"Processing {item.url}")
        resp = requests.get(item.url)
        resp.raise_for_status()
        content = resp.content
        result, next_urls = self._parser.parse(content, item.url)
        self._logger.info(f"next_urls: {next_urls}")
        return result, next_urls

    def _write(self, item, result, error=None):
        self._logger.info(f"Writing for {item.url}")
        if error is not None:
            self._sink.write({"error": str(error), 'result': None})
            return
        self._sink.write({"error": None, 'result': result, 'url': item.url})

    def _filter(self, urls):
        to_return = []
        for url in urls:
            if url in self._seen:
                continue
            to_return.append(url)

        return to_return

    def run(self):
        # алгоритм обхода страничек сайта
        while self._to_process:
            item = self._to_process.popleft()
            self._logger.info(f"running: {len(self._to_process)}")
            result = None
            next_urls = None
            try:
                result, next_urls = self._process(item)
            except Exception as e:
                self._logger.error(f"Smth wrong: ", e)
                item.tries += 1
                if item.tries > self._max_tries:
                    self._write(item, result, e)
                self._to_process.append(item)

            if result is not None:
                # сохраним полезный контент
                self._write(item, result)

            if next_urls is not None:
                for elem in self._filter(next_urls):
                    self._to_process.append(Item(elem))
                    self._seen.add(elem)
