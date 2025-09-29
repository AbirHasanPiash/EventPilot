# 🎉 EventPilot

EventPilot is a robust **backend API for event management**, powered by **Django Rest Framework (DRF)** and **PostgreSQL**. It delivers a secure, scalable solution for handling events, user roles, and interactions, with built-in support for authentication, analytics, and seamless workflows. Whether you're an admin overseeing the platform, an organizer creating events, or an attendee exploring opportunities, EventPilot streamlines the entire process.

Key highlights include **JWT-based authentication** via **Djoser**, role-based access control, interactive dashboards, and comprehensive API features like pagination and Swagger documentation. Designed with security and performance in mind, it's ideal for building modern event management applications.

- **Live Link:**
    - `[https://event-pilot-tau.vercel.app/swagger/](https://event-pilot-tau.vercel.app/swagger/)`

---

## ✨ Features

EventPilot offers a comprehensive set of features to manage events efficiently:

- 🔑 **Authentication & Authorization**
  - Secure JWT (JSON Web Tokens) authentication integrated with Djoser for seamless user sessions.
  - Role-based access control (RBAC) supporting three primary roles: **Admin** (full platform oversight), **Organizer** (event creation and management), and **Attendee** (event participation and interaction).
  - Token refresh and revocation mechanisms for enhanced security.

- 📧 **User Accounts**
  - Automated account activation via email verification using Django signals, ensuring only verified users gain access.
  - Full user lifecycle management: registration, login, logout, password reset, and profile updates.
  - Customizable email templates for notifications like welcome emails, password resets, and event updates.

- 📊 **Dashboards**
  - Advanced analytics dashboards tailored for **Admins** and **Organizers**, featuring real-time charts, metrics, and insights (e.g., event attendance trends, user engagement statistics).
  - Visualization tools integrated with libraries like Chart.js (via API endpoints) for interactive data representation.

- 📅 **Event Management**
  - Intuitive event browsing and discovery with filters for categories, dates, locations, and popularity.
  - User interactions including attending events, liking, bookmarking, and sharing.
  - Organizer request system: Attendees can apply to become organizers, with admin approval workflows.
  - Event lifecycle handling: Creation, editing, publishing, cancellation, and archiving.

- 📦 **API Features**
  - Pagination on all list endpoints to handle large datasets efficiently.
  - Interactive API documentation powered by **Swagger** (via drf-yasg) for easy exploration and testing.
  - RESTful API design adhering to DRF best practices, with serializers, viewsets, and routers for maintainability.
  - Rate limiting and throttling to prevent abuse.

- 🛡 **Security**
  - Mandatory email verification prior to account activation to mitigate spam and unauthorized access.
  - Permission classes enforcing role-based restrictions on endpoints.
  - JWT tokens for all protected routes, with configurable expiration and blacklisting.
  - Protection against common vulnerabilities (e.g., CSRF, SQL injection) via Django's built-in safeguards.

- ☁️ **Hosting & Storage**
  - Image uploads handled securely via **Cloudinary** for scalable media management.
  - Deployment-ready for platforms like **Vercel**, with support for environment-specific configurations.

---

## 🛠 Tech Stack

EventPilot leverages modern, reliable technologies for a high-performance backend:

- **Backend Framework:** Django Rest Framework (DRF) for building scalable APIs.
- **Database:** PostgreSQL for robust, relational data storage with support for complex queries.
- **Authentication:** JWT combined with Djoser for user management and token handling.
- **Email Service:** Configurable SMTP backend (compatible with providers like Gmail or SendGrid) for reliable notifications.
- **Documentation:** Swagger integrated via drf-yasg for auto-generated, interactive API docs.
- **Media Storage:** Cloudinary for handling images and files.
- **Other Tools:** Django signals for event-driven actions, Celery (optional for background tasks), and environment variable management for secure configurations.

---

## ⚙️ Installation & Setup

Follow these steps to set up EventPilot locally:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/eventpilot.git
   cd eventpilot
   ```

2. **Install Dependencies**
   Create a virtual environment and install required packages:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Copy `.env.example` to `.env` and fill in your details:
   ```
   # Cloudinary Settings
   cloud_name=*******
   api_key=**********************
   api_secret=**********************
   CLOUDINARY_URL=**********************

   # Database Settings (PostgreSQL)
   user=**********************
   password=**********************
   host=**********************
   port=5432
   dbname=postgres

   # Django Settings
   SECRET_KEY=**********************

   # Frontend Integration (for CORS and links)
   FRONTEND_PROTOCOL=http
   FRONTEND_DOMAIN=localhost:3000

   # Email Settings
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_USE_TLS=True
   EMAIL_PORT=587
   EMAIL_HOST_USER=**********************
   EMAIL_HOST_PASSWORD=**********************
   DEFAULT_FROM_EMAIL=**********************
   ```

4. **Apply Migrations and Create Superuser**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run the Server**
   ```bash
   python manage.py runserver
   ```
For production deployment (e.g., on Vercel), ensure you configure environment variables in your hosting platform and use a production-ready database.

---

## 📘 API Documentation

Explore and test the API interactively via Swagger at:

- Local: `[http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)`
- Production: `/swagger/` on your deployed URL.

The docs include detailed endpoint descriptions, request/response schemas, and authentication instructions.

---

## 📜 License

This project is licensed under the MIT License.

---

## 📧 Contact

For support, feedback, or inquiries, reach out to: abirhasanpiash@gmail.com

Contributions are welcome! Feel free to fork the repository, submit pull requests, or open issues for bugs and feature requests.