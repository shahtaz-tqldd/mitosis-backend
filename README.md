# Multi-Vendor E-commerce Backend

This project is built using Django and Django Rest Framework (DRF) to provide a robust and scalable backend for an e-commerce platform that supports multiple vendors.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)

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