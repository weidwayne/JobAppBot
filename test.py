from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait


import time # to sleep# to sleep
# to find links
from bs4 import BeautifulSoup
import json
import urllib.request
import re
# from scrape import *


USERNAME = ''
PASSWORD = ''
PREFERENCES = {
    "position_title": "Software Engineer",
    "location": "San Francisco"
}

# helper method to give user time to log into glassdoor
def login(driver):
    driver.get('https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r2592000&start=0')
    WebDriverWait(driver,20).until(
        EC.element_to_be_clickable((By.LINK_TEXT,"Sign in"))
    )
    sign_in_button = driver.find_element_by_link_text("Sign in")
    sign_in_button.click()
    email_field = driver.find_element_by_id("username")
    email_field.send_keys(USERNAME)
    password_field = driver.find_element_by_id('password')
    password_field.send_keys(PASSWORD + Keys.ENTER)
    # keep waiting for user to log-in until the URL changes to user page
    # while True:
    #     try:
    #         WebDriverWait(driver, 1).until(EC.url_contains("r2592000"))
    #     except TimeoutException:
    #         break
    return True # return once this is complete


def go_to_listings(driver):
    job_search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav-search"))
            )

    try:
        # look for search bar fields
        position_field = driver.find_element_by_xpath("//*[@aria-label='Search by title, skill, or company']")
        location_field = driver.find_element_by_xpath("//*[@aria-label='City, state, or zip code']")

        # fill in with pre-defined data
        position_field.send_keys(PREFERENCES['position_title'])
        location_field.clear()
        location_field.send_keys(PREFERENCES['location']+Keys.ENTER)

        # wait for a little so location gets set
        # time.sleep(1)
        # location_field.send_keys(Keys.ENTER)

        # close a random popup if it shows up
        try:
            driver.find_element_by_xpath("//*[@id='JAModal']/div/div[2]/span").click()
        except NoSuchElementException:
            pass
        return True

    except NoSuchElementException:
        return False


# aggregate all url links in a set
def aggregate_links(driver):
    allLinks = [] # all hrefs that exist on the page

    # wait for page to fully load
    left_rail = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                # (By.CLASS_NAME, "jobs-search__left-rail"))
                (By.CSS_SELECTOR, ".job-card-container--clickable"))
        )

    # time.sleep(5)

    # parse the page source using beautiful soup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source,"html.parser")

    # find all hrefs
    allJobLinks = soup.findAll("a", {"class": "currentJobId"})
    allLinks = [jobLink['href'] for jobLink in allJobLinks]
    allFixedLinks = []

    # clean up the job links by opening, modifying, and 'unraveling' the URL
    for link in allLinks:
        # first, replace GD_JOB_AD with GD_JOB_VIEW
        # this will replace the Glassdoor hosted job page to the proper job page
        # hosted on most likely Greenhouse or Lever
        link = link.replace("GD_JOB_AD", "GD_JOB_VIEW")

        # if there is no glassdoor prefex, add that
        # for example, /partner/jobListing.htm?pos=121... needs the prefix

        if link[0] == '/':
            link = f"https://www.glassdoor.com{link}"

        # then, open up each url and save the result url
        # because we got a 403 error when opening this normally, we have to establish the user agent
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers={'User-Agent':user_agent,}
        request=urllib.request.Request(link,None,headers) #The assembled request

        try:
            # the url is on glassdoor itself, but once it's opened, it redirects - so let's store that
            response = urllib.request.urlopen(request)
            newLink = response.geturl()

            # if the result url is from glassdoor, it's an 'easy apply' one and worth not saving
            # however, this logic can be changed if you want to keep those
            if "glassdoor" not in newLink:
                print(newLink)
                print('\n')
                allFixedLinks.append(newLink)
        except Exception:
            # horrible way to catch errors but this doesnt happen regualrly (just 302 HTTP error)
            print(f'ERROR: failed for {link}')
            print('\n')

    # convert to a set to eliminate duplicates
    return set(allFixedLinks)


def easyApply(driver,listing):
    time.sleep(2)
    listing.click()
    time.sleep(1)
    # do a keyword check            
    keyword_is_matched = True
    try:
        apply_button = driver.find_element_by_css_selector('.jobs-s-apply button')
        if apply_button.text == 'Easy Apply' and keyword_is_matched:
            apply_button.click()
            next_button = driver.find_element_by_css_selector('footer button')
            if next_button.get_attribute("data-control-name")=="continue_unify":
                next_button.click()
            else:
                follow_company_checkbox = driver.find_element_by_id("follow-company-checkbox")
                submit_button = driver.find_element_by_class_name("artdeco-button--primary")
                submit_button.click()
                driver.find_element_by_class_name("artdeco-modal__dismiss").click()
                # close_button = driver.find_element_by_class_name("artdeco-modal__dismiss")
                # close_button.click()
                # time.sleep(1)
                # discard_button = driver.find_element_by_xpath("//button[contains(@class,'artdeco-button')]//*[contains(.,'Discard')]/..")
                # discard_button.click()
                # print("Complex application, skipped...")
                
            time.sleep(1)
            review_button = driver.find_element_by_class_name("artdeco-button--primary")
            if review_button.get_attribute("data-control-name")=="continue_unify":
                driver.find_element_by_class_name("artdeco-modal__dismiss").click()
                time.sleep(1)
                discard_button = driver.find_element_by_xpath("//button[contains(@class,'artdeco-button')]//*[contains(.,'Discard')]/..")
                discard_button.click()
                print("Complex application, skipped...")
                
            else:
                review_button.click()
                time.sleep(1)
                submit_button = driver.find_element_by_class_name("artdeco-button--primary")
                if submit_button.get_attribute("data-control-name")=="submit_unify":
                    submit_button.click()
                    driver.find_element_by_class_name("artdeco-modal__dismiss").click()
                else:  
                    driver.find_element_by_class_name("artdeco-modal__dismiss").click()
                    time.sleep(1)
                    discard_button = driver.find_element_by_class_name("artdeco-modal__confirm-dialog-btn")[1]
                    discard_button.click()
                    print("Complex application, skipped...")
                    
    except NoSuchElementException:
        print("Complex application, skipped...")
        pass

    #     print('qualified')
    #     apply_button.click()


# 'main' method to iterate through all pages and aggregate URLs
def getURLs():
    # driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver')
    s = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=s)
    success = login(driver)
    if not success:
        # close the page if it gets stuck at some point - this logic can be improved
        driver.close()

    success = go_to_listings(driver)
    if not success:
        driver.close()

    allLinks = set()
    page = 1
    next_url = ''
    while page < 5: # pick an arbitrary number of pages so this doesn't run infinitely
        print(f'\nNEXT PAGE #: {page}\n')   

        # wait for page to fully load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                # (By.CLASS_NAME, "jobs-search__left-rail"))
                (By.CSS_SELECTOR, ".job-card-container--clickable"))
        )  
        this_page_url = driver.current_url
        # on the first page, the URL is unique and doesn't have a field for the page number
        if page == 1:
            
            all_listings = driver.find_elements_by_css_selector(".job-card-container--clickable")
            for listing in all_listings:
                # scrape all data
                # data = scrape_page(driver)    
                easyApply(driver,listing)
                
            # aggregate links on first page
            # extract information from the card (links, job title, company, location,third-party)
            # allLinks.update(aggregate_links(driver))
            # store the information to database 

            startPost = page*25
            page += 1
        #     # update URL
            next_url=f"{this_page_url}&start={startPost}"
            
            driver.get(next_url)
            time.sleep(1) # just to give things time

        # same patterns from page 2 onwards
        elif page >=2 :
            for listing in all_listings:
                # scrape all data
                # data = scrape_page(driver)    
                easyApply(driver,listing)
                
        #     # run regex to get all reusable parts of URL
            m = re.search('(?P<url>[^;]*?.start=)(?P<startPost>.*)', this_page_url)
        #     # increment page number for next time
            startPost = page*25
            page += 1
        #     # update URL
            next_url = f"{m.group('url')}{startPost}"
            driver.get(next_url)
            time.sleep(1) # just to give things time

    driver.close()
    return allLinks



# for testing purpose
getURLs()