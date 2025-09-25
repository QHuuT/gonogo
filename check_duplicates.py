from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./gonogo.db')
conn = engine.connect()

# Check duplicate blog_content_steps
result = conn.execute(text("""
    SELECT id, test_file_path, test_function_name, test_type
    FROM tests
    WHERE test_function_name = 'blog_content_steps'
"""))
rows = result.fetchall()

print('Duplicate blog_content_steps records:')
for row in rows:
    print(f'ID {row[0]}: {row[3]} - {row[1]} :: {row[2]}')

print(f'\nTotal: {len(rows)} records with same function name from different files')
print('This is a BDD step definition naming collision - same function name in different step files')

conn.close()