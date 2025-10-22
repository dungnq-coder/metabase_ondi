def input_int(prompt: str, allow_empty=False, allow_cancel=True) -> int | None:
    while True:
        value = input(prompt).strip()
        if allow_cancel and value.lower() == 'q':
            return None
        if allow_empty and value == '':
            return None
        if value.isdigit():
            return int(value)
        print("❗ Please enter a valid number or 'q' to cancel.")


def input_str(prompt: str, required=True, allow_cancel=True) -> str | None:
    while True:
        value = input(prompt).strip()
        if allow_cancel and value.lower() == 'q':
            return None
        if not value and required:
            print('❗ This field is required.')
            continue
        return value or None


def input_yes_no(prompt: str, default=None) -> bool | None:
    while True:
        value = input(f'{prompt} (y/n): ').strip().lower()
        if value == '' and default is not None:
            return default
        if value in ['y', 'yes']:
            return True
        if value in ['n', 'no']:
            return False
        if value == 'q':
            return None
        print("❗ Please enter 'y' or 'n' (or press q to cancel).")
