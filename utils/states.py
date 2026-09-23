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

class LeatherImportStates(StatesGroup):
    choosing_color = State()
    entering_quantity = State()
    confirming = State()

class LeatherSaleStates(StatesGroup):
    choosing_color = State()
    entering_quantity = State()
    confirming = State()

class CashStates(StatesGroup):
    choosing_category = State()
    entering_withdrawal_amount = State()
    confirming_withdrawal = State()
