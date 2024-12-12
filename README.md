# AUBoutique---Final-Project
AUBoutique: An Online Marketplace for the AUB Community

Overview

AUBoutique is an online marketplace designed specifically for the American University of Beirut (AUB) community to facilitate the buying and selling of various products. The project was developed in two phases:

Phase I: Focused on building a basic online marketplace with essential functionalities such as account management, product listing, product selling, and communication.

Phase II: Enhanced the system with a user-friendly Graphical User Interface (GUI) using PyQt5, peer-to-peer communication, product ratings, multi-currency support, and additional features.

System Architecture

2.1 Client-Server Architecture (Phase I)

The initial implementation employed a client-server architecture:

The server acts as a central repository for product listings and user data.

Clients interact with the server to manage accounts, product listings, and transactions.

All interactions between clients were routed through the server.

2.2 Hybrid Architecture (Phase II)

In Phase II, the system evolved into a hybrid model:

The server manages user accounts, product databases, and initial connection setup using TCP connections.

Peer-to-peer communication enables direct interaction between users, reducing server load and enhancing real-time capabilities.

Protocol and Communication

3.1 Communication Protocols

TCP (Transmission Control Protocol): Ensures reliable data transfer for critical actions like login, product management, and notifications.

UDP (User Datagram Protocol): Enables low-latency and efficient peer-to-peer messaging.

3.2 Client Request Handling

The client sends JSON-encoded requests specifying the desired action (e.g., login, add, buy, rate). Each request includes relevant data such as credentials, product details, or message content.

3.3 Server Response Handling

The server processes the request, interacts with the database as needed, and sends a JSON-encoded response back to the client. The response includes the action status and any additional data.

Features and Implementation

4.1 Account Management

Registration: User credentials are hashed using SHA-256 before being stored.

Login: The server verifies credentials and updates user status.

4.2 Product Management

Adding Products: Clients send product details (name, price, description, image). The server stores this information and notifies followers of the seller.

Buying Products: Clients specify product ID and quantity. The server updates inventory, logs the transaction, and sends a confirmation message with a collection date.

4.3 Messaging and Chat

Phase I: Server-routed messaging with offline message storage.

Phase II: Direct peer-to-peer messaging using UDP sockets.

4.4 User Following and Notifications

Following/Unfollowing: Clients can follow or unfollow other users. Notifications are sent when followed users list new products.

4.5 Currency Conversion

Supports multi-currency pricing with exchange rates fetched from an external API.

4.6 Product Ratings

Buyers can rate purchased products (1-5 stars). Ratings are aggregated and updated in real time.
Implementation Details

6.1 Client-Side

The client uses PyQt5 for the GUI, featuring:

Login/Registration Pages.

Dashboard for browsing products, managing inventory, chatting, and viewing followed users.

Search functionality for finding specific products.

6.2 Server-Side

The server is built using Python and SQLite, handling:

Database management (users, products, transactions, messages).

Request processing and response generation.

Notifications for new product listings.

6.3 Database Schema

userInfo: Stores user details and statuses.

objForSell: Tracks product details.

log: Records transactions.

messages: Stores undelivered messages.

followers: Manages follow relationships.

Appendix

7.1 Application Snapshots

Login Page

Dashboard

Chat Interface

Currency Selector
