#!/usr/bin/env python3
"""
Simple fix for US-00004 using direct SQL
"""

import sqlite3
import sys

def fix_us_004():
    # Connect directly to database
    conn = sqlite3.connect('gonogo.db')
    cursor = conn.cursor()

    print("=== Simple Fix US-00004 Epic FK ===\n")

    # Check current state
    cursor.execute("SELECT user_story_id, epic_id FROM user_stories WHERE user_story_id = 'US-00004'")
    result = cursor.fetchone()
    if result:
        print(f"Current: {result[0]} has epic_id = '{result[1]}'")

    # Get the correct epic ID
    cursor.execute("SELECT id, epic_id FROM epics WHERE epic_id = 'EP-00005'")
    epic_result = cursor.fetchone()
    if epic_result:
        correct_epic_id = epic_result[0]
        print(f"Epic EP-00005 has database id = {correct_epic_id}")

        # Update the foreign key
        cursor.execute("UPDATE user_stories SET epic_id = \
            ? WHERE user_story_id = 'US-00004'", (correct_epic_id,))

        # Verify the change
        cursor.execute("SELECT user_story_id, epic_id FROM user_stories WHERE user_story_id = 'US-00004'")
        new_result = cursor.fetchone()
        print(f"Updated: {new_result[0]} now has epic_id = {new_result[1]}")

        conn.commit()
        print("✅ Fix committed to database")
    else:
        print("❌ Epic EP-00005 not found")

    conn.close()

if __name__ == "__main__":
    fix_us_004()