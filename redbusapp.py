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

# Fetch unique 'State Names' dynamically
def fetch_unique_state_names():
    query = "SELECT DISTINCT state_name FROM all_bus_routes"
    state_df = fetch_data(query)
    if state_df.empty:
        return []
    return sorted(state_df["state_name"].dropna().unique().tolist())

# Fetch unique 'From' and 'To' locations dynamically based on state
def fetch_locations_by_state(state_name):
    query = """
        SELECT DISTINCT route_name FROM all_bus_routes
        WHERE state_name = %s
    """
    routes_df = fetch_data(query, [state_name])
    if routes_df.empty:
        return [], []

    # Split the routename into 'From' and 'To' parts
    routes_df["from_location"] = routes_df["route_name"].apply(lambda x: x.split("to")[0].strip().lower() if "to" in x.lower() else None)
    routes_df["to_location"] = routes_df["route_name"].apply(lambda x: x.split("to")[-1].strip().lower() if "to" in x.lower() else None)

    # Get unique locations
    from_locations = routes_df["from_location"].dropna().unique().tolist()
    to_locations = routes_df["to_location"].dropna().unique().tolist()

    return sorted(from_locations), sorted(to_locations)

# Fetch unique values for additional filters
def fetch_unique_column_values(column_name):
    query = f"SELECT DISTINCT {column_name} FROM all_bus_routes"
    column_df = fetch_data(query)
    if column_df.empty:
        return []
    column_df[column_name] = column_df[column_name].fillna(0)  # Handle NaN
    if column_name in ["total_seats", "window_seats"]:
        column_df[column_name] = column_df[column_name].astype(int)  # Convert to integers
    return sorted(column_df[column_name].unique().tolist())

# Streamlit App
def main():
    st.set_page_config(page_title="Redbus Data Scraping with Selenium & Dynamic Filtering using Streamlit", layout="wide")

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

    # Fetch unique state names for dropdown
    state_names = fetch_unique_state_names()

    # Sidebar Filters
    st.sidebar.header("Search Filters")
    
    # State Name Filter
    state_name = st.sidebar.selectbox(
        "State Name",
        options=[""] + state_names,
        format_func=lambda x: "Choose an option" if x == "" else x,
    )

    # Fetch locations based on the selected state
    if state_name:
        from_locations, to_locations = fetch_locations_by_state(state_name)
    else:
        from_locations, to_locations = [], []

    # Integrated Search Fields with Dropdown Suggestions
    from_location = st.sidebar.selectbox(
        "From Location",
        options=[""] + from_locations,
        format_func=lambda x: "Choose an option" if x == "" else x,
    )

    to_location = st.sidebar.selectbox(
        "To Location",
        options=[""] + to_locations,
        format_func=lambda x: "Choose an option" if x == "" else x,
    )

    # Submit Button
    if st.sidebar.button("Search"):
        query = """
            SELECT * FROM all_bus_routes
            WHERE 
                state_name = %s
                AND LOWER(TRIM(SUBSTRING_INDEX(route_name, 'to', 1))) LIKE %s
                AND LOWER(TRIM(SUBSTRING_INDEX(route_name, 'to', -1))) LIKE %s;
        """
        params = [state_name, f"%{from_location.lower()}%", f"%{to_location.lower()}%"]
        
        data = fetch_data(query, params)
        if data.empty:
            st.warning("No buses found matching your search criteria.")
            st.session_state.search_results = pd.DataFrame()
        else:
            st.session_state.search_results = data.reset_index(drop=True)
    
    # Bus Type Filters
    st.sidebar.subheader("Bus Type Filters")
    bus_type_filter = st.sidebar.selectbox(
        "Bus Type",
        options=["All", "Seater", "Sleeper", "AC", "Non-AC"],
        index=0,
    )
    
    # Additional Filters
    st.sidebar.subheader("Additional Filters")
    min_rating = st.sidebar.slider("Minimum Star Rating", min_value=0.0, max_value=5.0, step=0.1, value=0.0)
    price_range = st.sidebar.slider("Price Range", min_value=0, max_value=5000, value=(0, 5000))

    # Fetch unique departing times, total seats, and window seats for dropdowns
    departing_times = fetch_unique_column_values("departing_time")
    total_seats = fetch_unique_column_values("total_seats")
    window_seats = fetch_unique_column_values("window_seats")

    departing_time_filter = st.sidebar.selectbox(
        "Departing Time",
        options=["All"] + departing_times,
        index=0,
    )

    total_seats_filter = st.sidebar.selectbox(
        "Total Seats",
        options=["All"] + [str(seats) for seats in total_seats],
        index=0,
    )

    window_seats_filter = st.sidebar.selectbox(
        "Window Seats",
        options=["All"] + [str(seats) for seats in window_seats],
        index=0,
    )

    # Display Results
    if not st.session_state.search_results.empty:
        filtered_data = st.session_state.search_results.copy()
        
        if bus_type_filter != "All":
            if bus_type_filter == "Seater":
                filtered_data = filtered_data[filtered_data["bus_type"].str.contains("SEATER", case=False, na=False)]
            elif bus_type_filter == "Sleeper":
                filtered_data = filtered_data[filtered_data["bus_type"].str.contains("SLEEPER", case=False, na=False)]
            elif bus_type_filter == "AC":
                filtered_data = filtered_data[~filtered_data["bus_type"].str.contains("Non-AC", case=False, na=False)]
            elif bus_type_filter == "Non-AC":
                filtered_data = filtered_data[filtered_data["bus_type"].str.contains("Non-AC", case=False, na=False)]

        if departing_time_filter != "All":
            filtered_data = filtered_data[filtered_data["departing_time"] == departing_time_filter]

        if total_seats_filter != "All":
            filtered_data = filtered_data[filtered_data["total_seats"] == int(total_seats_filter)]

        if window_seats_filter != "All":
            filtered_data = filtered_data[filtered_data["window_seats"] == int(window_seats_filter)]

        if "star_rating" in filtered_data.columns:
            filtered_data = filtered_data[filtered_data["star_rating"] >= min_rating]

        if "price" in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data["price"] >= price_range[0]) & (filtered_data["price"] <= price_range[1])
            ]

        if filtered_data.empty:
            st.warning("No buses found matching your filters.")
        else:
            st.subheader("Search Results")
            st.dataframe(filtered_data, use_container_width=True, height=600)
    else:
        st.info("Enter 'From' and 'To' details in the sidebar and click 'Search'.")

if __name__ == "__main__":
    main()
