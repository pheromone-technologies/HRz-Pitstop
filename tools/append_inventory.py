import json
import openpyxl

def get_category(name):
    n = str(name).lower()
    if any(x in n for x in ['helmet', 'visor', 'pinlock', 'goggle', 'lens', 'intercom']):
        return 'Helmets & Accessories'
    if any(x in n for x in ['jacket', 'pant', 'glove', 'suit', 'shoe', 'boot', 'jersey', 'knee guard', 'elbow guard', 'rain']):
        return 'Riding Gears'
    if any(x in n for x in ['bag', 'luggage', 'topcase', 'saddle', 'pannier', 'carrier', 'tail bag', 'tank bag']):
        return 'Luggage & Touring'
    if any(x in n for x in ['light', 'fog', 'indicator', 'led', 'bulb', 'flasher', 'hazard', 'headlight', 'switch']):
        return 'Lighting'
    if any(x in n for x in ['crashguard', 'slider', 'crash guard', 'bash plate', 'sump guard', 'radiator guard', 'leg guard', 'grill']):
        return 'Bike Protection'
    if any(x in n for x in ['handle', 'grip', 'lever', 'mirror', 'bar end', 'riser', 'knuckle', 'handlebar']):
        return 'Handlebar & Accessories'
    if any(x in n for x in ['foot', 'peg', 'rest']):
        return 'Foot Rests'
    if any(x in n for x in ['mount', 'bracket', 'holder', 'stay', 'gps']):
        return 'Guards & Mounts'
    if any(x in n for x in ['cap', 'stand', 'paddock', 'oil', 'spool']):
        return 'Oil Caps & Stands'
    if any(x in n for x in ['fairing', 'fender', 'mudguard', 'winglet', 'cowl', 'windscreen', 'windshield', 'tail tidy']):
        return 'Body Fairing and Fenders'
    if any(x in n for x in ['cleaner', 'brush', 'lube', 'polish', 'cloth', 'micro fiber', 'wash', 'chain lube']):
        return 'Cleaning Accessories'
    if any(x in n for x in ['filter', 'exhaust', 'spark plug', 'chain sprocket', 'sprocket', 'chain kit']):
        return 'Performance Accessories'
    if any(x in n for x in ['cover', 'horn', 'cable', 'relay', 'charger']):
        return 'Bike Essentials'
    return 'General Accessories'

# Load the Excel file
file_path = 'HRZ_Pitstop_Client_Inventory_All_Bike_Models.xlsx'
wb = openpyxl.load_workbook(file_path)

# Load matched items
with open('matched_768_items.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Append items to corresponding sheets
counts = {sheet: 0 for sheet in wb.sheetnames}

for item in items:
    row_data = item['excel_row']
    name = row_data.get('Item Name', '')
    if not name: continue
    
    category = get_category(name)
    if category not in wb.sheetnames:
        category = 'General Accessories'
        
    sheet = wb[category]
    
    # Columns in the target excel (1-indexed for openpyxl):
    # 1: Part / Product Name
    # 2: Subcategory
    # 3: Brand
    # 4: Compatible Bike Make
    # 5: Compatible Bike Model
    # 6: MRP (₹)
    # 7: Selling Price (₹)
    # 8: Discount %
    # 9: Stock Quantity
    # 10: Product Image Filename / URL
    # 11: Short Description
    
    # We append to the next available row in the sheet.
    # Find the max row with data in column 1 (Product Name)
    max_row = 1
    for r in range(1, sheet.max_row + 2):
        if sheet.cell(row=r, column=1).value is None:
            max_row = r
            break
            
    mrp = row_data.get('Purchase Price', 0)
    sp = row_data.get('Sale Price', 0)
    stock = row_data.get('Available Quantity for Sale', 0)
    
    sheet.cell(row=max_row, column=1, value=name)
    sheet.cell(row=max_row, column=6, value=mrp)
    sheet.cell(row=max_row, column=7, value=sp)
    sheet.cell(row=max_row, column=9, value=stock)
    
    counts[category] += 1

wb.save(file_path)
print("Updated Excel file. Category breakdown:")
for k, v in counts.items():
    if v > 0:
        print(f"{k}: {v} items added.")
