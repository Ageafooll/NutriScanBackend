# ====== Core Connection and Initialization ======
from .core import (
    get_connection,
    init_db,
    crypt_context,
)

# ====== Core Exception Classes ======
from .core import (
    DatabaseError,
    DatabaseConnectionError,
    DatabaseAlreadyExistsError,
    DatabaseNotFoundError,
)

# ====== User Management ======
from .users import (
    # Account Management
    register_account,
    authenticate_account,
    delete_account,
    upgrade_to_premium,
    downgrade_from_premium,
    # Profile Management
    get_user_profile,
    update_user_profile,
    # Restrictions Management
    get_user_restrictions,
    add_user_restriction,
    delete_user_restriction,
)

# ====== Logging Functions ======
from .logs import (
    # Food Logging
    get_food_logs,
    add_food_log,
    delete_food_log,
    # Water Logging
    get_water_logs,
    add_water_log,
    delete_water_log,
    # Weight Logging
    get_weight_logs,
    add_weight_log,
    delete_weight_log,
)

# ====== Diet Management ======
from .diet import (
    # Diet Program Management
    get_user_diet_programs,
    create_diet_program,
    delete_diet_program,
    # Diet Meals Management
    get_diet_meals,
    add_diet_meal,
    delete_diet_meal,
)

__all__ = [
    # Core
    "get_connection",
    "init_db",
    "crypt_context",
    # Exceptions
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseAlreadyExistsError",
    "DatabaseNotFoundError",
    # Users
    "register_account",
    "authenticate_account",
    "delete_account",
    "upgrade_to_premium",
    "downgrade_from_premium",
    "get_user_profile",
    "update_user_profile",
    "get_user_restrictions",
    "add_user_restriction",
    "delete_user_restriction",
    # Logs
    "get_food_logs",
    "add_food_log",
    "delete_food_log",
    "get_water_logs",
    "add_water_log",
    "delete_water_log",
    "get_weight_logs",
    "add_weight_log",
    "delete_weight_log",
    # Diet
    "get_user_diet_programs",
    "create_diet_program",
    "delete_diet_program",
    "get_diet_meals",
    "add_diet_meal",
    "delete_diet_meal",
]
