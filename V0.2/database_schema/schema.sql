-- *** IMPORTANT ***
-- Schema intended for Sqlite3 
-- May not be compatible for others
PRAGMA foreign_keys = on;

create table
    if not exists CustomerAccount (
        ID integer primary key autoincrement not null,
        Name nvarchar (50) not null, -- nvarchar uses more storage than varchar but supports more languages
        Email varchar(150) unique not null, -- Can't have duplicate emails
        Password char(60) not null, -- Bcrypt method stores hashes as 60 characters, may not support other methods. Change if necessary
        Address varchar(250),
        Points integer (4) not null default (0)
    );

create table
    if not exists BusinessAccount (
        ID integer primary key autoincrement not null,
        Name nvarchar (50) not null, -- nvarchar uses more storage than varchar but supports more languages
        Email varchar(150) unique not null, -- Can't have duplicate emails
        Password char(60) not null -- Bcrypt method stores hashes as 60 characters, may not support other methods. Change if necessary
    );

create table
    if not exists DeliverySchedule (
        ID integer primary key autoincrement not null,
        DeliveryDate Date not null, -- Called the "Date" column in ERD, changed to avoid confusion
        BusinessAccountID integer not null,
        foreign key (BusinessAccountID) references BusinessAccount (ID) on delete cascade
    );

create table
    if not exists Offer (
        ID integer primary key autoincrement not null,
        Type varchar(20) not null, -- Deny values with numbers
        Amount int (2) default (0) not null,
        CustomerAccountID integer not null,
        foreign key (CustomerAccountID) references CustomerAccount (ID) on delete cascade
    );

create table
    if not exists Notification (
        ID integer primary key autoincrement not null,
        Title varchar(30) not null,
        Description varchar(250) not null,
        IsRead boolean default (0) not null, -- Default to false
        CustomerAccountID integer default (null),
        BusinessAccountID integer default (null),
        foreign key (CustomerAccountID) references CustomerAccount (ID) on delete cascade,
        foreign key (BusinessAccountID) references BusinessAccount (ID) on delete cascade
    );

create table
    if not exists Category (
        ID integer primary key autoincrement not null,
        CategoryName varchar(25) not null
    );

-- As "Product" will have a many to many relationship to "Cart" 
-- As multiple products can belong in multiple (differnt users) carts
-- Changes are required due to a Oversight in the ERD Design
-- Cart PK will contain the IDs of product and customer
-- Product will not have CartID and OrderID columns 
create table
    if not exists Product (
        ID integer primary key autoincrement not null,
        ProductName varchar(50) not null,
        Description varchar(450) not null,
        Cost decimal(5, 2) not null,
        Unit varchar(10) not null,
        Stock int (3) not null default (0),
        Allergens varchar(250) not null default ('No allergens'),
        Method varchar(500) not null,
        DeliveryAvailable boolean not null default (0),
        CollectionAvailable boolean not null default (0),
        BusinessAccountID integer not null,
        CategoryID integer not null,
        foreign key (BusinessAccountID) references BusinessAccount (ID) on delete cascade,
        foreign key (CategoryID) references Category (ID) on delete cascade
    );

-- Added Ammount Column if user wants more than one unit of product
create table
    if not exists Cart (
        CustomerAccountID integer not null,
        ProductID integer not null,
        Ammount integer not null default 1,
        constraint ID primary key (CustomerAccountID, ProductID),
        foreign key (CustomerAccountID) references CustomerAccount (ID) on delete cascade,
        foreign key (ProductID) references Product (ID) on delete cascade
    );

-- Due to issue mentioned before
-- Orders will contain OrderItemID to place orders containg multiple products without interfering with cart
create table
    if not exists CustomerOrder (
        ID integer primary key autoincrement not null,
        OrderFufillDate date,
        OrderMadeDate Date not null default (CURRENT_DATE), -- Defaults to the current date YYYY-MM-DD to when customer clicked order
        Status varchar(30) not null,
        Type varchar(10) not null check (
            Type = 'Collection'
            or Type = 'Delivery'
        ),
        Total decimal(10, 2) not null default (0),
        BusinessAccountID integer not null,
        CustomerAccountID integer not null,
        foreign key (BusinessAccountID) references BusinessAccount (ID) on delete cascade,
        foreign key (CustomerAccountID) references CustomerAccount (ID) on delete cascade
    );

-- Values will be inserted from Cart table
create table
    if not exists OrderItem (
        ID integer primary key autoincrement not null,
        CustomerAccountID integer not null,
        ProductID integer not null,
        Amount integer not null default 1,
        BusinessAccountID integer not null,
        OrderID integer,
        foreign key (OrderID) references CustomerOrder (ID) on delete cascade,
        foreign key (CustomerAccountID) references CustomerAccount (ID) on delete cascade,
        foreign key (BusinessAccountID) references BusinessAccount (ID) on delete cascade,
        foreign key (ProductID) references Product (ID) on delete cascade
    );