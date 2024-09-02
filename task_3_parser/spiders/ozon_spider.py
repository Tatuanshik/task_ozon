from typing import Any
import pandas as pd
import scrapy
from scrapy_selenium import SeleniumRequest
from collections import Counter


class QuotesSpider(scrapy.Spider):
    name = "ozon"

    def __init__(self):
        self.links = []
        self.product_data = []

    def start_requests(self):
        urls = ['https://ozon.by/category/smartfony-15502/?sorting=rating',
                'https://ozon.by/category/smartfony-15502/?page=2&sorting=rating',
                'https://ozon.by/category/smartfony-15502/?page=3&sorting=rating',]
        for url in urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response) -> Any:
        product_links = response.css('a.tile-hover-target::attr(href)').getall()
        for link in product_links:
            full_link = response.urljoin(link)
            if len(self.links) < 100 and full_link not in self.links:
                self.links.append(full_link)
                yield SeleniumRequest(
                    url=full_link,
                    callback=self.parse_product,
                    wait_time=10
                )
            if len(self.links) >= 100:
                break

    def parse_product(self, response):
        os_version = response.css('dt:contains("Версия iOS") + dd::text, dt:contains("Версия Android") + dd::text').get()
        if os_version is None:
            os_version = response.css('dt:contains("Версия iOS") + dd a::text, '
                                      'dt:contains("Версия Android") + dd a::text,'
                                      'dt:contains("Операционная система") + dd a::text,'
                                      'dt:contains("Операционная система") + dd::text').get()
        self.product_data.append({
            'os_version': os_version,
            'url': response.url,
        })

    def closed(self, reasons):
        self.save_data()

    def save_data(self):
        df = pd.DataFrame(self.product_data)
        counts = Counter(df['os_version'])
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        with open('models_os_version.txt', 'w', encoding='utf-8') as f:
            for os_version, count in sorted_counts:
                f.write(f"{os_version} — {count}\n")
