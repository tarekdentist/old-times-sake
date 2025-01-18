# Old Times Sake

## Video Demo
[Watch the Demo](https://youtu.be/e66NOC4JJSU)

## Description
**Old Times Sake** is a web application designed to help elderly individuals connect with people around them. The app allows users to send friend requests, discover age-appropriate activities, invite friends to join these activities, and exchange messages. With simplicity at its core, the app is tailored to meet the needs of the elderly demographic.

### Key Features
- **User-Friendly Interface**: A simple and accessible design.
- **Account Management**: Users can register with personal details, including a profile picture, which is securely stored using Cloudinary API.
- **Age Validation**: Ensures users are 50 years or older through both client-side and server-side validation.
- **Connect with Others**: Browse users by city or country, send connection requests, and manage friend requests dynamically without page reloads.
- **Discover Activities**: Find age-appropriate activities using Google Places API, complete with accessibility information.
- **Send Invitations**: Invite friends to activities and manage pending invitations.
- **Messaging System**: Exchange messages with friends and view them in a chronological layout.
- **Notifications**: Receive updates on the status of invitations.
- **Profile Management**: Update profile pictures and passwords securely.
- **Error Handling**: Customized error messages for user-specific issues.

---

## Routes and Features

### **Home Page**
- Features a navigation bar with "Log In" and "Register" buttons.
- Highlights the application's features with buttons redirecting users to respective pages or the login page.

### **Register**
- Input fields: First Name, Last Name, Username, Birthdate, Gender, Country, City, Interests, and Profile Picture.
- Validations:
  - **Client-side**: Ensures birthdate input corresponds to an age of at least 50 years.
  - **Server-side**: Validates data integrity and calculates age.
- **Country List**: Generated dynamically via an API and sorted alphabetically.

### **Connect**
- Browse users by city or country, displayed using Bootstrap cards.
- Send connection requests dynamically without page reloads.
- Requests are stored in the database and shown in the recipient’s "Requests" route.

### **Requests**
- View pending connection requests with options to "Accept" or "Reject."
- Accepted requests add users to the friend list, while rejected requests hide the sender permanently.

### **Activity**
- Discover activities in the user’s location using Google Places API.
- Filtered results for elderly-friendly activities like parks, libraries, and museums.
- View activity details and invite friends via a modal interface.

### **Invitations**
- Manage activity invitations with "Accept" or "Reject" options.
- Updates the database based on the user’s choice.

### **Notifications**
- View the status of sent invitations (accepted/rejected) in a card layout.

### **Friends**
- Browse a list of friends with the option to send messages via a modal interface.

### **Messages**
- View received messages in descending order, with options to reply via modal.

### **Profile**
- View and update profile details, including profile pictures and passwords.

### **Change Password**
- Update passwords securely with hashed storage.

### **Error**
- Customized error messages displayed using Jinja placeholders.

---

## Technologies Used
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Backend**: Python (Flask)
- **Database**: SQLite
- **APIs**: 
  - Google Places API
  - Cloudinary API
- **Validation**: Client-side (JavaScript) and Server-side (Flask, CS50.ai)

---
