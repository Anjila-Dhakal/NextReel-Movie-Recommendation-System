🎬 NextReel – Movie Recommendation System

**Discover your next favorite movie with personalized recommendations!**

NextReel is a web-based movie recommendation system developed using Django and Python. It helps users discover movies through personalized recommendations based on user ratings and analyzes movie reviews using sentiment analysis.

## 📌 Project Overview

NextReel aims to make movie discovery easier by providing personalized recommendations, movie information, ratings, and review sentiment analysis through a user-friendly web interface.

## ✨ Features

- 🎥 **Movie Browsing:** Browse movies and explore movie details.
- 🤖 **Personalized Recommendations:** Uses Singular Value Decomposition (SVD) collaborative filtering to recommend movies based on user-rating patterns.
- ⭐ **Movie Ratings:** Allow users to rate movies.
- 💬 **Review System:** Submit and view movie reviews.
- 🧠 **Sentiment Analysis:** Uses a Naive Bayes classifier to analyze review sentiment.
- 🔎 **Movie Search:** Search for movies by title.
- 👤 **User Authentication:** Register, log in, and manage user profiles.
- 🛠️ **Admin Dashboard:** Manage movie records, users, and model retraining.
- 📈 **Recommendation Model Training:** Retrain the recommendation model using available rating data.

## 🧰 Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Django | Web application framework |
| SQLite | Database |
| Pandas | Data processing |
| Scikit-learn | Machine learning and sentiment analysis |
| SVD Collaborative Filtering | Movie recommendation |
| Naive Bayes | Review sentiment classification |
| HTML & CSS | User interface |
| JavaScript | Frontend interactions |
| Git & GitHub | Version control |

## ⚙️ Machine Learning

### 1. SVD Collaborative Filtering

NextReel uses Singular Value Decomposition (SVD) to learn patterns from user–movie ratings and estimate how much a user may like an unrated movie.

The predicted rating can be expressed as:

\[
\hat r_{ui}=\mu+b_u+b_i+p_u^Tq_i
\]

Where:
- \(\mu\) represents the overall average rating.
- \(b_u\) represents the user bias.
- \(b_i\) represents the movie bias.
- \(p_u\) and \(q_i\) represent learned user and movie factors.

### 2. Naive Bayes Sentiment Analysis

A Naive Bayes classifier analyzes movie review text and predicts its sentiment based on patterns learned from labeled training data.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or a compatible Python version
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Anjila-Dhakal/NextReel-Movie-Recommendation-System.git
cd NextReel-Movie-Recommendation-System
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

If the project requires environment variables, create a local `.env` file based on `.env.example` and configure the required values.

Never upload real passwords, secret keys, or API credentials to GitHub.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an administrator account (optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create your account.

### 7. Start the development server

```bash
python manage.py runserver
```

Open the following URL in your browser:

http://127.0.0.1:8000/

## 📂 Project Structure

```text
NextReel-Movie-Recommendation-System/
├── admin_panel/
├── datasets/
├── media/
├── movie_project/
├── movies/
├── recommendations/
├── reviews/
├── users/
├── static/
├── templates/
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
