# E-Commerce_api

This FastAPI application provides a robust backend solution for managing users, businesses, products, and orders. It offers endpoints for user authentication, user registration, CRUD operations for users, businesses, products, and orders, as well as various validation mechanisms to ensure data integrity and security.

---

### Prerequisites:

Before you begin, ensure you have met the following requirements:

- SQLite3: SQLite3 is included with Python by default, so you don't need to install it separately. However, make sure you have a SQLite3 database file ready to use with your FastAPI application.

- Python: Make sure you have Python installed on your machine. You can download it from python.org.
  
---  

### Features

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

    git clone <repository-url>
    cd <repository-directory>

---

### Running Locally
Install dependencies:

create and activate virtual environment using:
    python3.10 -m venv env && source env/bin/activate

    pip install -r requirements.txt

---

#### Configuration

##### Environment Variables

The API uses environment variables to configure connections. Create a .env file in the root directory of the project and define the following variables:

    EMAIL = your_email_address
    PASS = your_email_password
    SECRET = your_secret_key

Make sure to replace `your_email_address` and `your_email_password` with your actual email address and password.

##### Generating the Secret Key

The SECRET variable is used for authentication and security purposes within the application. To generate a secure secret key, you can use Python's secrets module to generate a random hexadecimal string. Here's an example of how you can generate a secret key:

```python

import secrets

secret_key = secrets.token_hex(10)
print("Generated Secret Key:", secret_key)


```

---

##### Usage
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

---

### Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these guidelines:

1. Fork the repository and create a new branch for your feature or bug fix.

2. Make your changes and test thoroughly.

3. Ensure your code follows the existing coding style.

4. Create a pull request with a clear description of your changes.

---

### License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/odoh-tc/repo/blob/main/LICENSE) file for details.

---