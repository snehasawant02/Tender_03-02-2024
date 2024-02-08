import os
import time
from urllib.parse import urljoin
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import re
import fitz  # PyMuPDF
from urllib.parse import urlparse
pdf_folder = 'pdf_folder'
os.makedirs(pdf_folder, exist_ok=True)
url = "https://bidplus.gem.gov.in/all-bids"
chrome_options = Options()
chrome_options.add_argument('--headless')

with webdriver.Chrome(options=chrome_options) as driver:
    wait = WebDriverWait(driver, 10)
    driver.get(url)
    time.sleep(10)

    keywords1 = 'Data Entry'
    Keywords = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='searchBid']"))
    )
    Keywords.send_keys(keywords1)

    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='searchBidRA']"))
    )
    search_button.click()
    time.sleep(5)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    href_tags = soup.find_all('a', href=True)
    base_url = "https://bidplus.gem.gov.in"

for tag in href_tags:
    href = tag['href']
    if href.startswith('showbidDocument/') or href.startswith('/showradocumentPdf/') or href.startswith('/showbidDocument/'):
        full_url = urljoin(base_url, href)
        # Create a folder for each PDF
        pdf_folder_path = os.path.join(pdf_folder, f"pdf_{href.split('/')[-1]}")
        os.makedirs(pdf_folder_path, exist_ok=True)
        print(f"Downloading PDF from: {full_url}")
        pdf_file_path = os.path.join(pdf_folder_path, f"{href.split('/')[-1]}.pdf")
        with open(pdf_file_path, 'wb') as pdf_file:
            pdf_file.write(requests.get(full_url).content)

        def extract_links(pdf_url, search_terms):
            try:
                response = requests.get(pdf_url)
                file_name = urlparse(pdf_url).path.split('/')[-1]
                with open(file_name, 'wb') as file:
                    file.write(response.content)
                print(f"Downloaded: {file_name}")
                process_downloaded_pdf(file_name, search_terms)
            except Exception as e:
                print(f"Failed to download {pdf_url}: {str(e)}")

        def process_downloaded_pdf(pdf_path, search_terms):
            doc = fitz.open(pdf_path)

            for page_number in range(doc.page_count):
                page = doc[page_number]
                text = page.get_text("text").lower()

                # Check if any of the search terms are present on the page
                if any(term.lower() in text for term in search_terms):
                    extract_and_download(page, search_terms, pdf_folder_path)

            doc.close()

        def extract_and_download(page, search_terms, target_folder):
            links = page.get_links()

            # Extract the text around the search terms
            for term in search_terms:
                term_lower = term.lower()
                index = page.get_text("text").lower().find(term_lower)

                if index != -1:
                    start = max(0, index - 1)  # Adjust the number of characters to extract before the search term
                    end = min(len(page.get_text("text")),
                              index + len(term_lower) + 50)  # Adjust the number of characters to extract after the search term
                    extracted_text = page.get_text("text")[start:end]
                    pdf_number_match = re.search(r'\d+\.pdf', extracted_text)
                    if pdf_number_match:
                        pdf_number = pdf_number_match.group(0)
                        print("PDF Number:", pdf_number)

                        # Download the extracted text
                        links = page.get_links()
                        for link in links:
                            url = link.get('uri')
                            if pdf_number in url:
                                print("Matching URL:", url)
                                download_file(url)




        '''def download_file(url, target_folder):
            try:
                # Check if content is a valid URL
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad responses (e.g., 404)

                # Generate a unique file name based on the current timestamp
                file_name = os.path.join(target_folder, f"{time.time()}_extracted_document.pdf")

                # Save the content as a PDF file
                with open(file_name, 'wb') as file:
                    file.write(response.url)

                print(f"Downloaded: {file_name}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {url}: {str(e)}")'''


        def download_file(url):
            try:
                response = requests.get(url)
                file_name = urlparse(url).path.split('/')[-1]
                pdf_file_path = os.path.join(pdf_folder_path, f"{file_name}")
                with open(pdf_file_path, 'wb') as file:
                    file.write(response.content)
                    file.write(response.url.encode())  # Write the URL as bytes
                print(f"Downloaded: {pdf_file_path}")
            except Exception as e:
                print(f"Failed to download {url}: {str(e)}")



        search_terms = ["Minimum Wages Act", "Scope of work"]

        # Process each PDF URL
        process_downloaded_pdf(pdf_file_path, search_terms)