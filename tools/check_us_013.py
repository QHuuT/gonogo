#!/usr/bin/env python3
"""
Check US-00013 status
"""

import sqlite3

def check_us_013():
    conn = sqlite3.connect('gonogo.db')
    cursor = conn.cursor()

    sql = """
    SELECT user_story_id, github_issue_number, title, epic_id, component
    FROM user_stories
    WHERE user_story_id = 'US-00013';
    """

    cursor.execute(sql)
    result = cursor.fetchone()

    if result:
        print("US-00013 Status:")
        print(f"  User Story ID: {result[0]}")
        print(f"  GitHub Issue: #{result[1]}")
        print(f"  Title: {result[2]}")
        print(f"  Epic ID: {result[3]}")
        print(f"  Component: {result[4]}")
    else:
        print("US-00013 not found")

    conn.close()

if __name__ == "__main__":
    check_us_013()