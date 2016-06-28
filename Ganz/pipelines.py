# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class GanzPipeline(object):
		def __init__(self):
				self.file = None
				self.total = 0

				self.unform_file = open("data_unformatted.csv", 'wb')
				self.unform_file.write('"type","group","category","name","price","available","catelog","SKU","UPC"\n')
				
		def close_spider(self, spider):
				self.file = open("data.csv", 'wb')
				self.file.write('"type","group","category","name","price","available","catelog","SKU","UPC"\n')

				for pt_type in spider.product_list:
						for pt_group in spider.product_list[pt_type]:
								for pt_category in spider.product_list[pt_type][pt_group]:
										for item in spider.product_list[pt_type][pt_group][pt_category]:
												item['product_name'] = item["product_name"].replace("\"", " ")
												item['product_name'] = item["product_name"].replace(",", " ")
												line = '"%s","%s","%s","%s","%s","%s","%s","%s","\'%s\'"\n' % (item['type_name'], item['group_name'], item['category_name'], item['product_name'], item['price'], item['available'], item['catalog'], item['sku'], str(item['upc']))
												self.file.write(line)

				self.file.close()

		def process_item(self, item, spider):
				line = '"%s","%s","%s","%s","%s","%s","%s","%s","\'%s\'"\n' % (self.removeCharacter(item['type_name']), self.removeCharacter(item['group_name']), self.removeCharacter(item['category_name']), self.removeCharacter(item['product_name']), item['price'], self.removeCharacter(item['available']), self.removeCharacter(item['catalog']), item['sku'], str(item['upc']))
				line = line.encode("utf8")
				print line
				self.unform_file.write(line)				

				self.total += 1
				return item

		def removeCharacter(self, str_t):
				str_t = str_t.replace("\"", " ")
				str_t = str_t.replace(",", " ")

				return str_t
