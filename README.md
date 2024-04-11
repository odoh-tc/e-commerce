# Overview

    This FastAPI application provides a robust backend solution for managing users, businesses, products, and orders. It offers endpoints for user authentication, user registration, CRUD operations for users, businesses, products, and orders, as well as various validation mechanisms to ensure data integrity and security.

**Features**
**User Management**:

    User registration with strong password validation.
    User authentication with JWT token generation.
    Role-based access control (customers and business owners).
    User profile retrieval and update.
**Business Management:**

    Business creation, update, and deletion by business owners.
    Retrieval of businesses owned by a specific user.
    Listing all products associated with a business.
**Product Management:**

    Product creation, update, and deletion by business owners.
    Retrieval of products associated with a business.
    Validation of product details and stock availability.
**Order Management:**

    Order creation by customers with validation against product availability.
    Retrieval of orders placed by a specific customer.
    Update and deletion of orders by customers and business owners.

Installation
    Clone the repository:

    git clone *repository-url*
    cd *repository-directory*

**Running Locally**
Install dependencies:

create and activate virtual environment using:
    python3.10 -m venv env && source env/bin/activate

    pip install -r requirements.txt
Set up the database:

    Modify the database settings in .env file

Usage
Start the FastAPI server:

    uvicorn main:app --reload
    Navigate to http://localhost:8000/docs in your browser to access the Swagger UI for testing the API endpoints.

**Deploying with Docker**
Build the Docker image:
    docker build -t fastapi-app .

Run the Docker container:
    docker run -d -p 8000:8000 fastapi-app

    Navigate to http://localhost:8000/docs in your browser to access the Swagger UI for testing the API endpoints.

*Note: Ensure that Docker is installed on your machine before deploying with Docker.*