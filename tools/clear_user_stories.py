#!/usr/bin/env python3
"""
Clear existing user stories from database
"""

import sqlite3

def clear_user_stories():
    conn = sqlite3.connect('gonogo.db')
    cursor = conn.cursor()

    print("Clearing existing user stories...")
    cursor.execute("DELETE FROM user_stories")

    count = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"Deleted {count} user stories")

if __name__ == "__main__":
    clear_user_stories()