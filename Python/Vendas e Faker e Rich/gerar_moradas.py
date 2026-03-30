from faker import Faker
falso = Faker("pt_PT")
for _ in range(1, 6):
    print(f"{falso.street_name()}  {falso.postcode()}  {falso.city()}")
