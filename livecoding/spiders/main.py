# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
import json

def doc_title(response):
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
        for url in response.css('.event-item h3 a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse_event)
        for url in response.css('.nearby-description a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse)
        yield scrapy.Request(response.url+'events/past/?page=0&__fragment=centerColMeetupList',
                callback=lambda r:self.parse_past_events(r, 0))
        #scrapy.Request(response.url+'members/', self.parse_members_list)

    def parse_event(self, response):
        metas = extract_metas(response)
        start = response.css('time::attr("datetime")')
        if len(start) > 0:
            start = start.extract()[0]
        else:
            start = None
        title = response.css('#event-title h1::text').extract()[0]
        description = response.css('#event-description-wrap')
        if len(description) == 0:
            description = response.css('#past-event-description-wrap')
        description = description.extract()[0]
        attendees = list({x for x in \
                response.css('.event-attendees a::attr("href")').extract()})
        yield {
            'url': response.url,
            'type':'event',
            'title': title,
            'location': extract_location(metas),
            'start_time': start,
            'description': description,
            'attendees': attendees
        }
        for url in attendees:
            yield scrapy.Request(url, self.parse_member)

    def parse_past_events(self, response, i):
        try:
            body = json.loads(response.body_as_unicode())[0]
        except:
            return
        links = Selector(text=body).css('a::attr("href")').extract()
        for url in links:
            if '/members/' in url:
                yield scrapy.Request(url, self.parse_member)
            elif '/events/' in url and not '/past/' in url:
                yield scrapy.Request(url, self.parse_event)
        if len(links) > 0:
            yield scrapy.Request(response.url+'events/past/?page={}&__fragment=centerColMeetupList'.format(i),
                    callback=lambda r:self.parse_past_events(r, i+1))

    def parse_members_list(self, response):
        for url in response.css('.memName::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse_member)

    def parse_member(self, response):
        yield {
            'url': response.url,
            'type': 'member',
            'name': response.css('.memName::text').extract()[0]
        }
        for url in response.css('.D_memberProfileGroups .D_name a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse)