import xlsxwriter

# Data
bikes = {
    "ROYAL ENFIELD": ["Scram 440 new", "Classic 650", "Bear 650", "Guerrilla 450", "Himalayan 450", "SUPER METEOR 650", "Hunter 350", "Himalayan", "Classic 350 Reborn", "Standard 350 Reborn", "Meteor 350", "Classic", "Standard", "Electra", "Interceptor", "Thunderbird", "Thunderbird X", "Continental GT", "Scram"],
    "YAMAHA": ["XSR 155", "RX 100", "Aerox 155", "MT 15", "R3", "R15 V1", "R15 V2", "R15 V3", "R15 V4", "R1"],
    "KTM": ["KTM 390 Enduro R", "Adventure 890", "ADVENTURE 390 2025 Model", "Adventure 390", "Duke 125", "Duke 200", "Duke 250 BS6", "Duke 250", "Duke 390", "RC 390"],
    "BAJAJ": ["NS400Z", "Pulsar 220", "Pulsar NS 200", "Pulsar RS 200", "Dominar 400", "Pulsar 150", "Pulsar 180"],
    "HONDA": ["XL750 Transalp", "NX500", "CB 200X", "Hness CB 350", "Hornet 160R", "CBR 250 R", "CB 300", "CB 350 RS", "CB 500X", "NX400", "CB650R", "CBR 650R", "CBR 1000RR"],
    "SUZUKI": ["Gixxer", "Gixxer SF", "V Strom 250", "Hayabusa", "GSX-S750", "V Strom 800DE", "V Strom DL650"],
    "HERO": ["Xpulse 210", "Mavrick 440", "Xpulse 200", "Impulse"],
    "TRIUMPH": ["Tiger 900", "Tracker 400", "Scrambler 400 x", "Speed 400", "Tiger Sport 660", "Tiger", "Trident 660"],
    "TVS": ["Apache RTX 300 new", "tvs ronin", "Apache 200", "Apache RTR 160", "Apache RTR 310"],
    "HARLEY DAVIDSON": ["Harley 440X"],
    "OLA": ["Ola"],
    "BMW": ["G 310GS", "G 310 R", "S 1000R", "R 1200GS", "R 1300GS"],
    "KAWASAKI": ["Versys 650", "Ninja 300", "Z900", "Ninja 400", "Ninja ZX-10R", "Ninja ZX6R"],
    "BENELLI": ["Benelli 600", "TRK 502"],
    "DUCATI": ["Panigale V4"],
    "APRILA": ["RS660"]
}

# Create a new Excel file
workbook = xlsxwriter.Workbook('HRz_Data_Collection.xlsx')
worksheet = workbook.add_worksheet('Products')
hidden_sheet = workbook.add_worksheet('Data_Hidden')
hidden_sheet.hide()

# Format
header_format = workbook.add_format({
    'bold': True,
    'text_wrap': True,
    'valign': 'top',
    'bg_color': '#333333',
    'font_color': '#FFFFFF',
    'border': 1
})

columns = [
    "SKU",
    "Part / Product Name",
    "Subcategory",
    "Brand",
    "Compatible Bike Make",
    "Compatible Bike Model",
    "MRP (₹)",
    "Selling Price (₹)",
    "Discount %",
    "Stock Quantity",
    "Product Image Filename / URL",
    "Short Description"
]

for col_num, col_name in enumerate(columns):
    worksheet.write(0, col_num, col_name, header_format)

worksheet.set_column('A:A', 15)  # SKU
worksheet.set_column('B:B', 30)  # Product Name
worksheet.set_column('C:D', 20)  # Subcategory, Brand
worksheet.set_column('E:F', 25)  # Bike Make, Bike Model
worksheet.set_column('G:J', 12)  # Prices, Stock
worksheet.set_column('K:K', 40)  # Image URL
worksheet.set_column('L:L', 40)  # Description

# Write Data to Hidden Sheet
brands = list(bikes.keys())
hidden_sheet.write_column('A1', brands)
workbook.define_name('BrandList', '=Data_Hidden!$A$1:$A$' + str(len(brands)))

col_idx = 1 # B
for brand, models in bikes.items():
    # Write brand models to hidden sheet
    safe_brand_name = brand.replace(" ", "_").replace("-", "_")
    hidden_sheet.write_column(0, col_idx, models)
    
    # Define named range for each brand's models
    col_letter = xlsxwriter.utility.xl_col_to_name(col_idx)
    range_str = f'=Data_Hidden!${col_letter}$1:${col_letter}${len(models)}'
    workbook.define_name(safe_brand_name, range_str)
    
    col_idx += 1

# Add Data Validation

# Dropdown for Bike Make (Column E)
worksheet.data_validation('E2:E1000', {'validate': 'list', 'source': '=BrandList'})

# Dependent Dropdown for Bike Model (Column F)
for row in range(2, 1001):
    cell = f'F{row}'
    make_cell = f'E{row}'
    # Excel formula to substitute spaces with underscores
    formula = f'=INDIRECT(SUBSTITUTE({make_cell}, " ", "_"))'
    worksheet.data_validation(cell, {'validate': 'list', 'source': formula})

workbook.close()
print("HRz_Data_Collection.xlsx regenerated successfully with EXACT columns from Google Sheet!")
