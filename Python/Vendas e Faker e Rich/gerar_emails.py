from faker import Faker
gen = Faker("pt_PT")
emails = {""}
while len(emails) != 11:
    emails.add(gen.free_email())
emails.discard("")
print(emails)
