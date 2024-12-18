create database redbus_1;
use redbus_1;
create table all_bus_routes(
id int auto_increment primary key,
route_name varchar(255), route_link varchar(255),
bus_name varchar(255), bus_type varchar(255), departing_time varchar(255),
duration varchar(255), reaching_time varchar(255), star_rating float,
price float, old_price float, total_seats int, window_seats int,
state_name varchar(255));
select * from all_bus_routes;

