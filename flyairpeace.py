import json,time,datetime,lxml
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import threading,queue
from selenium.webdriver.common.by import By

login_url = 'https://booking.flyairpeace.com/VARS/Public/CustomerPanels/requirementsBS.aspx?country=ng&currency=USD'
my_queue =queue.Queue()


def selectDateInDatepicker(driver,dates):
    # this Function takes two argument driver and date which we want to select on datepicker
    get_the_year_and_month=True
    get_the_date=False
    validatedate = datetime.datetime(int(dates.split("/")[2]),int(dates.split("/")[1]),int(dates.split("/")[0])).strftime("%B")+dates.split("/")[2]
    
    while get_the_year_and_month:
        month=driver.find_element_by_class_name('ui-datepicker-month')
        year=driver.find_element_by_class_name('ui-datepicker-year')
        if validatedate == month.text+year.text:
            break
        driver.find_element_by_class_name('ui-datepicker-next').click()
    
    table_id = driver.find_element_by_class_name('ui-datepicker-calendar')# get calendar table
    rows = table_id.find_elements_by_tag_name("tr")# get all of the rows in the table
    for row in rows:
        col = row.find_elements_by_tag_name("td")#note: index start from 0, 1 is col 2
        for i in col:
            if i.text == dates.split("/")[0]:
                i.click()
                get_the_date=True
                break
        if get_the_date:
            break
                    
        

def getFlightDetails(i):
    __={}
    __['departureTime']=i[0].find('span',class_="time").get_text()
    __['departureDate']=i[0].find('span',class_="flightDate").get_text()
    __['departure']=i[0].find('div',class_='col-lg-10').get_text().replace('\n', '').replace(__['departureTime'],"").replace(__['departureDate'],"")
    __['duration']=i[1].get_text().split("m")[0].replace("\n","")+"m"
    __['flightNumber']=i[1].get_text().replace(__['duration'],"").replace("\n","").replace("Non-stop","")
    __['arrivalTime']=i[2].find('span',class_="time").get_text()
    __['arrivalDate']=i[2].find('span',class_="flightDate").get_text()
    __['arrival']=i[2].find('div',class_='col-lg-10').get_text().replace('\n', '').replace(__['arrivalTime'],"").replace(__['departureDate'],"")
    __['price']=i[3].get_text().replace('\n',"").replace("from","").replace("$","")
    __['currency']="USD"
    return __



def main(requdata):
    try:
        # local variables
        departurdate=requdata['departurdate']
        returningdate=requdata['returningdate']
        twoway=requdata['twoway']
        scrapdatalist=[]
        # Connect to cromme driver 
        driver = webdriver.Chrome('./chromedriver')
        driver.get(login_url) #coonnect to url 
        # select the origin airport
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "Origin")))
        el = driver.find_element_by_name('Origin')
        for option in el.find_elements_by_tag_name('option'):
            if option.get_attribute('value') == requdata['departure']:
                option.click() 
        time.sleep(2)
        # select the Destination airport
        el = driver.find_element_by_name('Destination')
        for option in el.find_elements_by_tag_name('option'):
            if option.get_attribute('value') == requdata['arrival']:
                option.click() 
        time.sleep(2)
        # Selecting Return or One Way
        if twoway is False:
            driver.find_element_by_xpath('//*[@id="divRequirementsPanel"]/div/div[1]/div[2]/div/div/div/div/label[2]/i').click()
        # selecting the departure date from detepicker
        datepicker = driver.find_element_by_id("departuredate")
        datepicker.click()
        selectDateInDatepicker(driver,requdata['departurdate'])
        # if junmeny is two way then selecting the returningdate date from detepicker
        if twoway is True:
            datepicker = driver.find_element_by_id("returndate")
            datepicker.click()
            selectDateInDatepicker(driver,requdata['returningdate']) 
        # Click submit button
        driver.find_element_by_id("submitButton").click()
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.ID, "Content_middelResult")))
        soup = BeautifulSoup(driver.page_source, 'lxml')
        divdata = soup.find_all('div', class_="flt-panel-heading")

        for i in divdata:
            requiredata=getFlightDetails(i.find_all('div',class_='col-xs-4'))
            scrapdatalist.append(requiredata)
        driver.close()
        return scrapdatalist
    except Exception as e:
        print("errro",e)
        return str(e)





if __name__ == '__main__':
    t1=time.time()
    requdata=[{
        "departure":"ABV",
        "arrival":"ABB",
        "twoway":True,
        "departurdate":"19/12/2020",
        "returningdate":"29/12/2020"
    },{
        "departure":"ABB",
        "arrival":"ABV",
        "twoway":True,
        "departurdate":"19/1/2021",
        "returningdate":"29/1/2021"
    }]
    finalresul={}
    for i in requdata:
        finalresul[i["departurdate"]+"-"+i["returningdate"]+"-"+i["departure"]+"-"+i["arrival"]]=main(i)
    print(json.dumps(finalresul),time.time()-t1)

