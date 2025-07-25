print("Olá mundo, meu nome é Marcos Alexandre e estou aprendendo Python")

nome = "Marcos"

print(nome)
print(2 + 3)  
print(5 - 1)  
print(4 * 2)  
print(8 / 2)   
nome = "Marcos"
idade = 25
print(nome)
print(idade)
nome = input("Qual seu nome? ")
print("Olá,", nome)

idade = int(input("Qual sua idade? "))

if idade >= 18:
    print("Você é maior de idade!")
else:
    print("Você é menor de idade.")

    nome = input("Digite seu nome: ")
idade = int(input("Digite sua idade: "))
print("Olá,", nome)

if idade >= 18:
    print("Pode entrar na festa!")
else:
    print("Vai jogar Minecraft em casa!")

print(10 // 3)  
print(10 % 3)   

nota = float(input("Digite sua nota: "))

if nota >= 7:
    print("Aprovado!")
elif nota >= 5:
    print("Recuperação.")
else:
    print("Reprovado.")

nome = input("Qual seu nome? ")
idade = int(input("Quantos anos você tem? "))

if idade < 12:
    print("Oi, criança", nome)
elif idade < 18:
    print("E aí, jovem", nome)
elif idade < 60:
    print("Olá, adulto", nome)
else:
    print("Saudações, senhor(a)", nome)





