import scrapy

import json
import re
from Ganz.items import ProductItem

from collections import OrderedDict

class GanzSpider(scrapy.Spider):
		name = "ganz"
		allowed_domains = ["shop.ganz.com"]

		username = "FrankLaMa"
		password = "contentgrabber"

		header = {	"Accept": "application/json, text/plain, */*",
								"Accept-Encoding": "gzip, deflate, sdch, br",
								"Accept-Language": "en-US,en;q=0.8", 
								"Connection": "keep-alive",
								"Host": "shop.ganz.com",
								"Cookie": "Cookie:JSESSIONID=9AF025EA668A26ABEC3DEA152F3016B5; GOPSESSIONID-%3FESTORE%3FSF_GOPAPP01_8084=IALEABAK; returningVisitor=true; returningMember=true; _ga=GA1.3.600542894.1466792143; _gat=1",
								"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}
	
		total_num = 0

		product_list = OrderedDict()

		handle_httpstatus_list = [553, 404, 400, 500]

		log_file = open("log.txt", 'wb')				

		def start_requests(self):
				token_header = self.header
				token_header["Referer"] = "https://shop.ganz.com/go/"

				return [scrapy.Request("https://shop.ganz.com/go/getToken", headers=token_header, callback=self.login)]

		# get token from the server and make request for login
		def login(self, response):
				token = response.body
				
				# make request for login
				login_header = self.header
				login_header["Content-Type"] = "application/json;charset=UTF-8"
				login_header["Referer"] = "https://shop.ganz.com/go/"
				login_header["Origin"] = "https://shop.ganz.com"
				
				payload = '{"username": "%s", "password": "%s", "token": "%s"}' % (self.username, self.password, token)

				request = scrapy.Request("https://shop.ganz.com/go/loginUser",
												headers=login_header, callback=self.main_page, method="POST", body=payload)
				yield request

		# request all data for product types, groups, categories.
		def main_page(self, response):
				request = scrapy.Request("https://shop.ganz.com/go/catalog/getTopNav?topNavs=all", callback=self.parse_categories)
				
				yield request

		def parse_categories(self, response):				
				data = json.loads(response.body)

				# make request header for getting product lists
				product_header = self.header
				product_header["Content-Type"] = "application/json;charset=UTF-8"
				product_header["Referer"] = "https://shop.ganz.com/go/"
				product_header["Origin"] = "https://shop.ganz.com"

				requests = []

				for shop_product in data['topNav']:

						# if shop products
						if shop_product['name'] == "SHOP PRODUCTS":
								# retrieve all product types
								for product_type in shop_product['categories']:
										# retrieve product groups
										for product_group in product_type['subMenuItems']:
												# retrieve product categories
												for product_category in product_group['subMenuItems']:
														type_name = product_type['name'].encode("utf8")
														group_name = product_group['name'].encode("utf8")
														category_name = product_category['name'].encode("utf8")

														#url = "https://shop.ganz.com/go/#/SHOP-PRODUCTS/%s/%s/%s?ts=%s&ptb2=&id=%d&country=US&p=1&ptb=&bbid=&bbname="\
														#					% (re.sub("[ ,.-/]+", '-', type_name), re.sub("[ ,.-/]+", '-', group_name),\
														#					re.sub("[ ,.-/]+", '-', category_name), ts, int(product_category['id']))

														ts = ""
														# if a category is "Top Sellers"
														if "isTopSeller" in product_category and product_category["isTopSeller"] == "true":
																ts = "True"

														requests.append([ts, product_category['id'], type_name, group_name, product_category['name'].encode("utf8")])
												
								for rq in requests:
										url = "https://shop.ganz.com/go/catalog/getProducts"
										payload = '{"categoryId": "%d", "showSubCategories": true, "showProducts": true, "pagination": {"pageNo": "1"}, "filters":null, "showProductsRecursively": false}' % (int(rq[1]))
										
										if rq[0] != "":
												url = "https://shop.ganz.com/go/catalog/getTopSellers"
												
										# make a request for getting product list
										request = scrapy.Request(url, callback=self.parse_products, body=payload, method="POST", headers=product_header)
										request.meta['type_name'] = rq[2]
										request.meta['group_name'] = rq[3]
										request.meta['total_num'] = 0
										request.meta['category_id'] = rq[1]
										request.meta['page'] = 1
										request.meta['category_name'] = rq[4]
										
										yield request
														
								break

				

		# get product information
		def parse_products(self, response):	
				if response.status in [553, 400, 404, 500]:
						# make a request for getting product list in the next page
						next_page = response.meta['page'] + 1
						payload = '{"categoryId": "%d", "showSubCategories": true, "showProducts": true, "pagination": {"pageNo": "%d"}, "filters":null, "showProductsRecursively": false}' % (int(response.meta['category_id']), next_page)

						product_header = self.header
						product_header["Content-Type"] = "application/json;charset=UTF-8"
						product_header["Referer"] = "https://shop.ganz.com/go/"
						product_header["Origin"] = "https://shop.ganz.com"

						request = scrapy.Request(response.url, callback=self.parse_products, body=payload, method="POST", headers=product_header, dont_filter=True)
						request.meta['type_name'] = response.meta['type_name']
						request.meta['group_name'] = response.meta['group_name']
						request.meta['total_num'] = response.meta['total_num']
						request.meta['category_id'] = response.meta['category_id']
						request.meta['page'] = response.meta['page'] + 1
						request.meta['category_name'] = response.meta['category_name']

						log = "Error: type(%s), group(%s), category(%s), page(%d): Skip page. %d error!\n" \
												% (response.meta['type_name'].encode("utf8"), response.meta['group_name'].encode("utf8"), \
													response.meta['category_name'].encode("utf8"), response.meta['page'], response.status)
						print log
						self.log_file.write(log)						

						yield request
				else:
				
						total_num = response.meta['total_num']

						data = json.loads(response.body)

						page_info = data['categoryParameters']['pagination']

						type_name = response.meta['type_name'].encode("utf8")
						group_name = response.meta['group_name'].encode("utf8")
						category_name = data['category']['name'].encode("utf8")

						if data['result']['result'] == u"FAILURE":
								log = "Total Number: type(%s), group(%s), category(%s), page(%d): %d\n" \
												% (type_name, group_name, category_name, page_info['pageNo'], total_num)
								print log
								self.log_file.write(log)
								return

						for product in data['products']:
								item = ProductItem()

								item['type_name'] = type_name
								item['group_name'] = group_name
								item['category_name'] = category_name

								if item['group_name'] == item['category_name']:
										item['category_name'] = "Top Sellers"
								item['product_name'] = product['title'].encode("utf8")
								item['price'] = str(product['price']).encode("utf8")
								if 'promoPrice' in product and product['promoPrice'] != None:
										item['price'] = str(product['promoPrice']).encode("utf8")

								item['available'] = product['availableDate'].encode("utf8")
								item['sku'] = product['uuid'].encode("utf8")
								item['upc'] = str(product['upc']).encode("utf8")
								item['catalog'] = "N/A"

								if len(product['catalogs']) > 0:
										item['catalog'] = product['catalogs'][0]['categoryName'].encode("utf8")
								if item['catalog'] == "N/A" and 'bonusBuyCategoryName' in product:
										item['catalog'] = product['bonusBuyCategoryName']

								if item['type_name'] not in self.product_list:
										self.product_list[item['type_name']] = OrderedDict()
								if item['group_name'] not in self.product_list[item['type_name']]:
										self.product_list[item['type_name']][item['group_name']] = OrderedDict()
								if item['category_name'] not in self.product_list[item['type_name']][item['group_name']]:
										self.product_list[item['type_name']][item['group_name']][item['category_name']] = []
												
								self.product_list[item['type_name']][item['group_name']][item['category_name']].append(item)

								yield item

								total_num += 1

						# make a request for getting product list in the next page
						next_page = page_info['pageNo'] + 1
						payload = '{"categoryId": "%d", "showSubCategories": true, "showProducts": true, "pagination": {"pageNo": "%d"}, "filters":null, "showProductsRecursively": false}' % (int(data['category']['id']), next_page)

						product_header = self.header
						product_header["Content-Type"] = "application/json;charset=UTF-8"
						product_header["Referer"] = "https://shop.ganz.com/go/"
						product_header["Origin"] = "https://shop.ganz.com"

						request = scrapy.Request(response.url, callback=self.parse_products, body=payload, method="POST", headers=product_header, dont_filter=True)
						request.meta['type_name'] = type_name
						request.meta['group_name'] = group_name
						request.meta['total_num'] = total_num
						request.meta['page'] = page_info['pageNo'] + 1
						request.meta['category_id'] = data['category']['id']
						request.meta['category_name'] = category_name
						
						print "Total Number: type(%s), group(%s), category(%s), page(%d)" \
												% (item['type_name'], item['group_name'], item['category_name'], page_info['pageNo'])
						yield request
						
								
