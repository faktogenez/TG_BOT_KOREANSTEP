# Overview

This is a Telegram bot for course sales and payment processing. The bot handles user interactions for purchasing online courses, processes payments through multiple payment methods (YooMoney, Visa, Tinkoff, USDT), and manages user access to course materials. It integrates with Google Sheets for user data management and includes automated reminder systems for unpaid users.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework Architecture
- **Framework**: Built using python-telegram-bot library (v22.3) with async/await support
- **Handler Structure**: Uses Application pattern with separate handlers for commands, messages, and callback queries
- **Job Queue**: Implements background task scheduling for automated reminders
- **Logging**: Comprehensive logging system for monitoring bot operations

## Data Management
- **User Data Storage**: Google Sheets integration using gspread library for user registration and payment tracking
- **Authentication**: OAuth2 service account authentication with Google Sheets API
- **Caching**: In-memory caching of user payment status in context.user_data for performance
- **Data Structure**: Sheet contains user information including Telegram ID, payment status, and timestamps

## Payment Processing Architecture
- **Multi-Currency Support**: Handles RUB, USD, KRW, and USDT payments
- **Payment Methods**: YooMoney, Visa cards, bank transfers, and cryptocurrency
- **Verification Process**: Manual payment verification through screenshot/receipt checking
- **Status Management**: Tracks payment status and course access permissions

## Configuration Management
- **Environment Variables**: Uses python-dotenv for secure credential management
- **Modular Configuration**: Separate config.py file containing bot settings, payment details, and message templates
- **Credential Security**: Google Sheets API credentials stored in separate JSON file

## Messaging and UI Architecture
- **Inline Keyboards**: Custom keyboard layouts for user navigation
- **Rich Media Support**: Handles images, videos, and formatted text messages
- **Multi-language Content**: Prepared for internationalization with centralized message templates
- **HTML Parsing**: Uses Telegram's HTML parse mode for rich text formatting

## Background Services
- **Reminder System**: Automated job queue for sending payment reminders to users
- **Timezone Handling**: PyTZ integration for proper timestamp management
- **Error Handling**: Comprehensive exception handling with logging

# External Dependencies

## Core Dependencies
- **python-telegram-bot**: Primary framework for Telegram bot functionality with job queue support
- **gspread**: Google Sheets API client for data management
- **oauth2client**: Authentication library for Google Sheets access
- **python-dotenv**: Environment variable management for secure configuration

## Utility Libraries
- **pytz**: Timezone handling for accurate timestamp management
- **requests**: HTTP client for external API communications
- **python-magic**: File type detection for media uploads
- **rsa/certifi**: Security and encryption libraries

## External Services
- **Google Sheets API**: Primary database for user data and payment tracking
- **Telegram Bot API**: Core messaging and interaction platform
- **Payment Processors**: 
  - YooMoney payment system
  - Traditional banking systems (Visa, MIR cards)
  - Cryptocurrency payment processing (USDT)

## Infrastructure
- **Deployment**: Configured for PythonAnywhere hosting with always-on tasks
- **Alternative Deployment**: Linux server deployment support with systemd services
- **Virtual Environment**: Python 3.10+ requirement with isolated dependency management