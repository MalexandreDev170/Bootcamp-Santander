
nome = input("Qual é o seu nome? ")


idade = int(input("Qual é a sua idade? "))


carteira = input("Você tem carteira de motorista? (s ou n) ").lower()

if idade >= 18 and carteira == 's':
    print("Pode dirigir!")
else:
    print("Não pode dirigir ainda!")

input("aperte enter para sair")
