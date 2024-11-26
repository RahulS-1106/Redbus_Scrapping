import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# MySQL Connection Setup
def connect_to_db():
    return pymysql.connect(
        host="localhost",       # Your MySQL server host
        user="root",            # Your MySQL username
        password="12345",       # Your MySQL password
        database="redbus_1"     # Database name
    )

# Initialize the WebDriver
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 30)  # Increased timeout for waiting

# Open the main page
driver.get("https://www.redbus.in/travels/nbstc")

# Define a list to store all the route data
all_data = []

def scrape_page():
    """Scrapes route data from the current page."""
    try:
        # Locate route containers
        routescontainer = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "route_details")))

        # Loop through each route to extract details
        for route in routescontainer:
            try:
                # Extract route name and link
                route_link_element = route.find_element(By.CLASS_NAME, "route")
                routename = route_link_element.text  # Route name is the text content
                routelink = route_link_element.get_attribute('href')  # Route link from href attribute

                # Append extracted data to the list
                all_data.append({'routename': routename, 'routelink': routelink})

            except Exception as e:
                print(f"An error occurred while extracting route data: {e}")
                continue

    except Exception as e:
        print(f"An error occurred on the page: {e}")

def scroll_page():
    """Scrolls to the bottom of the page to load all buses."""
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for content to load

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # End of page reached
        last_height = new_height

def click_buttons_and_scrape():
    """Clicks all buttons on the page and scrapes details revealed by them."""
    try:
        driver.maximize_window()
        time.sleep(3)  # Wait for content to load
        b = driver.find_elements(By.CSS_SELECTOR, "div[class='button']")
        time.sleep(3)

        # First, click the second button
        if len(b) > 1:
            try:
                wait.until(EC.element_to_be_clickable(b[1]))  # Wait for the second button to be clickable
                b[1].click()  # Click the second button
                time.sleep(3)  # Wait for content to load
            except Exception as e:
                print(f"An error occurred while clicking second button: {e}")

        # Then, click the first button
        if len(b) > 0:
            try:
                wait.until(EC.element_to_be_clickable(b[0]))  # Wait for the first button to be clickable
                b[0].click()  # Click the first button
                time.sleep(3)  # Wait for content to load
            except Exception as e:
                print(f"An error occurred while clicking first button: {e}")

        # Now perform scrolling to load all content
        scroll_page()

    except Exception as e:
        print(f"An error occurred while processing buttons: {e}")

def get_bus_details(route_link):
    """Scrapes bus details from the given route link."""
    try:
        # Open the route link
        driver.get(route_link)
        driver.maximize_window()
        time.sleep(1)  # Allow page to load

        # Handle buttons and scrape details from the dynamic content
        click_buttons_and_scrape()

        # Wait for the bus listings to load
        buses_container = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bus-item")))

        bus_details = []
        for bus in buses_container:
            try:
                # Extract bus details from the provided HTML structure
                busname = bus.find_element(By.CLASS_NAME, "travels").text
                bustype = bus.find_element(By.CLASS_NAME, "bus-type").text
                departing_time = bus.find_element(By.CLASS_NAME, "dp-time").text
                duration = bus.find_element(By.CLASS_NAME, "dur").text
                reaching_time = bus.find_element(By.CLASS_NAME, "bp-time").text

                # Extract the star rating
                try:
                    rating_text = bus.find_element(By.CLASS_NAME, "rating").text
                    star_rating = float(rating_text.strip())  # Convert to float
                except:
                    star_rating = None  # Handle cases where the rating is not found

                # Extract price information (old and current fare)
                old_price = None
                price = None
                try:
                    old_price_text = bus.find_element(By.CLASS_NAME, "oldFare").text
                    old_price = float(old_price_text.replace("INR", "").replace("₹", "").strip())  # Clean and convert old price
                except:
                    pass  # Handle cases where no old price is found

                try:
                    price_text = bus.find_element(By.CLASS_NAME, "fare").text
                    price = float(price_text.replace("INR", "").replace("₹", "").strip())  # Clean and convert current price
                except:
                    pass  # Handle cases where no current price is found

                # Extract total seats available
                try:
                    total_seats_text = bus.find_element(By.CLASS_NAME, "seat-left").text
                    total_seats = int(total_seats_text.split()[0])
                except:
                    total_seats = None  # Handle cases where seats are not available

                # Extract window seats
                try:
                    window_seats_text = bus.find_element(By.CLASS_NAME, "window-left").text
                    window_seats = int(window_seats_text.split()[0])
                except:
                    window_seats = None  # Handle cases where window seats are not available

                # Append the bus details to the list
                bus_details.append({
                    "busname": busname,
                    "bustype": bustype,
                    "departing_time": departing_time,
                    "duration": duration,
                    "reaching_time": reaching_time,
                    "star_rating": star_rating,
                    "price": price,
                    "old_price": old_price,
                    "total_seats": total_seats,
                    "window_seats": window_seats
                })
            except Exception as e:
                print(f"An error occurred while extracting bus details: {e}")
                continue

        return bus_details

    except Exception as e:
        print(f"An error occurred while visiting the bus route details page: {e}")
        return []

def insert_bus_details(route_data):
    """Inserts bus details into MySQL, including routename and routelink."""
    connection = connect_to_db()
    cursor = connection.cursor()

    # Insert the bus details for this route directly into buses table
    try:
        for bus in route_data['bus_details']:
            cursor.execute(""" 
                INSERT INTO apsrtc_buses (routename, routelink, busname, bustype, departing_time, duration, reaching_time, star_rating, price, old_price, total_seats, window_seats)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (route_data['routename'], route_data['routelink'], bus['busname'], bus['bustype'], bus['departing_time'], bus['duration'], 
                  bus['reaching_time'], bus['star_rating'], bus['price'], bus['old_price'], bus['total_seats'], bus['window_seats']))
        
        connection.commit()
        print(f"Data inserted for route {route_data['routename']} and its apsrtc_buses.")

    except Exception as e:
        print(f"An error occurred while inserting data into MySQL: {e}")
    finally:
        cursor.close()
        connection.close()

# Scrape data from the first 5 pages
for page_number in range(1, 6):
    scrape_page()
    if page_number < 5:  # Avoid navigating past the last page
        try:
            # Locate the pagination container
            pagination_container = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="root"]/div/div[4]/div[12]')
            ))

            # Locate the next page button within the container
            next_page_button = pagination_container.find_element(
                By.XPATH, f'.//div[contains(@class, "DC_117_pageTabs") and text()="{page_number + 1}"]'
            )

            # Ensure the next page button is in view
            actions = ActionChains(driver)
            actions.move_to_element(next_page_button).perform()
            time.sleep(1)  # Wait for smooth scrolling

            # Click the next page button
            next_page_button.click()

            # Wait for the active page number to match the target page
            wait.until(EC.text_to_be_present_in_element(
                (By.XPATH, '//div[contains(@class, "DC_117_pageTabs DC_117_pageActive")]'), str(page_number + 1)))

            # Wait for a short duration to ensure the next page loads completely
            time.sleep(3)

        except Exception as e:
            print(f"An error occurred while navigating to page {page_number + 1}: {e}")
            break

# Now, for each route, visit its link, scrape bus details and insert them into the database
for entry in all_data:
    route_data = get_bus_details(entry['routelink'])
    entry['bus_details'] = route_data
    insert_bus_details(entry)

# Close the WebDriver
driver.quit()
