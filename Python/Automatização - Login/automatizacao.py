import pyautogui as pyag
import os
import time as t
import colorama as clrm


def autologin(email, password):
    pyag.press("super")
    pyag.write("Opera GX")
    t.sleep(0.5)
    pyag.press("enter")
    t.sleep(1.5)
    pyag.write("https://fill.dev/form/login-simple")
    t.sleep(0.5)
    pyag.press("enter")
    t.sleep(5)
    pyag.click(620, 278)
    pyag.write(email[0:email.find("@") + 1])
    pyag.click(620, 330)
    pyag.write(password)
    pyag.press("enter")
    t.sleep(0.5)
    pyag.screenshot("verificação.png")
    aviso = "\nFoi tirada uma captura de ecrã! A mesma está na pasta onde este programa está!"
    return aviso


clrm.Style.RESET_ALL
os.system('cls' if os.name == 'nt' else 'clear')
print("="*5, "| LOGIN AUTOMÁTICO |", "="*5)
email = input("\nEmail: ")
while "@" not in email or (".com" or ".org") not in email:
    print(clrm.Fore.RED)
    email = input("Email inválido! | Email: ")
    print(clrm.Style.RESET_ALL)
password = input("Password: ")
print("\n", "="*20)
print(f"\nEmail: {email}\nPassword: {password}")
try:
    verificar = int(
        input("Quer fazer o login automáticamente?\n\n1 - Sim\n2 - Não\n\nEscolha: "))
    match verificar:
        case 1:
            pass
        case 2:
            quit()
        case _:
            print(clrm.Fore.RED)
            verificar = int(
                input("Opção inválida! | Escolha: "))
            print(clrm.Style.RESET_ALL)
    pass
except Exception:
    print(clrm.Fore.RED)
    verificar = int(input("Opção inválida! | Escolha: "))
    print(clrm.Style.RESET_ALL)

print(clrm.Style.RESET_ALL, clrm.Fore.RED, "\n3...", clrm.Fore.YELLOW)
t.sleep(1)
print("2...", clrm.Fore.GREEN)
t.sleep(1)
print("1...", clrm.Style.RESET_ALL)
t.sleep(1)
print(autologin(email, password))
