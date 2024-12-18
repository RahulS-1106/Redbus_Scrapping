**Red Bus Scraping Project**

Overview:
The Red Bus Project is a web scraping and visualization tool built with Selenium to extract bus information from the RedBus website. It stores the data in a MySQL database and provides an interactive visualization interface using Streamlit. The goal is to deliver insights into bus schedules, prices, ratings, and seat availability.

Features:
Data Scraping: Automates the extraction of key information such as bus routes, departure/arrival times, bus types, ratings, and prices using Selenium. Data Storage: Scraped data is stored in MySQL, enabling efficient query operations and structured data management. Visualization: An interactive Streamlit app allows users to explore and analyze the bus data through charts and filters.

Application Features:
State Filter: Select a state to filter buses relevant to that region.
Route Selection: Choose 'From' and 'To' locations for route-specific searches.
Additional Filters: 
1. Filter by bus type (e.g., AC, Non-AC).
2. Set price range and minimum star rating.
3. Filter by seat availability and departing time.
Real-Time Results:
Search results are displayed dynamically based on the selected filters.

Technologies Used:
Selenium: To automate web scraping from RedBus.
MySQL: As the database for storing the scraped data.
Streamlit: For creating a web-based interface for visualizing the data.
Python: For all backend operations, including scraping, data processing, and visualization.
