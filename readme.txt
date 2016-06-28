1. Install python scrapy 1.1.0

Please see http://doc.scrapy.org/en/latest/intro/install.html

2. Run the program

- In Ganz, run the following command

scrapy crawl ganz

3. Result

After executing the program, you can see data.csv, data_unformatted.csv and log.txt file in Ganz directory.

- data.csv has data of products. After completing the program, the program starts to write the result in the file.
- log.txt has errors during scraping data and number of products for each category.
- data_unformatted.csv has data of products. The program writes the result, when scraping data of each product.