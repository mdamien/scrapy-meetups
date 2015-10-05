# -*- coding: utf-8 -*-
import scrapy

def title(response):
    return response.selector.xpath('//title/text()').extract()[0] \
        .replace('- Meetup','').strip()

def attr(x, k):
    r = x.css('::attr("{}")'.format(k))
    if len(r) > 0:
        return r[0].extract()

def extract_metas(response):
    d = {}
    for meta in response.css('meta'):
        key = attr(meta, 'name')
        if not key:
            key = attr(meta, 'property')
        if key:
            value = attr(meta, 'content')
            d[key] = value
    return d

def extract_location(metas):
    loc = {}
    for key, value in metas.items():
        key = key.replace('og:','').replace('geo.','')
        if key in ('placename', 'region', 'country-name', \
                'latitude', 'longitude', 'locality','postal-code'):
            if 'tude' in key:
                value = float(value)
            loc[key] = value
    return loc

class MeetupSpider(scrapy.Spider):
    name = 'meetup'
    allowed_domains = ["meetup.com"]
    start_urls = ['http://www.meetup.com/hackerhours/']

    def parse(self, response):
        nb_of_members = int(response.css('.lastUnit.align-right::text')[0] \
                .extract().replace(',',''))
        metas = extract_metas(response)
        yield {
            'url': response.url,
            'type':'group',
            'name': metas['og:title'],
            'description': response.css('#groupDesc')[0].extract(),
            'number_of_members': nb_of_members,
            'location': extract_location(metas)
        }
        #for url in response.css('.event-item h3 a::attr("href")'):
        #    yield scrapy.Request(url.extract(), self.parse_event)
        for url in response.css('.nearby-description a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse)
        #scrapy.Request(response.url+'members/', self.parse_members_list)

    def parse_event(self, response):
        metas = extract_metas(response)
        yield {
            'meetup_title': title(response),
            'location': extract_location(metas)
        }

    def parse_members_list(self, response):
        for url in response.css('.memName::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse_member)

    def parse_member(self, response):
        yield {'member_title': title(response)}
        for url in response.css('.groupinfo-widget-root.paddedList li .D_name a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse)
