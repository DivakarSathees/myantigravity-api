**ECommerce Order Management**

  

**Problem Statement:**

Develop a Web API project for ECommerce Order Management using ASP.NET Core**.** This API will manage customers and their orders with complete CRU operations. The system should allow for customer creation and retrieval, as well as order creation, retrievel and updating management. You will need to define models, controllers, and handle status codes correctly. Make sure to implement validation and exception handling for erroneous input, especially in cases of missing data or invalid order amounts.

  

Your task is to implement the API based on the following requirements.

  

**Models:**

**Customer.cs:**

*   **CustomerId (int):** Represents the unique identifier for each customer. It is the primary key and is auto generated.
*   **Name (string):** The name of the customer. This field is required.
*   **Email (string):** The email address of the customer. This field is required and must be in a valid email format.
*   **Address (string):** The address of the customer. This field is required.
*   **Orders (ICollection<Order>):**
*   A **collection** of Order entities associated with the customer. This establishes a **one-to-many relationship** where one customer can have multiple orders. It is Optional.
*   This property is marked with \[JsonIgnore\] to prevent circular references during JSON serialization.

**Order.cs:**

*   **OrderId (int):** Represents the unique identifier for each order. It is the primary key and is auto generated.
*   **OrderDate (string):** Represents the date when the order was placed. This field must be in a valid format.
*   **TotalAmount (decimal):** The total amount for the order. It must be greater than zero.
*   **CustomerId (int):** Represents the foreign key linking to the Customer entity. This establishes a **many-to-one relationship** where multiple orders can be associated with a single customer.
*   **Customer (Customer):**
*   A reference to the Customer entity associated with the order. This navigation property links the order to the customer who placed it. It is Optional.
*   This property is marked with \[JsonIgnore\] to prevent circular references during JSON serialization.

  

Using **ApplicationDbContext** for **Customer** and **Order** Management. **ApplicationDbContext** must be present inside the **Data** folder.

*   **Namespace - dotnetapp.Data**

  

The **ApplicationDbContext** class acts as the primary interface between the application and the database, managing CR (Create, Read) operations for **Customer** entities and (Create, Read, Update) operations for **Order** entities. This context class defines the database schema through its DbSet properties and manages the **one-to-many relationship** between **Customer** and **Order** entities using the Fluent API.

  

**DbSet Properties:**

*   **DbSet<****Customer****\>** **Customer****s:**
*   Represents the **Customers** table in the database, where each **Customer** can have multiple associated **Order** entries. This defines the **one-to-many relationship** between **Customer** and **Order** (i.e., one Customer can make many Orders).
*   **DbSet<****Order****\>** **Order****s:**
*   Represents the **Orders** table in the database. Each Order is associated with a single **Customer**, establishing the many-to-one relationship between **Order** and **Customer** using the **CustomerId** **foreign key.**
*   `**OnDelete(DeleteBehavior.Cascade)**`: This is where the deletion behavior is configured. **Cascade delete** means that when a `Customer` entity is deleted, all associated `Order` entities will also be automatically deleted from the database.

  

**Implement the logic in the controller:**

**Controllers: Namespace:** `**dotnetapp.Controllers**`

**CustomerController:**

*   **CreateCustomer(\[FromBody\] Customer customer):**
*   Adds a new customer to the database.
*   Make a POST request to **/api/Customer** with the customer data in the request body.
*   Upon successful creation, it returns a **201 Created** response with the location of the newly created customer.
*   Return Type: **Task<ActionResult>**
*   **GetCustomersSortedByName():**
*   Retrieves and sorts customers by their name in ascending order.
*   Make a GET request to **/api/Customer/SortedByName**.
*   It returns a **200 OK** with the sorted customer list.
*   Return Type: **Task<ActionResult>**
*   **GetCustomer(int id):**
*   Retrieves a single customer by their CustomerId.
*   Make a GET request to **/api/Customer/{id}.**
*   If the customer is not found, it returns a **404 Not Found.**
*   Otherwise, it returns a **200 OK response** with the customer details.
*   Return Type: **Task<ActionResult>**

**OrderController:**

*   **CreateOrder(\[FromBody\] Order order):**
*   Adds a new order to the database.
*   Make a POST request to **/api/Order** with the order data in the request body.
*   If the order object is null, it returns a **400 Bad Request** with an error message.
*   Additionally, if the **TotalAmount** of the order is less than or equal to 0, it throws a custom **AmountException**.
*   Upon successful creation, it returns a **201 Created response** with the location of the newly created order.
*   Return Type: **Task<ActionResult>**
*   **GetOrders():**
*   Retrieves a list of all orders, including their associated customer ids.
*   Make a GET request to **/api/Order**.
*   If no orders are found, it returns a **204 No Content** instead of an empty list.
*   If orders are found, it returns a **200 OK response** with a list of orders and their associated customer ids.
*   Return Type: **Task<ActionResult>**
*   **UpdateOrder(int id, \[FromBody\] Order order):**
*   Updates the order identified by id.
*   Make a PUT request to **/api/Order/{id}** where {id} is the order's ID.
*   If the id does not match the OrderId of the provided order object, it returns a **400 Bad Request.**
*   If the order with the specified id is not found, it returns a 404 Not Found.
*   Upon a successful update, it returns a **204 No Content.**
*   Return Type: **Task<ActionResult>**

  

**Exceptions:**

*   The **AmountException** is a custom exception class located in the **dotnetapp.Exceptions** folder.
*   It is thrown when the **TotalAmount** in an order is less than or equal to 0. The exception provides the following message when triggered: **\\"Order amount must be greater than 0.\\"**

  

**Endpoints:**

**Customers:**

*   **POST /api/Customer:** Create a new customer.
*   **GET /api/Customer/SortedByName:** Retrieve and sort customers by name in ascending order.
*   **GET /api/Customer/{id}:** Retrieve a specific customer by their ID.

  

**Orders****:**

*   **GET /api/Order:** Retrieve a list of all orders, including their associated customerids.
*   **POST /api/Order:** Create a new order.
*   **PUT /api/Order/{id}:** Update an order by its ID.

  

**Status Codes and Error Handling:**

**204 No Content:** Returned when no records are found for Orders or customers.

**200 OK:** Returned when records are successfully retrieved.

**201 Created:** Returned when a new Orders or customer is successfully created.

**400 Bad Request:** Returned when there are validation errors or mismatched IDs during updates/creation.

**404 Not Found:** Returned when a Order or customer is not found during retrieval or deletion.

**AmountException:** Thrown when the **TotalAmount** of an order is less than or equal to 0, with the message **\\"Order amount must be greater than 0.\\" .** This exception should return a **status code of 500**.

  

**Note:**

*   Use swagger/index to view the API output screen in 8080 port.
*   Don't delete any files in the project environment.

  

**Commands to Run the Project:**

*   **cd dotnetapp**

Select the dotnet project folder

*   **dotnet restore**

This command will restore all the required packages to run the application.

*   **dotnet run**

To run the application in port 8080 (The settings preloaded click 8080 Port to View)

*   **dotnet build**

To build and check for errors

*   **dotnet clean**

If the same error persists clean the project and build again

  

  

**For Entity Framework Core:**

To use

Entity Framework :

Install EF:

*   **dotnet new tool-manifest**
*   **dotnet tool install --local dotnet-ef --version 6.0.6**

\\t\\t\\t--Then use dotnet dotnet-ef instead of dotnet-ef.

*   **dotnet dotnet-ef**

\\t\\t\\t--To check the EF installed or not.

*   **dotnet dotnet-ef migrations add initialsetup**

\\t\\t\\tThis command is to add migrations

*   **dotnet dotnet-ef database update**

\\t\\t\\tThis command is to update the database.

  

**Note:**

Use the below sample connection string to connect the MsSql Server

 private string **connectionString** \= \\"User ID=sa;password=examlyMssql@123; server=localhost;Database=appdb;trusted\_connection=false;Persist Security Info=False;Encrypt=False\\"