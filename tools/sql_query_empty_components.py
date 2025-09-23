#!/usr/bin/env python3
"""
SQL Query for User Stories with Empty Components
"""

import sqlite3

def query_empty_components():
    conn = sqlite3.connect('gonogo.db')
    cursor = conn.cursor()

    sql = """
    SELECT user_story_id, github_issue_number, title, epic_id, component
    FROM user_stories
    WHERE component IS NULL;
    """

    print("=== User Stories with Empty Components ===")
    print("SQL Query:")
    print(sql)
    print("\nResults:")

    cursor.execute(sql)
    results = cursor.fetchall()

    if results:
        print("user_story_id | github_issue | title | epic_id | component")
        print("-" * 70)
        for row in results:
            print(f"{row[0]:<12} | {row[1]:<12} | {row[2]:<20} | {row[3]:<7} | {row[4]}")
        print(f"\nTotal: {len(results)} user stories with empty components")
    else:
        print("No user stories with empty components found.")

    conn.close()

if __name__ == "__main__":
    query_empty_components()