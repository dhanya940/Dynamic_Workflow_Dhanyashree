# app/services/validation_service.py

import re
from typing import Any
from datetime import date


EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compare_value(value, operator, comparison_value):

    if operator == "equals":
        if isinstance(value, list):
            return comparison_value in [str(x) for x in value]

        return str(value) == str(comparison_value)

    if operator == "not_equals":
        if isinstance(value, list):
            return comparison_value not in [str(x) for x in value]

        return str(value) != str(comparison_value)

    if operator == "contains":
        if isinstance(value, list):
            return comparison_value in [str(x) for x in value]

        return str(comparison_value).lower() in str(value).lower()

    if operator == "greater_than":
        value_number = to_number(value)
        comparison_number = to_number(comparison_value)

        if value_number is None or comparison_number is None:
            return False

        return value_number > comparison_number

    if operator == "is_empty":
        return is_empty(value)

    return False


def validate_field(field, value):

    if is_empty(value):
        return None

    field_type = field.field_type.lower()
    config = field.validation_config or {}

    # TEXT
    if field_type in ["text", "textarea"]:

        if not isinstance(value, str):
            return f"{field.label} must be text"

        min_length = config.get("min_length")
        max_length = config.get("max_length")

        if min_length is not None:
            if len(value) < int(min_length):
                return (
                    f"{field.label} must contain at least "
                    f"{min_length} characters"
                )

        if max_length is not None:
            if len(value) > int(max_length):
                return (
                    f"{field.label} must contain at most "
                    f"{max_length} characters"
                )

    # EMAIL
    elif field_type == "email":

        if not re.match(EMAIL_REGEX, str(value)):
            return f"Invalid email format for {field.label}"

    # NUMBER
    elif field_type == "number":

        number = to_number(value)

        if number is None:
            return f"{field.label} must be a number"

        minimum = config.get("min")
        maximum = config.get("max")

        if minimum is not None and number < float(minimum):
            return f"{field.label} must be at least {minimum}"

        if maximum is not None and number > float(maximum):
            return f"{field.label} must be at most {maximum}"

    # DATE
    elif field_type == "date":

        try:
            parsed_date = date.fromisoformat(str(value))
        except ValueError:
            return f"{field.label} must be a valid date"

        minimum = config.get("min_date")
        maximum = config.get("max_date")

        if minimum:
            if parsed_date < date.fromisoformat(minimum):
                return f"{field.label} must be on or after {minimum}"

        if maximum:
            if parsed_date > date.fromisoformat(maximum):
                return f"{field.label} must be on or before {maximum}"

    # DROPDOWN
    elif field_type == "dropdown":

        allowed_values = {
            str(option.option_value)
            for option in field.options
        }

        if str(value) not in allowed_values:
            return f"Invalid option for {field.label}"

    # CHECKBOX
    elif field_type == "checkbox":

        if not isinstance(value, list):
            return f"{field.label} must contain selected options"

        allowed_values = {
            str(option.option_value)
            for option in field.options
        }

        for selected in value:

            if str(selected) not in allowed_values:
                return f"Invalid option selected for {field.label}"

        minimum = config.get("min_selections")

        if minimum is not None:
            if len(value) < int(minimum):
                return (
                    f"{field.label} requires at least "
                    f"{minimum} selections"
                )

        maximum = config.get("max_selections")

        if maximum is not None:
            if len(value) > int(maximum):
                return (
                    f"{field.label} allows at most "
                    f"{maximum} selections"
                )

    # RATING
    elif field_type == "rating":

        number = to_number(value)

        if number is None:
            return f"{field.label} must be a rating"

        minimum = config.get("min", 1)
        maximum = config.get("max", 5)

        if number < minimum or number > maximum:
            return (
                f"{field.label} must be between "
                f"{minimum} and {maximum}"
            )

    # FILE
    elif field_type == "file":

        # File validation is handled during upload
        # Here we just check if a file ID was provided (UUID format)
        if value and not is_empty(value):
            # Check if it looks like a UUID (file ID)
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(uuid_pattern, str(value), re.IGNORECASE):
                return f"{field.label} must be a valid file reference"

    return None


def evaluate_rules(fields, rules, submitted_values):

    field_ids = {str(field.id) for field in fields}

    visible = {
        str(field.id): True
        for field in fields
    }

    required = {
        str(field.id): bool(field.is_required)
        for field in fields
    }

    for rule in rules:

        trigger_id = str(rule.trigger_field_id)
        target_id = str(rule.target_field_id)

        if trigger_id not in field_ids:
            continue

        if target_id not in field_ids:
            continue

        trigger_value = submitted_values.get(trigger_id)

        condition = compare_value(
            trigger_value,
            rule.operator,
            rule.comparison_value
        )

        if rule.action == "show":

            if not condition:
                visible[target_id] = False

        elif rule.action == "hide":

            if condition:
                visible[target_id] = False

        elif rule.action == "require":

            if condition:
                required[target_id] = True

    return visible, required


def validate_submission(fields, rules, submitted_values):

    errors = {}

    visible, required = evaluate_rules(
        fields,
        rules,
        submitted_values
    )

    field_map = {
        str(field.id): field
        for field in fields
    }

    # Reject unknown fields
    for field_id in submitted_values:

        if field_id not in field_map:
            errors[field_id] = "Unknown field"

    # Validate every field
    for field_id, field in field_map.items():

        value = submitted_values.get(field_id)

        # Hidden field must not contain data
        if not visible[field_id]:

            if not is_empty(value):

                errors[field_id] = (
                    f"{field.label} must be empty "
                    f"because this field is hidden"
                )

            continue

        # Required field
        if required[field_id]:

            if is_empty(value):

                errors[field_id] = (
                    f"{field.label} is required"
                )

                continue

        # Normal validation
        if not is_empty(value):

            error = validate_field(
                field,
                value
            )

            if error:
                errors[field_id] = error

    return errors