# Authentication System


##  Project Overview
This is a modern authentication system built to provide **secure, scalable, and flexible user authentication** for web applications. It supports:

- Standard **email/password login and signup**  
- **Google OAuth 2.0** integration  
- **Multi-Factor Authentication (MFA)** using authenticator apps  
- JWT-based session management for secure sessions  

It’s designed to help developers implement authentication quickly while following best security practices.

---


<a href="https://ibb.co/390yTqhx"><img src="https://i.ibb.co/Pv5ZrnC2/auth-login.png" alt="auth-login" border="0" /></a>



<a href="https://ibb.co/8C55ycg"><img src="https://i.ibb.co/vFPPNY4/authscreen.png" alt="authscreen" border="0" /></a>

## Key Features

- **Email & Password Authentication**: Handles registration and login with hashed passwords.  

- **Google OAuth 2.0 Login**: Integrates Google sign-in while enforcing security.  

- **MFA / 2FA Support**: Implements Time-Based One-Time Passwords (TOTP) for additional account protection.  

- **JWT-based Authentication**: Provides stateless sessions with user information stored in tokens.  

- **API Endpoints**: Exposes endpoints for login, signup, MFA setup, and user data retrieval.


## Technologies Used
- **Frontend:** React, React Router  
- **Backend:** Python, FastAPI  
- **Database:** PostgreSQL  
- **Authentication & Security:**  
  - JWT for token-based sessions  
  - OAuth 2.0 for Google login  
  - MFA using TOTP  
  - Passwords hashed with bcrypt  

---

## How to run the server locally

### Backend Setup
1. Clone the repository:  
   ```bash
   git clone https://github.com/hyemiie/authentication_system
   
2. Install dependencies:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set environment variables:
Create a .env file:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret
```

4. Start the backend:

```bash
uvicorn main:app --reload
```

Backend runs at http://127.0.0.1:8000

| Endpoint                | Method | Description                               |
| ----------------------- | ------ | ----------------------------------------- |
| `/signup`               | POST   | Creates a new user (email/password/name)   |
| `/login`                | POST   | Authenticates a user and return JWT        |
| `/google/login`         | GET    | Initiates Google OAuth login               |
| `/auth/google/callback` | GET    | Handles Google login callback and syncs user info        |
| `/setup_mfa`            | POST   | Generates QR code and secret for MFA setup |
| `/verify_mfa`           | POST   | Verifies TOTP code during MFA login         |
| `/user/{email}`         | GET    | Fetches user data by email                  |

## How It Works

1. **Email/Password Registration & Login**  
   - User signs up with email, password, and name.  
   - Passwords are hashed before storing in the database.  
   - On login, credentials are verified and a JWT token is issued.  

2. **Google OAuth Login**  
   - User clicks "Sign in with Google".  
   - Browser is redirected to Google OAuth consent page.  
   - Google redirects back to `/auth/google/callback` with an authorization code.  
   - Backend exchanges the code for access and ID tokens, creates or updates the user, and issues a session token.  

3. **MFA / 2FA Verification**  
   - For users with MFA enabled, a TOTP code is generated via authenticator app.  
   - User submits the 6-digit code to `/verify_mfa`.  
   - Backend verifies the code and completes login if valid.  

4. **JWT-based Session Management**  
   - After successful login, backend issues a JWT containing user info.  
   - Frontend stores the JWT (in memory or local storage) and includes it in API requests.  
   - Backend validates the token on protected endpoints.  


You can test how this works on the demo url: https://auth-client-eight.vercel.app/
---
## Contributing
Want to suggest a feature or fix a bug?
Fork the repo, make your changes, and open a pull request — I’m open to ideas or good conversations.

GitHub: [@hyemiie](https://github.com/hyemiie)  
Email: yemiojedapo1@gmail.com
