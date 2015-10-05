# -*- coding: utf-8 -*-
import scrapy

def title(response):
	return response.selector.xpath('//title/text()').extract()[0] \
		.replace('- Meetup','').strip()

class MeetupSpider(scrapy.Spider):
    name = 'meetup'
    allowed_domains = ["meetup.com"]
    start_urls = ['http://www.meetup.com/hackerhours/']

    def parse(self, response):
        yield {'group_name': title(response)}
        for url in response.css('.event-item h3 a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse_event)
        for url in response.css('.nearby-description a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse)
        scrapy.Request(response.url+'members/', self.parse_members_list)

    def parse_event(self, response):
        yield {'meetup_title': title(response)}

    def parse_members_list(self, response):
        for url in response.css('.memName::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse_member)

    def parse_member(self, response):
    	yield {'member_title': title(response)}
        for url in response.css('.groupinfo-widget-root.paddedList li .D_name a::attr("href")'):
            yield scrapy.Request(url.extract(), self.parse)
