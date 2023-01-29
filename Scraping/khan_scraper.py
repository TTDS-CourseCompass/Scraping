import requests
import PyPDF2
from bs4 import BeautifulSoup
from io import BytesIO
import xml.etree.cElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import math
import json
import slimit
#from lecture import Lecture, Slide


""" XML Format 

doc = ET.Element("doc")
ET.SubElement(doc, "lectureno")
ET.SubElement(doc, "course")
ET.SubElement(doc, "date")
ET.SubElement(doc, "headline")
ET.SubElement(doc, "url")

slides = ET.SubElement(doc, "slides")
slide = ET.SubElement(slides, "slide")
ET.SubElement(slide, "slideno")
ET.SubElement(slide, "text")

ET.SubElement(doc, "source")

tree = ET.ElementTree(doc)
tree.write("index_format.xml")

"""

class Scraper:
    SCROLL_PAUSE_TIME = 0.8
    COURSES_ON_ONE_SCROLL = 10  # The MIT website displays 10 more pages every time you scroll

    def __init__(self, num_courses):
        # Initialise variables
        self.doc_list = []
        self.base_url = 'https://www.khanacademy.org/computing/computer-programming'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(chrome_options=self.options, executable_path='\chromedriver_win32\chromedriver.exe')
        self.driver.get(self.base_url)
        # Call methods
        self.scroll_scrape(num_courses)

    def scroll_scrape(self, num_courses):
        """ Scroll to the bottom of the page to load a specific number of courses to scrape
        Args:
            - num_courses: The number of courses to load
        """
        # Get scroll height
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")

        for scroll_num in range(math.ceil(num_courses / self.COURSES_ON_ONE_SCROLL) - 1):
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

            # Wait to load page
            time.sleep(self.SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        self.parse_khan_page()

    def get_text_from_article(self, article_link):
            response = requests.get(article_link)
            soup = BeautifulSoup(response.text, 'lxml')
            content = 'no content!'
            #print(str(soup.find_all('div')))
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                if '__PAGE_SETTINGS__' in script.string[:100]:
                    content = script.string[:20].strip()
                    
            return content # currently giving just raw javascript
                                        # so we can handle a string output
                                        # ultimately, this method should unpack the JS in 
                                        # content and return that
                    

    

    def get_lesson_articles(self, url, unit_title):
        """Retrieves all lessons and then all activities in that lesson
        that are articles. will potentialy update to also retrieve videos

        Args:
            url (): url
            unit_title (string): unit_title
            doc (_type_): ElementTree root
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        lesson_no = 0
        for lesson_card in soup.find_all('div', {'data-test-id':'lesson-card'}):
            lesson_no += 1
            lesson_card_title = lesson_card.find('a', {'data-test-id':'lesson-card-link'}).text
            lesson_link = lesson_card.find('a', {'data-test-id':'lesson-card-link'})['href']
            print('\t' + str(lesson_card_title))
            contents = lesson_card.find('div', {'class':'_1g8ypdt'})
            activity_no = 0
            
            doc = ET.Element('doc')
            self.doc_list.append(doc)
            slides = ET.SubElement(doc, 'slides')
            ET.SubElement(doc, 'course').text = unit_title
            ET.SubElement(doc, 'headline').text = lesson_card_title
            ET.SubElement(doc, 'url').text = self.base_url + lesson_link
            ET.SubElement(doc, 'date').text  = 'None'
            ET.SubElement(doc, 'lectureno').text = str(lesson_no)
            ET.SubElement(doc, 'source').text = 'Khan Academy'
            
            
            for activity in contents.find_all('div', {'class' : '_u7elqji'}):
                
                activity_type = activity.find('span', {'aria-label':'Article'}) # might be useful in future to consider 
                                                                                # aria-label:Talk-Through
                if activity_type:
                    activity_no += 1
                    activity_title = activity.find('span', {'class':'_14hvi6g8'}).text
                    print('\t\t' + str(activity_title))
                    article_link = self.base_url + activity.find('a')['href']
                    print('\t\t' + str(article_link)[:30])
                    
                    slide = ET.SubElement(slides, 'slide')
                    ET.SubElement(slide, 'slideno').text = str(activity_no)
                    ET.SubElement(slide, 'text').text = self.get_text_from_article(article_link)
                    
                                
                
   


    def parse_khan_page(self):
        page = self.driver.page_source
        self.driver.quit()
        soup = BeautifulSoup(page, 'lxml')
        #print(str(soup)[:1000])
        #for link in soup.find_all('a', {'data-test-id':'lesson-link'}):
            #print(str(link['href']))


        for unit_card in soup.find_all('div', {'data-slug':'table-of-contents'}):
            unit_header = unit_card.find('a', {'data-test-id':'unit-header'})
            unit_title = unit_header.find('h3').text
            unit_link = unit_header['href']

            print('\n')          
            print(unit_title)
            print(unit_link)
            print('=============================')
            
           

            self.get_lesson_articles(self.base_url + unit_link, unit_title)
            
            
            docno = 0
            for doc in self.doc_list:
                docno += 1
                tree = ET.ElementTree(doc)
                with open('khan_lec_{}.xml'.format(str(docno)), 'wb') as f:
                    tree.write(f)                
                
            


    def get_single_course_data(self, course_title, href, course_tags, level_info, prof_info):
        """ Scrape each individual course information
        """
        pass
        # TODO: Link to get_pdf_data etc..
        # source_code = requests.get(item_url)
        # soup = BeautifulSoup(source_code.text, 'html.parser')
        # # for item_description in soup.findAll('p'):
        # for item_description in soup.findAll('div', {'id': 'description'}):
        #     description = item_description.findAll('p')
        #     print(description[0].string)
    
    def get_pdf_data(self):
        """ Scrape textual information from PDF slides
        """
        url = "https://ocw.mit.edu/courses/6-s897-machine-learning-for-healthcare-spring-2019/resources/mit6_s897s19_lec1/"

        # Requests URL and get response object
        response = requests.get(url)
        # Parse text obtained
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all hyperlinks present on webpage
        links = soup.find_all('a')
        
        lec_num = 0
        # From all links check for pdf link and
        # if present download file
        for link in links:
            if ('.pdf' in link.get('href', [])):
                lec_num += 1
                print("Lectures Downloaded: {} ".format(lec_num))
        
                # Get response object for link
                try:
                    link_ref = link.get('href')
                    if link_ref[0] == '/':
                        link_ref = 'https://ocw.mit.edu{}'.format(link_ref)
                    response = requests.get(link_ref)
                except Exception as e:
                    print(e)
                    continue

                # Start building XML tree
                doc = ET.Element("doc")
                ET.SubElement(doc, "lectureno").text = str(lec_num)
                ET.SubElement(doc, "course").text = 'dummy'
                ET.SubElement(doc, "date").text = 'dummy'
                ET.SubElement(doc, "headline").text = 'dummy'
                ET.SubElement(doc, "url").text = link_ref
                slides = ET.SubElement(doc, "slides")
                
                # Get the contents of PDF as text
                raw_data = response.content
                with BytesIO(raw_data) as data:
                    read_pdf = PyPDF2.PdfReader(data)

                    slide = ET.SubElement(slides, "slide")
                    for page in range(len(read_pdf.pages)):
                        # Add slide info to XML tree
                        ET.SubElement(slide, "slideno").text = str(page)
                        ET.SubElement(slide, "text").text = read_pdf.pages[page].extract_text()
                
                ET.SubElement(doc, "source").text = 'dummy'
                tree = ET.ElementTree(doc)
                tree.write("lec_{}.xml".format(lec_num), encoding="utf-8")
        
        print("All PDF files text extracted")


if __name__ == '__main__':
    scraper = Scraper(30)