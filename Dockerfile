FROM python:3.12-slim

# Prevents Python from buffering outputs
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /mitosis_app

# Copy only requirements first for better caching
COPY requirements.txt /mitosis_app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the project files
COPY . /mitosis_app/

# Expose port 5000
EXPOSE 5000

# Run migrations in a specific order and start the server
CMD ["sh", "-c", "python manage.py makemigrations user && \
                  python manage.py makemigrations products && \
                  python manage.py makemigrations && \
                  python manage.py migrate user && \
                  python manage.py migrate products && \
                  python manage.py migrate && \
                  python manage.py runserver 0.0.0.0:5000"]