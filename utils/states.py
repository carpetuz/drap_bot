from aiogram.fsm.state import State, StatesGroup

class ImportStates(StatesGroup):
    choosing_width = State()
    choosing_color = State()
    entering_length = State()
    confirming = State()

class SaleStates(StatesGroup):
    choosing_width = State()
    choosing_color = State()
    choosing_roll = State()
    entering_sold_length = State()
    confirming = State()
    entering_customer_name = State()
    entering_customer_phone = State()
    entering_initial_paid = State()
    confirming_debt = State()

class LeatherImportStates(StatesGroup):
    choosing_color = State()
    entering_quantity = State()
    confirming = State()

class LeatherSaleStates(StatesGroup):
    choosing_color = State()
    entering_quantity = State()
    confirming = State()
    entering_customer_name = State()
    entering_customer_phone = State()
    entering_initial_paid = State()
    confirming_debt = State()

class CashStates(StatesGroup):
    choosing_category = State()
    entering_withdrawal_amount = State()
    confirming_withdrawal = State()

class DebtPaymentStates(StatesGroup):
    choosing_debt = State()
    entering_payment_amount = State()
    confirming_payment = State()

class KavralanImportStates(StatesGroup):
    entering_length = State()
    confirming = State()

class KavralanSaleStates(StatesGroup):
    choosing_roll = State()
    entering_sold_length = State()
    confirming = State()
    entering_customer_name = State()
    entering_customer_phone = State()
    entering_initial_paid = State()
    confirming_debt = State()

class Branch3SaleStates(StatesGroup):
    choosing_collection = State()
    entering_length = State()
    confirming = State()


