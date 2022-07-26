import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os
from os import path
import shutil
from sklearn.manifold import trustworthiness
import tabula
import glob
import pikepdf
from selenium.webdriver.support.select import Select
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import io
import re


class Gem():

    """ sorting the file according to the time its being made and returing the 
    latest downloaded file in the directory

    find the latest files which start with the name GEM in the source downoad 
    folder and move it to the destination folder where the data extraation and downloaidng
    the link happens . Please the source , destination , key word of the
     file starting to take the action

     function to get the selenium edge driver

     eturns the list of files with any extension from a folder


     """

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        

    def latestDownload(self):

        path = self.src
        os.chdir(path)
        files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
        newest = files[-1]
        return newest

    def move_file(self, keyword="GEM"):

        files = [i for i in os.listdir(self.src) if i.startswith(
            keyword) and path.isfile(path.join(self.src, i))]
        for f in files:
            shutil.move(os.path.join(self.src, f), os.path.join(self.dst, f))
        return files

    def get_driver(self):

        ser = Service(executable_path='C:\\edgedriver_win64\\msedgedriver.exe')
        driver = webdriver.Edge(service=ser)
        driver.maximize_window()
        return driver

    def itemwise_download(self,url,items):

        driver = self.get_driver()
        driver.get(url)
        driver.find_element(By.XPATH, '//*[@id="search_concept"]').click()
        time.sleep(1)
        driver.find_element(
            By.XPATH, '//*[@id="exTab2"]/div[1]/div[2]/form/div/div/ul/li[2]/a').click()
        time.sleep(1)

        for item in items:
            Searchbox = driver.find_element(By.XPATH, ('//*[@id="search_by"]'))
            Searchbox.clear()
            Searchbox.send_keys(item)
            driver.find_element(
                By.XPATH, '//*[@id="exTab2"]/div[1]/div[2]/form/div/span/button/span').click()

            linklist = []
            
            for j in range(1, 10):
                try:
                    # Extracting the text from the link element

                    link = driver.find_element(
                        By.XPATH, f'//*[@id="pagi_content"]/div[{j}]/div[1]/p[1]/a').text
                    if(link):
                        linklist.append(link)
                    else:
                        break

                except Exception as e:
                    print("error", str(e))
                    pass

            if (len(linklist)) > 0:

                for k in range(1, len(linklist)+1):

                    # Extracting the text from the link element
                    link = driver.find_element(
                        By.XPATH, f'//*[@id="pagi_content"]/div[{k}]/div[1]/p[1]/a').text
                    link = link.replace("/", "")
                    link = f'{link}.pdf'
                    # click on the link and download the file to destination.
                    driver.find_element(
                        By.XPATH, f'//*[@id="pagi_content"]/div[{k}]/div[1]/p[1]/a').click()

                    time.sleep(2)
                    # identifying the latest downloaded file in source directory
                    file = self.latestDownload()

                    if file.startswith("GeM") and path.isfile(path.join(self.src, file)):
                        os.rename(file, link)
                        self.move_file()

            else:
                continue

            time.sleep(2)

        return link

    def pdf_list(self, extension='pdf'):

        pdf_file_list = glob.glob(f'{self.dst}/*.{extension}')
        return pdf_file_list

    def extract_text_by_page(self, pdf_file_list):
        with open(pdf_file_list, 'rb') as fh:
            for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                resource_manager = PDFResourceManager()
                fake_file_handle = io.StringIO()
                converter = TextConverter(resource_manager, fake_file_handle)
                page_interpreter = PDFPageInterpreter(
                    resource_manager, converter)
                page_interpreter.process_page(page)

                text = fake_file_handle.getvalue()
                yield text

            # close open handles
            converter.close()
            fake_file_handle.close()

    def extract_text(self, pdffile):
        tot = {}
        for i, page in enumerate(self.extract_text_by_page(pdffile)):
            tot.update({i+1: page})
        return tot

    def dataExtraction(self, pattern, pdftext):
        """using regex extarcting data from the pdf file """

        pattern_data = re.findall(pattern, pdftext)
        try:
            pattern_data = pattern_data[0]
        except Exception as e:
            pattern_data = "NA"
            print("error", str(e))
            pass
        return pattern_data

    def data_to_csv(self, pdf_file_list):

        for a in pdf_file_list:

            tender_no = a.split('\\')[1].replace('.pdf', '')
            df = tabula.read_pdf(a, pages="1", stream=True)
            pdftext = str(self.extract_text(a))

            date_pattern = 'Dated: (\d{2}-\d{2}-\d{4})'
            tender_date = self.dataExtraction(date_pattern, pdftext)

            place_pattern = 'AddressQuantityDelivery Days1(.*?)Buyer'
            place = self.dataExtraction(place_pattern, pdftext)

            Emd_pattern = 'DocumentEMD DetailRequired([a-zA-Z]*)'
            Emd = self.dataExtraction(Emd_pattern, pdftext)

            # ePBG_pattern = 'ePBG DetailRequired([a-zA-Z]*)'
            # ePBG = self.dataExtraction(ePBG_pattern, pdftext)

            # place1_pattern = 'Delivery Days1\**([\w][\D]*)'
            # place1 = self.dataExtraction(place1_pattern, pdftext)

            try:
                mseindex = df[0][df[0]['Unnamed: 0'].str.contains(
                    'MSE', regex=False, case=False, na=False)].index.tolist()
                msevalue = df[0]['Bid Details'][mseindex[0]+1]
            except Exception as e:
                msevalue = 'No'
                print("error", str(e))
                pass
            new_df = [[
                tender_no, tender_date, place,Emd,
                df[0]['Bid Details'][0],  # Bid End
                # df[0]['Bid Details'][1],  # Bid Open
                # df[0]['Bid Details'][4],  # Ministry Name
                df[0]['Bid Details'][5],  # Department Name
                # df[0]['Bid Details'][6],  # Oranization name
                df[0]['Bid Details'][7], # Total Qunatity
                df[0]['Bid Details'][8],  # Item Category
                # df[0]['Bid Details'][9],  # Item Category
                msevalue

            ]]
            columns = ['tender_no', 'Date', 'place_of_supply',
                       'Emd', 'Bid End Date/Time',
                       'Department Name','Total Qunatity',
                       'Item Category','MSE Exemption']

            new_df = pd.DataFrame(new_df, columns=columns)

            if os.path.isfile("D:\\Gem2\\gem1.csv"):
                new_df.to_csv("D:\\Gem2\\gem1.csv", index=False,
                              header=False, mode='a')
            else:
                new_df.to_csv("D:\\Gem2\\gem1.csv", index=False)
        return new_df

    def tenderNum(self, file):
        tender_no = file.split('\\')[1].replace('.pdf', '')
        return tender_no

    def tenderFolder(self, file):
        tender_no = self.tenderNum(file)
        directory = tender_no
        folder_location = os.path.join(self.dst, directory)
        if not os.path.exists(folder_location):
            os.mkdir(folder_location)
        yield folder_location

    def link_download(self,pdf_file_list):
        urls = []        
        for file in pdf_file_list:
            tender_no =self.tenderNum(file)
            folder_location=next(self.tenderFolder(file))
            pdf_file = pikepdf.Pdf.open(file)
            for page in pdf_file.pages:
                for annots in page.get("/Annots"):
                    try:
                        uri = annots.get("/A").get("/URI")
                        urls.append(str(uri))
                        uri=str(uri)
                    except Exception as e:
                        print("error", str(e))
                        pass
                    if uri is not None:
                        #print("[+] URL founs",uri)
                        # print(str(uri))
                        # do not download the file with terms and conditions
                        if uri.endswith("termsCondition"):
                            pass
                        else:
                            # Download the CSV, PDF, WOrd or excel file
                            if uri.endswith(".pdf") or uri.endswith(".csv") or uri.endswith(".docx") or uri.endswith(".xlsx"):
                                filename = os.path.join(
                                    folder_location, uri.split("/")[-1])
                                # with requests.get(uri, stream=True) as r:
                                #     r.raise_for_status()                                
                                #     print("Saving to", filename)
                                #     with open(filename, 'wb') as f:
                                #         for chunk in r.iter_content(chunk_size=1024): 
                                #             # If you have chunk encoded response uncomment if
                                #             # and set chunk_size parameter to None.
                                #             #if chunk: 
                                #             f.write(chunk)   
                                # 
                                with requests.get(uri, stream=True) as r:
                                    print("Saving to", filename)
                                    with open(filename, 'wb') as f:
                                            shutil.copyfileobj(r.raw, f)                                        

                            else:
                                try:
                                    # Download the table directly from website
                                    html = requests.get(uri)
                                    soup = BeautifulSoup(html.text, 'lxml')
                                    tables = soup.find_all('table')
                                    df = pd.read_html(str(tables[0]))[0]
                                    folder = f'D:\\Gem\\{tender_no}\\'
                                    df.to_csv(f"{folder}\\{tender_no}.csv")
                                except Exception as e:
                                    print("error", str(e))
                                    pass

            pdf_file.close()
        return urls

    def move_pdf_file(self,pdf_file_list):
        for file in pdf_file_list:
            source = file
            tender_no = file.split('\\')[1].replace('.pdf', '')
            # Destination path
            destination = f"D:\\Gem2\\{tender_no}"
            # Move the content of
            # source to destination
            dest = shutil.move(source, destination)
            # print(dest) prints the
            # Destination of moved directory
        return (print("files moved"))

