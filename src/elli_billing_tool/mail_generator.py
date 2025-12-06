"""Email generation for sending reimbursement forms."""

from pathlib import Path


def load_mail_template(template_path: Path, placeholders: dict[str, str]) -> str:
    """
    Load email template and replace placeholders.

    Args:
        template_path: Path to the template file
        placeholders: Dictionary of placeholder -> value mappings

    Returns:
        Email body with replaced placeholders
    """
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    for placeholder, value in placeholders.items():
        content = content.replace(f"{{{placeholder}}}", value)

    return content
