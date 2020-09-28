import json,time,datetime,lxml
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import threading,queue
from selenium.webdriver.common.by import By

login_url = 'https://www.emirates.com/ng/english/'
my_queue =queue.Queue()

def selectDateInDatepicker(driver,dates):
        month=driver.find_element_by_class_name('label-month')
        year=driver.find_element_by_class_name('label-year')
        validatedate = datetime.datetime(int(dates.split("/")[2]),int(dates.split("/")[1]),int(dates.split("/")[0])).strftime("%B")+dates.split("/")[2]
        table_id = driver.find_element_by_class_name('icon-arrow-right')
        for i in range(13):
            time.sleep(1)
            if validatedate == month.text+year.text:
                break
            table_id.click()
        table_id = driver.find_element_by_class_name('ek-datepicker__table')
        rows = table_id.find_elements_by_tag_name("tr")# get all of the rows in the table
        for row in rows:
            col = row.find_elements_by_tag_name("td")#note: index start from 0, 1 is col 2
            for i in col:
                if i.text == dates.split("/")[0]:
                    i.click()

def getFlightDetails(i):
    __={}
    __['departure']=i.find('div', class_='ts-fie__place').find('p').get_text().split("\n")[4]
    __['departureTime']=i.find('time', class_="ts-fie__departure").get_text().split("\n")[1]
    __['arrival']=i.find('div', class_='ts-fie__place ts-fie__right-side').find('p').get_text().split("\n")[5]
    __['arrivalTime']=i.find('time', class_="ts-fie__arrival").get_text().replace('\n', '')
    __['durationTime']=i.find('div',class_='ts-fie__infographic').find('time').get_text().replace('\n', '').replace("Duration","")
    return __

def getFlightPrice(i):
    __={}
    __['currency']=i.find('div', class_='ts-fbr-option--economy').find('div',class_='ts-fbr-option__container').find("p",class_="ts-fbr-option__currency").get_text().split(" ")[1].replace('\n', '')
    __['economyPrice']=float(i.find('div', class_='ts-fbr-option--economy').find('div',class_='ts-fbr-option__container').find("strong",class_="ts-fbr-option__price").get_text().replace('\n', '').replace(',', ''))
    try:
        __['businessPrice']=float(i.find('div', class_='ts-fbr-option--business').find('div',class_='ts-fbr-option__container').find("strong",class_="ts-fbr-option__price").get_text().replace('\n', '').replace(',', ''))
    except:
        __['businessPrice']="Not Available"
    try:
        __['firstPrice']=float(i.find('div', class_='ts-fbr-option--first').find('div',class_='ts-fbr-option__container').find("strong",class_="ts-fbr-option__price").get_text().replace('\n', '').replace(',', ''))
    except:
        __['firstPrice']="Not Available"
 
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
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "Departure airport")))
        # Enteringi the defarture and arrival loacation 
        elem=driver.find_element_by_name("Departure airport")
        elem.clear()
        elem.send_keys(requdata['departure'])
        elem=driver.find_element_by_name("Arrival airport")
        elem.clear()
        time.sleep(1)
        elem.send_keys(requdata['arrival'])
        driver.find_element_by_name("Departure airport").click()
        element=WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "textfield__date")))
        element.click()
        if twoway is False:
            driver.find_element_by_css_selector('label.one-way').click()
            datefordepure=[departurdate]
        else:
            datefordepure=[departurdate,returningdate]
        
        for date in datefordepure:
            selectDateInDatepicker(driver,date)
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="panel0"]/div[2]/div/div/section/div[4]/div[2]/div[3]/form/button')))
        element.click();
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "ctl00_c_pH_heading1")))
        soup = BeautifulSoup(driver.page_source, 'lxml')
        divdata = soup.find_all('div', class_='ts-fbr-flight-list-row')
        elm=driver.find_elements_by_class_name("ts-info")
        counter=0
        
        for i in divdata:
            filterdetails={}
            filterdetails['breakdownJourney']=[]
            filterdetails['waiting']=[]
            filterdetails['flightNumbers']=[]
            filterdetails.update(getFlightDetails(i))
            filterdetails.update(getFlightPrice(i))
            # elm[counter].click()
            if filterdetails['departure'].capitalize()==requdata['departure']:
                filterdetails['departurdate']=departurdate
            else:
                filterdetails['departurdate']=returningdate
            sectiondata=i.find_all('section', class_='ts-fip__modal__panel')
           
            for j in sectiondata:
                __breakdownjouny={}
                __breakdownjouny.update(getFlightDetails(j))
                __breakdownjouny['flightNumber']=j.find('p',class_='details status-detail').find('strong').get_text().replace('\n', '')
                __breakdownjouny['aircraftType']=j.find('p',class_='details aircraft-detail').find('strong').get_text().replace('\n', '')
                filterdetails['flightNumbers'].append(__breakdownjouny['flightNumber'])
                filterdetails['breakdownJourney'].append(__breakdownjouny)
            waitingdiv=sectiondata=i.find_all('div', class_='ts-fip__modal__connection')
            
            for j in sectiondata:
                filterdetails['waiting'].append(j.get_text().replace('\n', ''))
            
            # driver.find_elements_by_class_name("ts-fip__modal")[counter].find_element_by_class_name("ts-icon-close").click()
            scrapdatalist.append(filterdetails)
            counter=counter+1
        driver.close()
        return scrapdatalist
        # return {requdata["departurdate"]+"-"+requdata["returningdate"]+"-"+requdata["departure"]+"-"+requdata["arrival"]:scrapdatalist}
    except Exception as e:
        print("errro",e)
        return str(e)
        # return {requdata["departurdate"]+"-"+requdata["returningdate"]+"-"+requdata["departure"]+"-"+requdata["arrival"]:str(e)}





if __name__ == '__main__':
    t1=time.time()
    requdata=[{
        "departure":"cai",
        "arrival":"dxb",
        "twoway":True,
        "departurdate":"19/12/2020",
        "returningdate":"29/12/2020"
    },
    {
        "departure":"cai",
        "arrival":"cpt",
        "twoway":True,
        "departurdate":"19/1/2021",
        "returningdate":"29/1/2021"
    },
    {
        "departure":"cai",
        "arrival":"dxb",
        "twoway":True,
        "departurdate":"19/2/2020",
        "returningdate":"29/2/2020"
    }]
    finalresul={}
    for i in requdata:
        finalresul[i["departurdate"]+"-"+i["returningdate"]+"-"+i["departure"]+"-"+i["arrival"]]=main(i)
    print(json.dumps(finalresul),time.time()-t1)

# for thread
    # finalresul={}
    # for req in [requdata[x:x+3] for x in range(0,len(requdata),3)]:
    #     treadlinks=[]
    #     for i in req:
    #         th1=threading.Thread(target=lambda q,arg1: q.put(main(arg1)),args=(my_queue,i),daemon=True)
    #         th1.start()
    #         treadlinks.append(th1)
    #     for th in treadlinks:
    #         th.join()
    #     while not my_queue.empty():
    #         # print(my_queue.get())
    #         finalresul.update(my_queue.get())
    #     # print(i)
    #     # finalresul[i["departurdate"]+"-"+i["returningdate"]+"-"+i["departure"]+"-"+i["arrival"]]=main(i)
    # print(json.dumps(finalresul),time.time()-t1)