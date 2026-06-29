from converter_file.detect import TARGET_FORMATS


def prompt_target_format(group: str) -> str:
    if group not in TARGET_FORMATS:
        raise ValueError(f"Grupo inválido: {group}")

    options = TARGET_FORMATS[group]

    while True:
        print(f"\nFormatos disponíveis para {group}:")
        for i, fmt in enumerate(options, start=1):
            print(f"  {i}. .{fmt}")

        choice = input("Escolha o número do formato de destino: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]

        print(f"Opção inválida. Digite um número entre 1 e {len(options)}.")
