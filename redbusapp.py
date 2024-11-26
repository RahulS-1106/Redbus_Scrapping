import streamlit as st
import pymysql
import pandas as pd

# Database Connection Function
def connect_to_db():
    try:
        return pymysql.connect(
            host="localhost",  # Replace with your host
            user="root",  # Replace with your username
            password="12345",  # Replace with your password
            database="redbus_1",  # Replace with your database name
        )
    except pymysql.MySQLError as e:
        st.error(f"Database connection failed: {e}")
        return None

# Fetch data from the database
def fetch_data(query, params=None):
    conn = connect_to_db()
    if conn is None:
        return pd.DataFrame()  # Return an empty DataFrame if connection fails
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        data = cursor.fetchall()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Data fetching failed: {e}")
        return pd.DataFrame()  # Return empty DataFrame on failure
    finally:
        conn.close()

# Fetch unique 'From' and 'To' locations dynamically
def fetch_unique_locations():
    query = "SELECT DISTINCT routename FROM apsrtc_buses"
    routes_df = fetch_data(query)
    if routes_df.empty:
        return [], []

    # Split the routename into 'From' and 'To' parts
    routes_df["from_location"] = routes_df["routename"].apply(lambda x: x.split("to")[0].strip().lower() if "to" in x.lower() else None)
    routes_df["to_location"] = routes_df["routename"].apply(lambda x: x.split("to")[-1].strip().lower() if "to" in x.lower() else None)

    # Get unique locations
    from_locations = routes_df["from_location"].dropna().unique().tolist()
    to_locations = routes_df["to_location"].dropna().unique().tolist()

    return sorted(from_locations), sorted(to_locations)

# Streamlit App
def main():
    st.set_page_config(page_title="Redbus Data Scraping with Selenium & Dynamic Filtering using Streamlit", layout="wide")  # Set wide layout for more space

    # Title at the top of the page
    st.title("Redbus Data Scraping with Selenium & Dynamic Filtering using Streamlit")

    # Add custom CSS to lift the main content upwards
    st.markdown(
        """
        <style>
            .main {
                padding-top: 0rem;  /* Reduces the padding at the top */
            }
        </style>
        """, 
        unsafe_allow_html=True
    )

    # Initialize session state for storing search results
    if "search_results" not in st.session_state:
        st.session_state.search_results = pd.DataFrame()

    # Fetch unique locations for dropdowns
    from_locations, to_locations = fetch_unique_locations()

    # Sidebar Filters
    st.sidebar.header("Search Filters")
    
    # Integrated Search Fields with Dropdown Suggestions
    from_location = st.sidebar.selectbox(
        "From Location",
        options=[""] + from_locations,  # Add an empty option for placeholder
        format_func=lambda x: "Choose an option" if x == "" else x,  # Display 'Choose an option' as the placeholder
    )

    to_location = st.sidebar.selectbox(
        "To Location",
        options=[""] + to_locations,  # Add an empty option for placeholder
        format_func=lambda x: "Choose an option" if x == "" else x,  # Display 'Choose an option' as the placeholder
    )

    # Submit Button
    if st.sidebar.button("Search"):
        # Build the query with splitting logic
        query = """
            SELECT * FROM apsrtc_buses
            WHERE 
                LOWER(TRIM(SUBSTRING_INDEX(routename, 'to', 1))) LIKE %s
                AND LOWER(TRIM(SUBSTRING_INDEX(routename, 'to', -1))) LIKE %s;
        """
        params = [f"%{from_location.lower()}%", f"%{to_location.lower()}%"]
        
        # Fetch and store results in session state
        data = fetch_data(query, params)
        if data.empty:
            st.warning("No buses found matching your search criteria.")
            st.session_state.search_results = pd.DataFrame()
        else:
            st.session_state.search_results = data.reset_index(drop=True)
    
    # Bus Type Filters (Always Visible)
    st.sidebar.subheader("Bus Type Filters")
    show_seater = st.sidebar.checkbox("Seater")
    show_sleeper = st.sidebar.checkbox("Sleeper")
    show_ac = st.sidebar.checkbox("AC")
    show_nonac = st.sidebar.checkbox("Non-AC")
    
    # Star Rating and Price Slider Filters
    st.sidebar.subheader("Additional Filters")
    min_rating = st.sidebar.slider("Minimum Star Rating", min_value=0.0, max_value=5.0, step=0.1, value=0.0)
    price_range = st.sidebar.slider("Price Range", min_value=0, max_value=5000, value=(0, 5000))

    # Display Results
    if not st.session_state.search_results.empty:
        # Filter data based on checkboxes
        filtered_data = st.session_state.search_results.copy()
        
        # Apply filter for Seater
        if show_seater:
            filtered_data = filtered_data[filtered_data["bustype"].str.contains("SEATER", case=False, na=False)]
        
        # Apply filter for Sleeper
        if show_sleeper:
            filtered_data = filtered_data[filtered_data["bustype"].str.contains("SLEEPER", case=False, na=False)]
        
        # Apply filter for AC buses
        if show_ac:
            # Exclude Non-AC buses
            nonac_regex = r"(^.*?(NON-AC|NONAC|non-ac|nonac|Non A/C|NON A/C|NON AC)[^\)]*\)?|.*\((NON-AC|NONAC|non-ac|nonac|Non A/C|NON A/C|NON AC)[^\)]*\))"
            filtered_data = filtered_data[~filtered_data["bustype"].str.contains(nonac_regex, case=False, na=False, regex=True)]

        # Apply filter for Non-AC buses
        if show_nonac:
            filtered_data = filtered_data[filtered_data["bustype"].str.contains(
                r"\(?(NON-AC|NONAC|non-ac|nonac|Non A/C|NON A/C|NON AC)[^\)]*\)?", 
                case=False, na=False, regex=True)]  # Explicitly specify regex=True

        # Apply filter for Star Rating
        if "star_rating" in filtered_data.columns:  # Corrected column name
            filtered_data = filtered_data[filtered_data["star_rating"] >= min_rating]
        else:
            st.warning("The 'star_rating' column is missing from the data.")

        # Apply filter for Price Range
        if "price" in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data["price"] >= price_range[0]) & (filtered_data["price"] <= price_range[1])
            ]
        else:
            st.warning("The 'price' column is missing from the data.")

        # Show filtered results
        if filtered_data.empty:
            st.warning("No buses found matching your filters.")
        else:
            # Place everything in the main container (aligned from left to top)
            st.subheader("Search Results")  # Header for the search results
            st.dataframe(filtered_data, use_container_width=True, height=600)  # Display the data with bigger space
    else:
        st.info("Enter 'From' and 'To' details in the sidebar and click 'Search'.")

if __name__ == "__main__":
    main()
