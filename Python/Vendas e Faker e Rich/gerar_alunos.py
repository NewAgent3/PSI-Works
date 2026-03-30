from faker import Faker
generator = Faker("pt_PT")
for _ in range(1, 11):
    nome = generator.name()
    email = nome.lower().replace(" ", "") + "@" + generator.free_email_domain()
    print(nome, email)
