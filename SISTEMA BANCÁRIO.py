import textwrap
import json
from datetime import datetime
import os

# Constantes do sistema
ARQUIVO_DADOS = "dados_bancarios.json"
AGENCIA = "0001"
LIMITE_SAQUES = 3
LIMITE_VALOR_SAQUE = 500.00

def menu():
    menu = """\n
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [ec]\tEncerrar conta
    [nu]\tNovo usuário
    [q]\tSair
    => """
    return input(textwrap.dedent(menu)).strip().lower()

def carregar_dados():
    """Carrega os dados do arquivo JSON se existir"""
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, 'r') as f:
                return json.load(f)
        except:
            return {"usuarios": [], "contas": [], "saldo": 0, "extrato": "", "numero_saques": 0}
    return {"usuarios": [], "contas": [], "saldo": 0, "extrato": "", "numero_saques": 0}

def salvar_dados(dados):
    """Salva os dados no arquivo JSON"""
    with open(ARQUIVO_DADOS, 'w') as f:
        json.dump(dados, f, indent=2)

def formatar_valor(valor):
    """Formata valores monetários"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def validar_cpf(cpf):
    """Valida se o CPF tem 11 dígitos numéricos"""
    return cpf.isdigit() and len(cpf) == 11

def validar_valor_monetario(valor_str):
    """Valida se o valor é monetário válido"""
    try:
        valor = float(valor_str)
        return valor > 0, valor
    except ValueError:
        return False, 0

def obter_data_hora_atual():
    """Retorna a data e hora atual formatada"""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def depositar(saldo, valor, extrato, /):
    if valor > 0:
        saldo += valor
        data_hora = obter_data_hora_atual()
        extrato += f"{data_hora} - Depósito:\t{formatar_valor(valor)}\n"
        print("\n=== Depósito realizado com sucesso! ===")
    else:
        print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

    return saldo, extrato

def sacar(*, saldo, valor, extrato, limite, numero_saques, limite_saques):
    excedeu_saldo = valor > saldo
    excedeu_limite = valor > limite
    excedeu_saques = numero_saques >= limite_saques

    if excedeu_saldo:
        print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")
        return saldo, extrato, numero_saques

    elif excedeu_limite:
        print(f"\n@@@ Operação falhou! O valor do saque excede o limite de {formatar_valor(limite)}. @@@")
        return saldo, extrato, numero_saques

    elif excedeu_saques:
        print(f"\n@@@ Operação falhou! Número máximo de {limite_saques} saques excedido. @@@")
        return saldo, extrato, numero_saques

    elif valor > 0:
        saldo -= valor
        numero_saques += 1
        data_hora = obter_data_hora_atual()
        extrato += f"{data_hora} - Saque:\t\t{formatar_valor(valor)}\n"
        print("\n=== Saque realizado com sucesso! ===")
        print(f"Saques restantes hoje: {limite_saques - numero_saques}")

    else:
        print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

    return saldo, extrato, numero_saques

def exibir_extrato(saldo, /, *, extrato):
    print("\n================ EXTRATO ================")
    print("Não foram realizadas movimentações." if not extrato else extrato)
    print(f"\nSaldo:\t\t{formatar_valor(saldo)}")
    print("==========================================")

def criar_usuario(usuarios):
    cpf = input("Informe o CPF (somente número): ").strip()
    
    if not validar_cpf(cpf):
        print("\n@@@ CPF inválido! Deve conter 11 dígitos numéricos. @@@")
        return
    
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        print("\n@@@ Já existe usuário com esse CPF! @@@")
        return

    nome = input("Informe o nome completo: ").strip()
    if not nome:
        print("\n@@@ Nome não pode estar vazio! @@@")
        return

    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ").strip()
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ").strip()

    usuarios.append({
        "nome": nome, 
        "data_nascimento": data_nascimento, 
        "cpf": cpf, 
        "endereco": endereco
    })

    print("=== Usuário criado com sucesso! ===")

def filtrar_usuario(cpf, usuarios):
    usuarios_filtrados = [usuario for usuario in usuarios if usuario["cpf"] == cpf]
    return usuarios_filtrados[0] if usuarios_filtrados else None

def criar_conta(agencia, numero_conta, usuarios):
    cpf = input("Informe o CPF do usuário: ").strip()
    
    if not validar_cpf(cpf):
        print("\n@@@ CPF inválido! @@@")
        return None
    
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        print("\n=== Conta criada com sucesso! ===")
        # Formata o número da conta com 4 dígitos (0001, 0002, etc.)
        numero_conta_formatado = str(numero_conta).zfill(4)
        return {
            "agencia": agencia, 
            "numero_conta": numero_conta_formatado, 
            "usuario": usuario,
            "ativa": True
        }

    print("\n@@@ Usuário não encontrado, fluxo de criação de conta encerrado! @@@")
    return None

def listar_contas(contas):
    if not contas:
        print("\n@@@ Nenhuma conta cadastrada! @@@")
        return
        
    for conta in contas:
        if conta.get("ativa", True):  # Mostra apenas contas ativas
            linha = f"""\
                Agência:\t{conta['agencia']}
                C/C:\t\t{conta['numero_conta']}
                Titular:\t{conta['usuario']['nome']}
                Status:\t\t{'Ativa' if conta.get('ativa', True) else 'Encerrada'}
            """
            print("=" * 100)
            print(textwrap.dedent(linha))

def encerrar_conta(contas):
    if not contas:
        print("\n@@@ Nenhuma conta cadastrada! @@@")
        return contas
        
    numero_conta = input("Informe o número da conta a ser encerrada: ").strip().zfill(4)
    
    for conta in contas:
        if conta["numero_conta"] == numero_conta and conta.get("ativa", True):
            confirmacao = input(f"Tem certeza que deseja encerrar a conta {numero_conta}? (s/n): ").strip().lower()
            if confirmacao == 's':
                conta["ativa"] = False
                print("=== Conta encerrada com sucesso! ===")
            return contas
    
    print("\n@@@ Conta não encontrada ou já encerrada! @@@")
    return contas

def main():
    # Carrega dados existentes
    dados = carregar_dados()
    
    saldo = dados.get("saldo", 0)
    extrato = dados.get("extrato", "")
    numero_saques = dados.get("numero_saques", 0)
    usuarios = dados.get("usuarios", [])
    contas = dados.get("contas", [])
    
    # Encontra o próximo número de conta
    proximo_numero_conta = max([int(conta["numero_conta"]) for conta in contas] or [0]) + 1

    while True:
        opcao = menu()

        if opcao == "d":
            valor_str = input("Informe o valor do depósito: ").replace(",", ".")
            valido, valor = validar_valor_monetario(valor_str)
            
            if valido:
                saldo, extrato = depositar(saldo, valor, extrato)
            else:
                print("\n@@@ Valor inválido! Digite um valor numérico positivo. @@@")

        elif opcao == "s":
            valor_str = input("Informe o valor do saque: ").replace(",", ".")
            valido, valor = validar_valor_monetario(valor_str)
            
            if valido:
                saldo, extrato, numero_saques = sacar(
                    saldo=saldo,
                    valor=valor,
                    extrato=extrato,
                    limite=LIMITE_VALOR_SAQUE,
                    numero_saques=numero_saques,
                    limite_saques=LIMITE_SAQUES,
                )
            else:
                print("\n@@@ Valor inválido! Digite um valor numérico positivo. @@@")

        elif opcao == "e":
            exibir_extrato(saldo, extrato=extrato)

        elif opcao == "nu":
            criar_usuario(usuarios)

        elif opcao == "nc":
            conta = criar_conta(AGENCIA, proximo_numero_conta, usuarios)
            if conta:
                contas.append(conta)
                proximo_numero_conta += 1

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "ec":
            contas = encerrar_conta(contas)

        elif opcao == "q":
            # Salva dados antes de sair
            dados_salvar = {
                "usuarios": usuarios,
                "contas": contas,
                "saldo": saldo,
                "extrato": extrato,
                "numero_saques": numero_saques
            }
            salvar_dados(dados_salvar)
            print("\n=== Obrigado por usar nosso sistema! ===")
            break

        else:
            print("\n@@@ Operação inválida, por favor selecione novamente a operação desejada. @@@")

if __name__ == "__main__":
    main()
