'''
produto_1 = int(10)
produto_2 = int(100)

print(produto_1 + produto_2)
print(produto_1 - produto_2)
print(produto_1 / produto_2)
print(produto_1 // produto_2)
print(produto_1 * produto_2)
print(produto_1 % produto_2)
print(produto_1 ** produto_2)
'''
'''
to com fome
'''
'''

saldo = 500
saldo = saldo + 200
print (saldo)
'''


'''
def sacar(valor):
    saldo = 500

    if saldo >= valor:
        print("valor sacado")
    else: 
        print("saldo insuficiente")

sacar(150)
sacar(600)
'''
opcao = 1
while opcao != 0:

    acerto = int(input("Digite o acerto: "))
    classe_de_armadura = int(input("Digite a classe de armadura: "))

    status = "conseguiu" if acerto >= classe_de_armadura else "não conseguiu"
    print(f"o jogador {status} acertar o inimigo")

    opcao = int(input("[1] Continuar testando ou [0] Parar o teste: "))


'''

texto = input("Informe um texto: ")
VOGAIS = "AEIOU"

for letra in texto:
    if letra.upper() in VOGAIS:
        print(letra, end="")
        '''
