from llm.code_generator import generate_code_from_query

query = "Add 'Somebody That I Used to Know' to my June playlist"
code = generate_code_from_query(query)

print(code)
