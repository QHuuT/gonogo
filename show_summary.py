from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./gonogo.db")
conn = engine.connect()

result = conn.execute(
    text(
        "SELECT test_type, COUNT(*) as count, "
        "COUNT(test_function_name) as with_func "
        "FROM tests GROUP BY test_type"
    )
)

print("\nDatabase Test Summary:")
print(f"{'Type':<15} {'Total':<10} {'With Function':<15}")
print("-" * 45)
for row in result:
    print(f"{row[0]:<15} {row[1]:<10} {row[2]:<15}")

print("\n")
result = conn.execute(
    text("SELECT COUNT(*) FROM tests WHERE test_function_name IS NOT NULL")
)
total_with_func = result.scalar()

result = conn.execute(text("SELECT COUNT(*) FROM tests"))
total = result.scalar()

print(f"Total tests: {total}")
print(
    f"Tests with function names: {total_with_func} ({total_with_func * 100 // total}%)"
)
print(f"Tests without function names: {total - total_with_func} (BDD scenarios)")

conn.close()
