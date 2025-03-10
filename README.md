# Multi-Vendor E-commerce Platform

This project is built using Django and Django Rest Framework (DRF) to provide a robust and scalable backend for an e-commerce platform that supports multiple vendors.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Features

- **Multi-Vendor Support**: Allow multiple vendors to sell their products on the same platform.
- **User Authentication**: Secure user authentication and authorization using Django's built-in authentication system.
- **Product Management**: Vendors can add, update, and delete their products.
- **Order Management**: Customers can place orders, and vendors can manage their orders.
- **Payment Integration**: Integration with popular payment gateways for secure transactions.
- **Review and Rating System**: Customers can leave reviews and ratings for products and vendors.
- **Search and Filter**: Advanced search and filter options for products.
- **Admin Panel**: A comprehensive admin panel for managing the platform.

## Installation

### Prerequisites

- Python 3.6 or higher
- Django 3.0 or higher
- Django Rest Framework 3.11 or higher
- PostgreSQL (recommended) or any other supported database

### Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/shahtaz-tqldd/mitosis-backend.git
   cd mitosis-backend
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the environment variables**:

   - Create a PostgreSQL database.
   - Create a .env file and fill this up according to .env.example

5. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

## Usage

- Access the admin panel at `http://127.0.0.1:8000/admin/` using the superuser credentials.
- Access the API endpoints at `http://127.0.0.1:8000/api/`.

## API Endpoints

### Authentication

- `POST /api/v1/auth/register/`: Register a new user.
- `POST /api/v1/auth/login/`: Log in a user and get access token and refresh token.
- `POST /api/v1/auth/refresh-token/`: Token refresh
- `POST /api/v1/auth/forget-password/`: Forget password OTP sent to email
- `POST /api/v1/auth/reset-password/`: Reset password with OTP verification

### Vendors

- `GET /api/vendors/`: List all vendors.
- `POST /api/vendors/`: Create a new vendor.
- `GET /api/vendors/{id}/`: Retrieve a vendor.
- `PUT /api/vendors/{id}/`: Update a vendor.
- `DELETE /api/vendors/{id}/`: Delete a vendor.

### Products

- `GET /api/products/`: List all products.
- `POST /api/products/`: Create a new product.
- `GET /api/products/{id}/`: Retrieve a product.
- `PUT /api/products/{id}/`: Update a product.
- `DELETE /api/products/{id}/`: Delete a product.

### Orders

- `GET /api/orders/`: List all orders.
- `POST /api/orders/`: Create a new order.
- `GET /api/orders/{id}/`: Retrieve an order.
- `PUT /api/orders/{id}/`: Update an order.
- `DELETE /api/orders/{id}/`: Delete an order.

### Reviews

- `GET /api/reviews/`: List all reviews.
- `POST /api/reviews/`: Create a new review.
- `GET /api/reviews/{id}/`: Retrieve a review.
- `PUT /api/reviews/{id}/`: Update a review.
- `DELETE /api/reviews/{id}/`: Delete a review.