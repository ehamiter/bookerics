import logging

# ANSI escape sequences for colors
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

class CustomFormatter(logging.Formatter):
    def format(self, record):
        level_name = record.levelname
        if level_name == "INFO":
            level_name_color = f"{GREEN}{level_name}{RESET}"
        elif level_name == "WARNING":
            level_name_color = f"{YELLOW}{level_name}{RESET}"
        elif level_name == "ERROR":
            level_name_color = f"{RED}{level_name}{RESET}"
        else:
            level_name_color = level_name

        # Calculate the number of spaces needed for alignment
        num_spaces = 9 - len(record.levelname)
        spaces = " " * num_spaces

        # Update the levelname to include color and spacing
        record.levelname = f"{level_name_color}:{spaces}"

        return super().format(record)

# Create a logger
logger = logging.getLogger("customLogger")
logger.setLevel(logging.INFO)

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter with dynamic spacing
formatter = CustomFormatter('%(levelname)s%(message)s')

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
logger.addHandler(ch)

# Test logging
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
