def to_safe_filename(filename):
    def safe_char(c):
        return c if c.isalnum() or c == '-' else '-'

    return "".join(safe_char(c) for c in filename).strip("-")
