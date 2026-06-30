import sys
from typing import TypeVar

from converter_file.detect import TARGET_FORMATS
from converter_file.estimate import estimate_output_size_labels

CANCEL_VALUE = "__cancel__"
T = TypeVar("T")


class ConversionCancelled(Exception):
    pass


def prompt_target_format(group: str, input_paths: list[str] | None = None) -> str:
    if group not in TARGET_FORMATS:
        raise ValueError(f"Grupo inválido: {group}")

    options = TARGET_FORMATS[group]
    estimates = estimate_output_size_labels(input_paths or [], options, group)

    if _supports_arrow_menu():
        return _prompt_interactive(group, options, estimates)

    return _prompt_with_numbers(group, options, estimates)


def prompt_yes_no(message: str) -> bool:
    return prompt_choice(message, [("Sim", True), ("Não", False)])


def prompt_text(message: str) -> str:
    if _supports_arrow_menu():
        try:
            return _prompt_text_with_questionary(message)
        except ImportError:
            pass

    return input(f"{message} ").strip()


def prompt_choice(message: str, choices: list[tuple[str, T]]) -> T:
    if not choices:
        raise ValueError("Choices cannot be empty")

    if _supports_arrow_menu():
        return _prompt_choice_interactive(message, choices)

    return _prompt_choice_with_numbers(message, choices)


def _supports_arrow_menu() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_choice_with_numbers(message: str, choices: list[tuple[str, T]]) -> T:
    while True:
        print(f"\n{message}")
        for i, (label, _) in enumerate(choices, start=1):
            print(f"  {i}. {label}")

        choice = input("Escolha uma opção: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(choices):
            return choices[int(choice) - 1][1]

        print(f"Opção inválida. Digite um número entre 1 e {len(choices)}.")


def _prompt_text_with_questionary(message: str) -> str:
    import questionary

    result = questionary.text(message, style=_questionary_style()).ask()
    if result is None:
        raise ConversionCancelled
    return result.strip()


def _prompt_choice_interactive(message: str, choices: list[tuple[str, T]]) -> T:
    try:
        return _prompt_choice_with_questionary(message, choices)
    except ImportError:
        return _prompt_choice_with_arrows(message, choices)


def _prompt_choice_with_questionary(message: str, choices: list[tuple[str, T]]) -> T:
    import questionary
    from questionary import Choice

    result = questionary.select(
        message,
        choices=[Choice(title=label, value=value) for label, value in choices],
        instruction="Use as setas e Enter",
        style=_questionary_style(),
    ).ask()

    if result is None:
        raise ConversionCancelled

    return result


def _prompt_choice_with_arrows(message: str, choices: list[tuple[str, T]]) -> T:
    selected = 0

    while True:
        _render_choice_menu(message, choices, selected)
        key = _read_key()

        if key == "up":
            selected = (selected - 1) % len(choices)
        elif key == "down":
            selected = (selected + 1) % len(choices)
        elif key == "enter":
            print()
            return choices[selected][1]
        elif key == "\x03":
            raise ConversionCancelled
        elif key.isdigit() and 1 <= int(key) <= len(choices):
            print()
            return choices[int(key) - 1][1]


def _render_choice_menu(message: str, choices: list[tuple[str, T]], selected: int) -> None:
    print("\033[2J\033[H", end="")
    print(message)
    print("Use ↑/↓ e Enter para selecionar.\n")

    for i, (label, _) in enumerate(choices):
        marker = ">" if i == selected else " "
        print(f"{marker} {i + 1}. {label}")


def _prompt_with_numbers(group: str, options: list[str], estimates: dict[str, str]) -> str:
    while True:
        print(f"\nFormatos disponíveis para {group}:")
        for i, fmt in enumerate(options, start=1):
            print(f"  {i}. {_format_option_label(fmt, estimates)}")
        print("  0. Cancelar")

        choice = input("Escolha o número do formato de destino ou 0 para cancelar: ").strip()

        if choice == "0":
            raise ConversionCancelled

        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]

        print(f"Opção inválida. Digite um número entre 0 e {len(options)}.")


def _prompt_interactive(group: str, options: list[str], estimates: dict[str, str]) -> str:
    try:
        return _prompt_with_questionary(group, options, estimates)
    except ImportError:
        return _prompt_with_arrows(group, options, estimates)


def _prompt_with_questionary(group: str, options: list[str], estimates: dict[str, str]) -> str:
    import questionary
    from questionary import Choice

    result = questionary.select(
        f"Formato de destino para {group}:",
        choices=[Choice(title=_format_option_label(fmt, estimates), value=fmt) for fmt in options]
        + [Choice(title="Cancelar", value=CANCEL_VALUE)],
        instruction="Use as setas e Enter",
        style=_questionary_style(),
    ).ask()

    if result in (None, CANCEL_VALUE):
        raise ConversionCancelled

    return result


def _prompt_with_arrows(group: str, options: list[str], estimates: dict[str, str]) -> str:
    selected = 0
    choices = options + [CANCEL_VALUE]

    while True:
        _render_arrow_menu(group, choices, selected, estimates)
        key = _read_key()

        if key == "up":
            selected = (selected - 1) % len(choices)
        elif key == "down":
            selected = (selected + 1) % len(choices)
        elif key == "enter":
            print()
            if choices[selected] == CANCEL_VALUE:
                raise ConversionCancelled
            return choices[selected]
        elif key == "\x03":
            raise ConversionCancelled
        elif key.isdigit() and 1 <= int(key) <= len(options):
            print()
            return options[int(key) - 1]
        elif key == "0":
            print()
            raise ConversionCancelled


def _render_arrow_menu(
    group: str,
    choices: list[str],
    selected: int,
    estimates: dict[str, str],
) -> None:
    print("\033[2J\033[H", end="")
    print(f"Formatos disponíveis para {group}:")
    print("Use ↑/↓ e Enter para selecionar.\n")

    for i, fmt in enumerate(choices):
        marker = ">" if i == selected else " "
        if fmt == CANCEL_VALUE:
            print(f"{marker} 0. Cancelar")
            continue
        print(f"{marker} {i + 1}. {_format_option_label(fmt, estimates)}")


def _format_option_label(fmt: str, estimates: dict[str, str]) -> str:
    label = f".{fmt}"
    estimate = estimates.get(fmt)
    if estimate is None:
        return label
    return f"{label} ({estimate} estimado)"


def _questionary_style():
    from questionary import Style

    return Style(
        [
            ("qmark", "fg:#7c3aed bold"),
            ("question", "bold"),
            ("answer", "fg:#22c55e bold"),
            ("pointer", "fg:#7c3aed bold"),
            ("highlighted", "fg:#7c3aed bold"),
            ("selected", "fg:#22c55e"),
        ]
    )


def _read_key() -> str:
    if sys.platform == "win32":
        return _read_windows_key()
    return _read_posix_key()


def _read_windows_key() -> str:
    import msvcrt

    key = msvcrt.getwch()
    if key in ("\r", "\n"):
        return "enter"
    if key in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        if code == "H":
            return "up"
        if code == "P":
            return "down"
    return key


def _read_posix_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key in ("\r", "\n"):
            return "enter"
        if key == "\x1b":
            sequence = sys.stdin.read(2)
            if sequence == "[A":
                return "up"
            if sequence == "[B":
                return "down"
        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
